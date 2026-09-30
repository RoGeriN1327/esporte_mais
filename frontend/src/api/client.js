// Cliente HTTP único da aplicação (axios) e gestão dos tokens de sessão.
//
// - O access token (JWT, 30 min) fica só em memória e vai no header Authorization.
// - O refresh token (7 dias) fica no localStorage para manter o login ao recarregar.
// - Se uma requisição voltar 401, o interceptor renova os tokens uma única vez e
//   repete a requisição; se a renovação falhar, a sessão local é encerrada.
import axios from 'axios'

export const CHAVE_REFRESH = 'esporte_refresh_token'
export const CHAVE_USUARIO = 'esporte_usuario'

// VITE_API_URL é embutida no bundle durante o build (não é lida em tempo de execução).
// Só em desenvolvimento existe o valor padrão; o build de produção falha sem ela
// (ver vite.config.js).
const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/+$/, '')

const api = axios.create({ baseURL: API_URL })

let accessToken = null
export function definirAccessToken(token) {
  accessToken = token
}

// Callback do AuthContext para voltar à tela de login quando a sessão expira.
let aoExpirarSessao = null
export function registrarSessaoExpirada(callback) {
  aoExpirarSessao = callback
}

api.interceptors.request.use((config) => {
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`
  return config
})

// Várias requisições podem receber 401 ao mesmo tempo: todas aguardam a mesma renovação.
let renovacaoEmCurso = null
api.interceptors.response.use(
  (resposta) => resposta,
  async (erro) => {
    const original = erro.config
    const ehRotaDeAuth = original?.url?.startsWith('/auth/')
    if (erro.response?.status === 401 && original && !original._retentada && !ehRotaDeAuth) {
      const refresh = localStorage.getItem(CHAVE_REFRESH)
      if (refresh) {
        original._retentada = true
        try {
          renovacaoEmCurso =
            renovacaoEmCurso ||
            axios.post(`${api.defaults.baseURL}/auth/refresh`, { refresh_token: refresh })
          const { data } = await renovacaoEmCurso
          renovacaoEmCurso = null
          localStorage.setItem(CHAVE_REFRESH, data.refresh_token)
          localStorage.setItem(CHAVE_USUARIO, JSON.stringify(data.usuario))
          definirAccessToken(data.access_token)
          original.headers.Authorization = `Bearer ${data.access_token}`
          return api(original)
        } catch {
          renovacaoEmCurso = null
          localStorage.removeItem(CHAVE_REFRESH)
          localStorage.removeItem(CHAVE_USUARIO)
          definirAccessToken(null)
          if (aoExpirarSessao) aoExpirarSessao()
        }
      }
    }
    return Promise.reject(erro)
  },
)

// Converte o erro da API em uma frase para exibir ao usuário.
// "detail" é texto nos erros de negócio e uma lista nos erros de validação (422).
export function mensagemDeErro(erro) {
  const detail = erro?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length > 0) {
    const msg = detail[0]?.msg || ''
    return msg.replace(/^Value error,\s*/, '') || 'Dados inválidos. Verifique os campos.'
  }
  return 'Não foi possível completar a operação. Tente novamente.'
}

export default api
