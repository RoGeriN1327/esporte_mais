import { useState } from 'react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'

import { useAuth } from '../contexts/useAuth'

function LinkNav({ para, children }) {
  return (
    <NavLink
      to={para}
      end
      className={({ isActive }) =>
        `rounded-md px-3 py-1.5 text-sm font-medium transition ${
          isActive ? 'bg-emerald-700 text-white' : 'text-emerald-100 hover:bg-emerald-600'
        }`
      }
    >
      {children}
    </NavLink>
  )
}

export default function Layout() {
  const { usuario, ehPessoa, ehAdmin, ehGestor, logout } = useAuth()
  const navigate = useNavigate()
  const [menuAberto, setMenuAberto] = useState(false)

  async function aoSair() {
    await logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-emerald-800 shadow">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2 px-4 py-3">
          <Link to={ehAdmin ? '/admin' : '/'} className="text-xl font-bold text-white">
            Esporte<span className="text-emerald-300">+</span>
          </Link>

          <nav className="order-3 flex w-full flex-wrap gap-1 sm:order-2 sm:w-auto">
            {ehPessoa && (
              <>
                <LinkNav para="/">Início</LinkNav>
                <LinkNav para="/quadras">Agendar quadra</LinkNav>
                <LinkNav para="/meus-agendamentos">Meus agendamentos</LinkNav>
              </>
            )}
            {ehAdmin && (
              <>
                <LinkNav para="/admin">Início</LinkNav>
                <LinkNav para="/admin/quadras">Quadras</LinkNav>
                <LinkNav para="/admin/agendamentos">Agendamentos</LinkNav>
                <LinkNav para="/admin/usuarios">Usuários</LinkNav>
                {ehGestor && <LinkNav para="/admin/administradores">Administradores</LinkNav>}
                {ehGestor && <LinkNav para="/admin/configuracoes">Configurações</LinkNav>}
              </>
            )}
          </nav>

          <div className="relative order-2 sm:order-3">
            <button
              className="flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-700"
              onClick={() => setMenuAberto((aberto) => !aberto)}
            >
              {usuario?.nome}
              <span className="text-xs">▾</span>
            </button>
            {menuAberto && (
              <div
                className="absolute right-0 z-40 mt-1 w-44 overflow-hidden rounded-lg border border-gray-200 bg-white shadow-lg"
                onMouseLeave={() => setMenuAberto(false)}
              >
                {ehPessoa && (
                  <Link
                    to="/perfil"
                    className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                    onClick={() => setMenuAberto(false)}
                  >
                    Meu perfil
                  </Link>
                )}
                <button
                  className="block w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-gray-50"
                  onClick={aoSair}
                >
                  Sair
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  )
}
