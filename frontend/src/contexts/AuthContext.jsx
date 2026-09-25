import { createContext, useContext, useEffect, useMemo, useState } from 'react'

import * as authApi from '../api/auth.api'
import api, {
  CHAVE_REFRESH,
  CHAVE_USUARIO,
  definirAccessToken,
  registrarSessaoExpirada,
} from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [usuario, setUsuario] = useState(null)
  const [carregando, setCarregando] = useState(true)

  function guardarSessao(dados) {
    localStorage.setItem(CHAVE_REFRESH, dados.refresh_token)
    localStorage.setItem(CHAVE_USUARIO, JSON.stringify(dados.usuario))
    definirAccessToken(dados.access_token)
    setUsuario(dados.usuario)
  }

  function limparSessao() {
    localStorage.removeItem(CHAVE_REFRESH)
    localStorage.removeItem(CHAVE_USUARIO)
    definirAccessToken(null)
    setUsuario(null)
  }

  useEffect(() => {
    registrarSessaoExpirada(() => setUsuario(null))
    const refresh = localStorage.getItem(CHAVE_REFRESH)
    if (!refresh) {
      setCarregando(false)
      return
    }
    api
      .post('/auth/refresh', { refresh_token: refresh })
      .then(({ data }) => guardarSessao(data))
      .catch(() => limparSessao())
      .finally(() => setCarregando(false))
  }, [])

  async function login(email, senha) {
    const dados = await authApi.login(email, senha)
    guardarSessao(dados)
    return dados.usuario
  }

  async function logout() {
    const refresh = localStorage.getItem(CHAVE_REFRESH)
    try {
      if (refresh) await authApi.logout(refresh)
    } catch {

    }
    limparSessao()
  }

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
    [usuario, carregando],
  )

  return <AuthContext.Provider value={valor}>{children}</AuthContext.Provider>
}

export function useAuth() {
  return useContext(AuthContext)
}
