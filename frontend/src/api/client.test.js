// Unitários — cliente HTTP (src/api/client.js).
// Verifica a renovação automática de sessão: ao receber 401, o cliente troca o
// refresh token por um novo par, repete a requisição original e, se a renovação
// falhar, encerra a sessão local. O servidor é simulado por um adapter do axios.
import axios, { AxiosError } from 'axios'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import api, {
  CHAVE_REFRESH,
  CHAVE_USUARIO,
  definirAccessToken,
  mensagemDeErro,
  registrarSessaoExpirada,
} from './client'

const NOVA_SESSAO = {
  access_token: 'access-novo',
  refresh_token: 'refresh-novo',
  usuario: { id: 7, nome: 'Ana', tipo: 'Pessoa' },
}

function responder(config, status, data = {}) {
  const resposta = { data, status, statusText: String(status), headers: {}, config }
  if (status >= 400) {
    return Promise.reject(
      new AxiosError(`HTTP ${status}`, 'ERR_BAD_REQUEST', config, null, resposta),
    )
  }
  return Promise.resolve(resposta)
}

/** Servidor falso: responde 401 enquanto o token enviado não for o renovado. */
function servidorQueExigeTokenNovo(requisicoes) {
  return (config) => {
    requisicoes.push({ url: config.url, authorization: config.headers.Authorization })
    return config.headers.Authorization === 'Bearer access-novo'
      ? responder(config, 200, { ok: true })
      : responder(config, 401, { detail: 'Sessão expirada. Faça login novamente.' })
  }
}

describe('interceptors de autenticação', () => {
  let requisicoes
  let refresh
  let sessaoExpirada

  beforeEach(() => {
    localStorage.clear()
    requisicoes = []
    definirAccessToken('access-antigo')
    sessaoExpirada = vi.fn()
    registrarSessaoExpirada(sessaoExpirada)
    refresh = vi.spyOn(axios, 'post').mockResolvedValue({ data: NOVA_SESSAO })
    api.defaults.adapter = servidorQueExigeTokenNovo(requisicoes)
  })

  afterEach(() => {
    vi.restoreAllMocks()
    definirAccessToken(null)
  })


  it('envia o access token no cabeçalho Authorization somente quando há sessão', async () => {
    definirAccessToken('access-novo')
    await api.get('/usuarios/me')
    expect(requisicoes[0].authorization).toBe('Bearer access-novo')

    definirAccessToken(null)
    api.defaults.adapter = (config) => {
      requisicoes.push(config.headers.Authorization)
      return responder(config, 200)
    }
    await api.get('/quadras')
    expect(requisicoes[1]).toBeUndefined()
  })

  it('ao receber 401, renova a sessão e repete a requisição com o novo token', async () => {
    localStorage.setItem(CHAVE_REFRESH, 'refresh-antigo')

    const resposta = await api.get('/agendamentos/me')

    expect(resposta.data).toEqual({ ok: true })
    expect(refresh).toHaveBeenCalledTimes(1)
    expect(refresh).toHaveBeenCalledWith('http://localhost:8000/auth/refresh', {
      refresh_token: 'refresh-antigo',
    })
    expect(requisicoes.map((r) => r.authorization)).toEqual([
      'Bearer access-antigo',
      'Bearer access-novo',
    ])
    expect(localStorage.getItem(CHAVE_REFRESH)).toBe('refresh-novo')
    expect(JSON.parse(localStorage.getItem(CHAVE_USUARIO))).toEqual(NOVA_SESSAO.usuario)
  })

  it('várias requisições com 401 ao mesmo tempo disparam UMA única renovação', async () => {
    // O refresh token é de uso único (rotação): duas renovações paralelas fariam a
    // segunda falhar e derrubar a sessão do usuário.
    localStorage.setItem(CHAVE_REFRESH, 'refresh-antigo')

    const respostas = await Promise.all([
      api.get('/agendamentos/me'),
      api.get('/agendamentos/me/proximo'),
      api.get('/usuarios/me'),
    ])

    expect(refresh).toHaveBeenCalledTimes(1)
    expect(respostas.every((r) => r.data.ok)).toBe(true)
  })

  it('se a renovação falhar, encerra a sessão local; depois pode renovar de novo', async () => {
    localStorage.setItem(CHAVE_REFRESH, 'refresh-revogado')
    localStorage.setItem(CHAVE_USUARIO, '{"id":7}')
    refresh.mockRejectedValueOnce(new AxiosError('HTTP 401'))

    await expect(api.get('/agendamentos/me')).rejects.toMatchObject({
      response: { status: 401 },
    })
    expect(localStorage.getItem(CHAVE_REFRESH)).toBeNull()
    expect(localStorage.getItem(CHAVE_USUARIO)).toBeNull()
    expect(sessaoExpirada).toHaveBeenCalledTimes(1)

    // Após um novo login, a renovação volta a funcionar normalmente.
    localStorage.setItem(CHAVE_REFRESH, 'refresh-de-novo-login')
    await expect(api.get('/usuarios/me')).resolves.toMatchObject({ data: { ok: true } })
    expect(refresh).toHaveBeenCalledTimes(2)
  })

  it('não tenta renovar em rotas de autenticação, sem refresh salvo ou em erros que não são 401', async () => {
    // Senha errada no login: sem renovação.
    localStorage.setItem(CHAVE_REFRESH, 'refresh-antigo')
    await expect(api.post('/auth/login', {})).rejects.toMatchObject({ response: { status: 401 } })

    // Erro de regra de negócio (409): repassado como está.
    api.defaults.adapter = (config) => responder(config, 409, { detail: 'Conflito' })
    await expect(api.post('/agendamentos', {})).rejects.toMatchObject({
      response: { status: 409 },
    })

    // Sem refresh token salvo: apenas repassa o 401.
    localStorage.clear()
    api.defaults.adapter = servidorQueExigeTokenNovo(requisicoes)
    await expect(api.get('/usuarios/me')).rejects.toMatchObject({ response: { status: 401 } })

    expect(refresh).not.toHaveBeenCalled()
    expect(sessaoExpirada).not.toHaveBeenCalled()
  })

  it('não entra em laço: se a repetição também der 401, desiste após uma renovação', async () => {
    localStorage.setItem(CHAVE_REFRESH, 'refresh-antigo')
    api.defaults.adapter = (config) => {
      requisicoes.push(config.url)
      return responder(config, 401)
    }

    await expect(api.get('/usuarios/me')).rejects.toMatchObject({ response: { status: 401 } })
    expect(refresh).toHaveBeenCalledTimes(1)
    expect(requisicoes).toHaveLength(2)
  })
})

describe('mensagemDeErro', () => {
  const erroComDetail = (detail) => ({ response: { data: { detail } } })

  it('usa a mensagem da API, sem o prefixo técnico do Pydantic nas validações', () => {
    expect(mensagemDeErro(erroComDetail('O prazo de cancelamento foi encerrado.'))).toBe(
      'O prazo de cancelamento foi encerrado.',
    )
    const validacao = [
      { msg: 'Value error, CPF inválido. Informe 11 dígitos numéricos válidos.' },
      { msg: 'Outro erro' },
    ]
    expect(mensagemDeErro(erroComDetail(validacao))).toBe(
      'CPF inválido. Informe 11 dígitos numéricos válidos.',
    )
  })

  it('usa mensagens padrão quando a API não informa o motivo', () => {
    expect(mensagemDeErro(erroComDetail([{}]))).toBe('Dados inválidos. Verifique os campos.')
    const generica = 'Não foi possível completar a operação. Tente novamente.'
    for (const erro of [new Error('Network Error'), erroComDetail([]), undefined]) {
      expect(mensagemDeErro(erro)).toBe(generica)
    }
  })
})
