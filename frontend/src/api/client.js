import axios from 'axios'

export const CHAVE_REFRESH = 'esporte_refresh_token'
export const CHAVE_USUARIO = 'esporte_usuario'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
})

let accessToken = null
export function definirAccessToken(token) {
  accessToken = token
}

let aoExpirarSessao = null
export function registrarSessaoExpirada(callback) {
  aoExpirarSessao = callback
}

api.interceptors.request.use((config) => {
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`
  return config
})

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
