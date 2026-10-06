import { useCallback, useEffect, useMemo, useState } from 'react'

import * as authApi from '../api/auth.api'
import {
  CHAVE_REFRESH,
  CHAVE_SESSAO_EXPIRA,
  CHAVE_USUARIO,
  definirAccessToken,
  registrarSessaoExpirada,
  renovarSessao,
  sessaoVencida,
} from '../api/client'
import { AuthContext } from './useAuth'

// De quanto em quanto tempo conferir se a sessão acabou. Um intervalo curto (em vez de
// um único setTimeout de 2 horas) continua certo mesmo se o computador hibernar.
const INTERVALO_VERIFICACAO_MS = 15_000

export function AuthProvider({ children }) {
  const [usuario, setUsuario] = useState(null)
  // true quando a sessão terminou sozinha (não por logout): o login mostra um aviso.
  const [sessaoExpirada, setSessaoExpirada] = useState(false)
  // Só há o que carregar se existir uma sessão salva para renovar.
  const [carregando, setCarregando] = useState(() => localStorage.getItem(CHAVE_REFRESH) !== null)

  const guardarSessao = useCallback((dados) => {
    localStorage.setItem(CHAVE_REFRESH, dados.refresh_token)
    localStorage.setItem(CHAVE_USUARIO, JSON.stringify(dados.usuario))
    localStorage.setItem(CHAVE_SESSAO_EXPIRA, dados.sessao_expira_em)
    definirAccessToken(dados.access_token)
    setSessaoExpirada(false)
    setUsuario(dados.usuario)
  }, [])

  const limparSessao = useCallback(() => {
    localStorage.removeItem(CHAVE_REFRESH)
    localStorage.removeItem(CHAVE_USUARIO)
    localStorage.removeItem(CHAVE_SESSAO_EXPIRA)
    definirAccessToken(null)
    setUsuario(null)
  }, [])

  const expirarSessao = useCallback(() => {
    limparSessao()
    setSessaoExpirada(true)
  }, [limparSessao])

  useEffect(() => {
    registrarSessaoExpirada(() => {
      setUsuario(null)
      setSessaoExpirada(true)
    })
    if (!localStorage.getItem(CHAVE_REFRESH)) return
    // renovarSessao() é compartilhada: se o efeito rodar duas vezes (StrictMode) ou se
    // uma requisição já estiver renovando, todos aguardam a mesma chamada ao backend.
    renovarSessao()
      .then((data) => guardarSessao(data))
      // Página reaberta depois do fim da sessão: renovarSessao() nem chama o backend.
      .catch(() => (sessaoVencida() ? expirarSessao() : limparSessao()))
      .finally(() => setCarregando(false))
  }, [guardarSessao, limparSessao, expirarSessao])

  // Encerra a sessão quando as 2 horas acabam, mesmo sem nenhuma ação do usuário.
  useEffect(() => {
    if (!usuario) return undefined
    const verificar = () => {
      if (sessaoVencida()) expirarSessao()
    }
    verificar()
    const intervalo = setInterval(verificar, INTERVALO_VERIFICACAO_MS)
    document.addEventListener('visibilitychange', verificar)
    window.addEventListener('focus', verificar)
    return () => {
      clearInterval(intervalo)
      document.removeEventListener('visibilitychange', verificar)
      window.removeEventListener('focus', verificar)
    }
  }, [usuario, expirarSessao])

  const login = useCallback(
    async (email, senha) => {
      const dados = await authApi.login(email, senha)
      guardarSessao(dados)
      return dados.usuario
    },
    [guardarSessao],
  )

  const logout = useCallback(async () => {
    const refresh = localStorage.getItem(CHAVE_REFRESH)
    try {
      if (refresh) await authApi.logout(refresh)
    } catch {
      // Falha no logout remoto (rede, sessão já expirada) não impede encerrar a sessão local.
    }
    limparSessao()
  }, [limparSessao])

  const valor = useMemo(
    () => ({
      usuario,
      carregando,
      sessaoExpirada,
      ehPessoa: usuario?.tipo === 'Pessoa',
      ehAdmin: usuario?.tipo === 'Administrativo',
      ehGestor: usuario?.tipo === 'Administrativo' && usuario?.perfil === 'Gestor',
      login,
      logout,
      limparSessao,
    }),
    [usuario, carregando, sessaoExpirada, login, logout, limparSessao],
  )

  return <AuthContext.Provider value={valor}>{children}</AuthContext.Provider>
}
