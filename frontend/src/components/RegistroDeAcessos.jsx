import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'

import { registrarAcesso } from '../api/acessos.api'

// Espera a tela "assentar" antes de registrar: redirecionamentos (ex.: / → /login)
// e o efeito duplicado do StrictMode geram um registro só, o da tela que ficou aberta.
export const ESPERA_MS = 800

export default function RegistroDeAcessos() {
  const { pathname } = useLocation()

  useEffect(() => {
    const temporizador = setTimeout(() => registrarAcesso(pathname), ESPERA_MS)
    return () => clearTimeout(temporizador)
  }, [pathname])

  return null
}
