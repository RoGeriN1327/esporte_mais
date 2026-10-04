// Estrutura das telas logadas: cabeçalho com a marca, navegação do perfil e menu do usuário
// (Quadro 12 do DERS). No celular, a navegação vira um painel lateral aberto pelo botão de menu.
import { useEffect, useRef, useState } from 'react'
import {
  TbBuildingStadium,
  TbCalendarEvent,
  TbCalendarPlus,
  TbChevronDown,
  TbHome,
  TbLayoutDashboard,
  TbListDetails,
  TbLogout,
  TbMenu2,
  TbSettings,
  TbUser,
  TbUserShield,
  TbUsers,
  TbX,
} from 'react-icons/tb'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'

import { useAuth } from '../contexts/useAuth'
import Avatar from './Avatar'

const NAV_PESSOA = [
  { para: '/', rotulo: 'Início', Icone: TbHome, exato: true },
  { para: '/quadras', rotulo: 'Agendar quadra', Icone: TbCalendarPlus },
  { para: '/meus-agendamentos', rotulo: 'Meus agendamentos', Icone: TbListDetails },
]

function navAdmin(ehGestor) {
  return [
    { para: '/admin', rotulo: 'Início', Icone: TbLayoutDashboard, exato: true },
    { para: '/admin/quadras', rotulo: 'Quadras', Icone: TbBuildingStadium },
    { para: '/admin/agendamentos', rotulo: 'Agendamentos', Icone: TbCalendarEvent },
    { para: '/admin/usuarios', rotulo: 'Usuários', Icone: TbUsers },
    ...(ehGestor
      ? [
          { para: '/admin/administradores', rotulo: 'Administradores', Icone: TbUserShield },
          { para: '/admin/configuracoes', rotulo: 'Configurações', Icone: TbSettings },
        ]
      : []),
  ]
}

/** Fecha algo (menu/painel) ao clicar fora do elemento ou ao pressionar Esc. */
function useFecharFora(aberto, fechar, ref) {
  useEffect(() => {
    if (!aberto) return
    function aoClicar(evento) {
      if (ref && !ref.current?.contains(evento.target)) fechar()
    }
    function aoTeclar(evento) {
      if (evento.key === 'Escape') fechar()
    }
    if (ref) document.addEventListener('mousedown', aoClicar)
    document.addEventListener('keydown', aoTeclar)
    return () => {
      document.removeEventListener('mousedown', aoClicar)
      document.removeEventListener('keydown', aoTeclar)
    }
  }, [aberto, fechar, ref])
}

function LinkNavegacao({ item, aoClicar, empilhado = false }) {
  const { para, rotulo, Icone, exato } = item
  return (
    <NavLink
      to={para}
      end={exato}
      onClick={aoClicar}
      className={({ isActive }) =>
        `flex items-center gap-2 whitespace-nowrap rounded-lg font-bold transition-colors focus-visible:outline-2 focus-visible:outline-marca-600 ${
          empilhado ? 'px-3 py-3 text-[15px]' : 'px-3 py-2 text-sm'
        } ${isActive ? 'bg-marca-50 text-marca-700' : 'text-cinza-600 hover:bg-cinza-100 hover:text-cinza-900'}`
      }
    >
      <Icone aria-hidden="true" className="size-[18px] shrink-0" />
      {rotulo}
    </NavLink>
  )
}

const CLASSE_ITEM_MENU =
  'flex w-full items-center gap-2.5 rounded-md px-3 py-2.5 text-left text-sm font-bold transition-colors focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-marca-600'

function MenuUsuario({ nome, ehPessoa, onSair }) {
  const [aberto, setAberto] = useState(false)
  const raiz = useRef(null)
  useFecharFora(aberto, () => setAberto(false), raiz)

  return (
    <div ref={raiz} className="relative hidden lg:block">
      <button
        type="button"
        onClick={() => setAberto((valor) => !valor)}
        aria-haspopup="menu"
        aria-expanded={aberto}
        className="flex items-center gap-2.5 rounded-lg py-1.5 pl-1.5 pr-2.5 transition-colors hover:bg-cinza-100 focus-visible:outline-2 focus-visible:outline-marca-600"
      >
        <Avatar nome={nome} />
        <span className="max-w-40 truncate text-sm font-bold text-cinza-800">{nome}</span>
        <TbChevronDown aria-hidden="true" className={`size-4 text-cinza-500 transition-transform ${aberto ? 'rotate-180' : ''}`} />
      </button>

      {aberto && (
        <div role="menu" className="absolute right-0 z-40 mt-2 w-56 rounded-xl border border-cinza-200 bg-white p-1.5 shadow-lg shadow-cinza-900/5">
          {ehPessoa && (
            <Link to="/perfil" role="menuitem" onClick={() => setAberto(false)} className={`${CLASSE_ITEM_MENU} text-cinza-800 hover:bg-cinza-100`}>
              <TbUser aria-hidden="true" className="size-[18px] text-cinza-500" />
              Meu perfil
            </Link>
          )}
          <button type="button" role="menuitem" onClick={onSair} className={`${CLASSE_ITEM_MENU} text-erro-700 hover:bg-erro-50`}>
            <TbLogout aria-hidden="true" className="size-[18px]" />
            Sair
          </button>
        </div>
      )}
    </div>
  )
}

function PainelCelular({ aberto, onFechar, itens, nome, ehPessoa, onSair }) {
  useFecharFora(aberto, onFechar)
  const painel = useRef(null)
  useEffect(() => {
    if (aberto) painel.current?.focus()
  }, [aberto])

  if (!aberto) return null
  return (
    <div className="fixed inset-0 z-50 lg:hidden">
      <div aria-hidden="true" className="absolute inset-0 bg-cinza-900/40" onClick={onFechar} />
      <div
        ref={painel}
        role="dialog"
        aria-modal="true"
        aria-label="Menu"
        tabIndex={-1}
        className="absolute inset-y-0 right-0 flex w-[min(20rem,85vw)] flex-col overscroll-contain bg-white outline-none motion-safe:animate-entrar"
      >
        <div className="flex h-16 items-center justify-between border-b border-cinza-200 px-4">
          <div className="flex min-w-0 items-center gap-2.5">
            <Avatar nome={nome} />
            <span className="truncate text-sm font-bold text-cinza-800">{nome}</span>
          </div>
          <button
            type="button"
            onClick={onFechar}
            aria-label="Fechar menu"
            className="grid size-10 place-items-center rounded-lg text-cinza-600 transition-colors hover:bg-cinza-100 focus-visible:outline-2 focus-visible:outline-marca-600"
          >
            <TbX aria-hidden="true" className="size-5" />
          </button>
        </div>
        <nav aria-label="Navegação principal" className="flex flex-1 flex-col gap-1 overflow-y-auto p-3">
          {itens.map((item) => (
            <LinkNavegacao key={item.para} item={item} aoClicar={onFechar} empilhado />
          ))}
        </nav>
        <div className="space-y-1 border-t border-cinza-200 p-3 pb-[max(0.75rem,env(safe-area-inset-bottom))]">
          {ehPessoa && (
            <Link to="/perfil" onClick={onFechar} className={`${CLASSE_ITEM_MENU} py-3 text-cinza-800 hover:bg-cinza-100`}>
              <TbUser aria-hidden="true" className="size-[18px] text-cinza-500" />
              Meu perfil
            </Link>
          )}
          <button type="button" onClick={onSair} className={`${CLASSE_ITEM_MENU} py-3 text-erro-700 hover:bg-erro-50`}>
            <TbLogout aria-hidden="true" className="size-[18px]" />
            Sair
          </button>
        </div>
      </div>
    </div>
  )
}

export default function Layout() {
  const { usuario, ehPessoa, ehAdmin, ehGestor, logout } = useAuth()
  const navigate = useNavigate()
  const [painelAberto, setPainelAberto] = useState(false)
  const itens = ehAdmin ? navAdmin(ehGestor) : NAV_PESSOA
  const nome = usuario?.nome ?? ''

  async function aoSair() {
    setPainelAberto(false)
    await logout()
    navigate('/login')
  }

  return (
    <div className="min-h-dvh bg-cinza-50">
      <a
        href="#conteudo"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-white focus:px-4 focus:py-2 focus:font-bold focus:text-marca-700 focus:shadow"
      >
        Pular para o conteúdo
      </a>
      <header className="sticky top-0 z-30 border-b border-cinza-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center gap-6 px-4 sm:px-6">
          <Link
            to={ehAdmin ? '/admin' : '/'}
            className="shrink-0 rounded-md focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-marca-600"
          >
            <img src="/marca/logo.svg" alt="Esporte+ — início" width="133" height="34" className="h-[34px] w-auto" />
          </Link>

          <nav aria-label="Navegação principal" className="hidden min-w-0 flex-1 gap-1 lg:flex">
            {itens.map((item) => (
              <LinkNavegacao key={item.para} item={item} />
            ))}
          </nav>

          <div className="ml-auto flex items-center">
            <MenuUsuario nome={nome} ehPessoa={ehPessoa} onSair={aoSair} />
            <button
              type="button"
              onClick={() => setPainelAberto(true)}
              aria-label="Abrir menu"
              aria-expanded={painelAberto}
              className="grid size-10 place-items-center rounded-lg text-cinza-700 transition-colors hover:bg-cinza-100 focus-visible:outline-2 focus-visible:outline-marca-600 lg:hidden"
            >
              <TbMenu2 aria-hidden="true" className="size-6" />
            </button>
          </div>
        </div>
      </header>

      <PainelCelular
        aberto={painelAberto}
        onFechar={() => setPainelAberto(false)}
        itens={itens}
        nome={nome}
        ehPessoa={ehPessoa}
        onSair={aoSair}
      />

      <main id="conteudo" className="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-10">
        <Outlet />
      </main>
    </div>
  )
}
