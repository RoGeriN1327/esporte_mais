import { createContext, useContext } from 'react'

// Separado do AuthProvider (AuthContext.jsx) para que aquele arquivo exporte apenas
// componentes — requisito do Fast Refresh do Vite.
export const AuthContext = createContext(null)

export function useAuth() {
  return useContext(AuthContext)
}
