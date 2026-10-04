import { useCallback, useEffect, useMemo, useState } from 'react'

import * as authApi from '../api/auth.api'
import {
  CHAVE_REFRESH,
  CHAVE_USUARIO,
  definirAccessToken,
  registrarSessaoExpirada,
  renovarSessao,
} from '../api/client'
import { AuthContext } from './useAuth'

export function AuthProvider({ children }) {
  const [usuario, setUsuario] = useState(null)
  // Só há o que carregar se existir uma sessão salva para renovar.
  const [carregando, setCarregando] = useState(() => localStorage.getItem(CHAVE_REFRESH) !== null)

  const guardarSessao = useCallback((dados) => {
    localStorage.setItem(CHAVE_REFRESH, dados.refresh_token)
    localStorage.setItem(CHAVE_USUARIO, JSON.stringify(dados.usuario))
    definirAccessToken(dados.access_token)
    setUsuario(dados.usuario)
  }, [])

  const limparSessao = useCallback(() => {
    localStorage.removeItem(CHAVE_REFRESH)
    localStorage.removeItem(CHAVE_USUARIO)
    definirAccessToken(null)
    setUsuario(null)
  }, [])

  useEffect(() => {
    registrarSessaoExpirada(() => setUsuario(null))
    if (!localStorage.getItem(CHAVE_REFRESH)) return
    // renovarSessao() é compartilhada: se o efeito rodar duas vezes (StrictMode) ou se
    // uma requisição já estiver renovando, todos aguardam a mesma chamada ao backend.
    renovarSessao()
      .then((data) => guardarSessao(data))
      .catch(() => limparSessao())
      .finally(() => setCarregando(false))
  }, [guardarSessao, limparSessao])

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
      ehPessoa: usuario?.tipo === 'Pessoa',
      ehAdmin: usuario?.tipo === 'Administrativo',
      ehGestor: usuario?.tipo === 'Administrativo' && usuario?.perfil === 'Gestor',
      login,
      logout,
      limparSessao,
    }),
    [usuario, carregando, login, logout, limparSessao],
  )

  return <AuthContext.Provider value={valor}>{children}</AuthContext.Provider>
}
