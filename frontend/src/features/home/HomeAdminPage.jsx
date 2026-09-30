import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import * as adminApi from '../../api/admin.api'
import { useAuth } from '../../contexts/useAuth'
import { hojeISO } from '../../utils/datas'

function saudacao() {
  const hora = new Date().getHours()
  if (hora < 12) return 'Bom dia'
  if (hora < 18) return 'Boa tarde'
  return 'Boa noite'
}

function dataExtensa() {
  return new Date().toLocaleDateString('pt-BR', {
    weekday: 'long',
    day: '2-digit',
    month: 'long',
    year: 'numeric',
  })
}

function CartaoMetrica({ titulo, valor, sublinha, corIcone, icone }) {
  return (
    <div className="flex items-center gap-4 rounded-xl bg-white p-5 shadow-sm">
      <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-lg ${corIcone}`}>
        {icone}
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-xs font-medium uppercase tracking-wide text-gray-500">{titulo}</p>
        <p className="mt-0.5 text-2xl font-bold text-gray-800">{valor}</p>
        {sublinha && <p className="text-xs text-gray-500">{sublinha}</p>}
      </div>
    </div>
  )
}

function CartaoAcao({ para, titulo, descricao, icone }) {
  return (
    <Link
      to={para}
      className="group flex flex-col rounded-xl border border-transparent bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-emerald-200 hover:shadow-md"
    >
      <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-50 text-emerald-700 transition group-hover:bg-emerald-100">
        {icone}
      </div>
      <h3 className="text-base font-semibold text-gray-800 group-hover:text-emerald-700">
        {titulo}
      </h3>
      <p className="mt-1 text-sm text-gray-500">{descricao}</p>
    </Link>
  )
}

function Secao({ titulo, children }) {
  return (
    <section>
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-500">
        {titulo}
      </h2>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{children}</div>
    </section>
  )
}

const Icone = {
  agenda: (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5">
      <rect x="3" y="4" width="18" height="18" rx="2" />
      <path d="M16 2v4M8 2v4M3 10h18" />
    </svg>
  ),
  quadra: (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5">
      <rect x="3" y="6" width="18" height="12" rx="1" />
      <path d="M12 6v12M3 12h4M17 12h4" />
      <circle cx="12" cy="12" r="2" />
    </svg>
  ),
  usuarios: (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  ),
  administrador: (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      <path d="M9 12l2 2 4-4" />
    </svg>
  ),
  engrenagem: (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9c.36.15.68.38.94.68" />
    </svg>
  ),
  relogio: (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6">
      <circle cx="12" cy="12" r="10" />
      <path d="M12 6v6l4 2" />
    </svg>
  ),
  trofeu: (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6">
      <path d="M8 21h8M12 17v4M7 4h10v5a5 5 0 0 1-10 0V4z" />
      <path d="M17 4h3v2a3 3 0 0 1-3 3M7 4H4v2a3 3 0 0 0 3 3" />
    </svg>
  ),
  pessoas: (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
    </svg>
  ),
}

export default function HomeAdminPage() {
  const { usuario, ehGestor } = useAuth()

  const hoje = hojeISO()

  const { data: agendamentosHoje } = useQuery({
    queryKey: ['admin-agendamentos-hoje', hoje],
    queryFn: () => adminApi.painelAgendamentos({ data: hoje }),
  })
  const { data: quadras } = useQuery({
    queryKey: ['admin-quadras'],
    queryFn: () => adminApi.listarQuadrasAdmin(),
  })
  const { data: usuarios } = useQuery({
    queryKey: ['admin-usuarios-pessoa'],
    queryFn: () => adminApi.listarUsuariosPessoa(),
  })

  const totalAgendamentosHoje = agendamentosHoje?.length ?? '—'
  const confirmadosHoje = agendamentosHoje?.filter((a) => a.status === 'Confirmado').length ?? 0
  const quadrasAtivas = quadras?.filter((q) => q.status === 'Ativa').length ?? '—'
  const totalQuadras = quadras?.length ?? 0
  const usuariosAtivos = usuarios?.filter((u) => u.status === 'Ativo').length ?? '—'
  const totalUsuarios = usuarios?.length ?? 0

  return (
    <div className="space-y-8">
      <div className="rounded-xl bg-gradient-to-r from-emerald-700 to-emerald-800 p-6 text-white shadow">
        <h1 className="text-2xl font-bold sm:text-3xl">
          {saudacao()}, {usuario?.nome?.split(' ')[0] || 'admin'}
        </h1>
        <p className="mt-1 text-sm text-emerald-100">
          {usuario?.perfil} · <span className="capitalize">{dataExtensa()}</span>
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <CartaoMetrica
          titulo="Agendamentos hoje"
          valor={totalAgendamentosHoje}
          sublinha={`${confirmadosHoje} confirmado(s)`}
          corIcone="bg-emerald-100 text-emerald-700"
          icone={Icone.relogio}
        />
        <CartaoMetrica
          titulo="Quadras ativas"
          valor={quadrasAtivas}
          sublinha={`${totalQuadras} cadastrada(s)`}
          corIcone="bg-blue-100 text-blue-700"
          icone={Icone.trofeu}
        />
        <CartaoMetrica
          titulo="Usuários ativos"
          valor={usuariosAtivos}
          sublinha={`${totalUsuarios} cadastrado(s)`}
          corIcone="bg-amber-100 text-amber-700"
          icone={Icone.pessoas}
        />
      </div>

      <Secao titulo="Operação">
        <CartaoAcao
          para="/admin/agendamentos"
          titulo="Painel de Agendamentos"
          descricao="Consulte, agende em nome do cidadão, remarque ou cancele."
          icone={Icone.agenda}
        />
      </Secao>

      <Secao titulo="Cadastros">
        <CartaoAcao
          para="/admin/quadras"
          titulo="Quadras"
          descricao="Cadastre, edite e desative quadras esportivas."
          icone={Icone.quadra}
        />
        <CartaoAcao
          para="/admin/usuarios"
          titulo="Usuários"
          descricao="Cadastre, desative e reative Usuários Pessoa."
          icone={Icone.usuarios}
        />
        {ehGestor && (
          <CartaoAcao
            para="/admin/administradores"
            titulo="Administradores"
            descricao="Cadastre, edite e desative Gestores e Operadores."
            icone={Icone.administrador}
          />
        )}
      </Secao>

      {ehGestor && (
        <Secao titulo="Sistema">
          <CartaoAcao
            para="/admin/configuracoes"
            titulo="Configurações"
            descricao="Prazo mínimo de cancelamento e antecedência do lembrete."
            icone={Icone.engrenagem}
          />
        </Secao>
      )}
    </div>
  )
}
