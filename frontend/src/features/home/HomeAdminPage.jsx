// Menu principal do painel administrativo (Gestor e Operador; Figura 6 do DERS):
// indicadores do dia e atalhos para cada área de gestão.
import { useQuery } from '@tanstack/react-query'
import {
  TbBuildingStadium,
  TbCalendarEvent,
  TbCalendarStats,
  TbChevronRight,
  TbSettings,
  TbUserShield,
  TbUsers,
} from 'react-icons/tb'
import { Link } from 'react-router-dom'

import * as adminApi from '../../api/admin.api'
import { useAuth } from '../../contexts/useAuth'
import { dataExtensa, hojeISO } from '../../utils/datas'

function saudacao() {
  const hora = new Date().getHours()
  if (hora < 12) return 'Bom dia'
  if (hora < 18) return 'Boa tarde'
  return 'Boa noite'
}

function Indicador({ Icone, titulo, valor, detalhe, carregando }) {
  return (
    <div className="flex items-center gap-4 rounded-2xl border border-cinza-200 bg-white p-5">
      <span className="grid size-12 shrink-0 place-items-center rounded-xl bg-marca-50 text-marca-700">
        <Icone aria-hidden="true" className="size-6" />
      </span>
      <div className="min-w-0">
        <p className="text-sm font-semibold text-cinza-500">{titulo}</p>
        <p className="text-3xl font-black tabular-nums leading-tight text-cinza-900">{carregando ? '–' : valor}</p>
        {detalhe && <p className="text-xs font-semibold text-cinza-500">{carregando ? 'Carregando…' : detalhe}</p>}
      </div>
    </div>
  )
}

function Atalho({ para, Icone, titulo, descricao }) {
  return (
    <Link
      to={para}
      className="group flex items-center gap-4 rounded-2xl border border-cinza-200 bg-white p-5 transition-colors hover:border-marca-300 hover:bg-marca-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marca-600"
    >
      <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-cinza-100 text-cinza-700 transition-colors group-hover:bg-white group-hover:text-marca-700">
        <Icone aria-hidden="true" className="size-6" />
      </span>
      <span className="min-w-0 flex-1">
        <span className="block font-extrabold text-cinza-900">{titulo}</span>
        <span className="block text-sm text-cinza-600">{descricao}</span>
      </span>
      <TbChevronRight aria-hidden="true" className="size-5 shrink-0 text-cinza-400 transition-transform group-hover:translate-x-0.5" />
    </Link>
  )
}

function plural(quantidade, singular, pluralTexto) {
  return `${quantidade} ${quantidade === 1 ? singular : pluralTexto}`
}

function contar(lista, condicao) {
  return lista ? lista.filter(condicao).length : 0
}

export default function HomeAdminPage() {
  const { usuario, ehGestor } = useAuth()
  const hoje = hojeISO()

  const agendamentosHoje = useQuery({
    queryKey: ['admin-agendamentos', { data: hoje }],
    queryFn: () => adminApi.painelAgendamentos({ data: hoje }),
  })
  const quadras = useQuery({ queryKey: ['admin-quadras', {}], queryFn: () => adminApi.listarQuadrasAdmin() })
  const usuarios = useQuery({ queryKey: ['admin-usuarios-pessoa'], queryFn: adminApi.listarUsuariosPessoa })

  const atalhos = [
    { para: '/admin/agendamentos', Icone: TbCalendarEvent, titulo: 'Gerenciar agendamentos', descricao: 'Consulte, agende para o cidadão, remarque ou cancele.' },
    { para: '/admin/quadras', Icone: TbBuildingStadium, titulo: 'Gerenciar quadras', descricao: 'Cadastre, edite e desative quadras esportivas.' },
    { para: '/admin/usuarios', Icone: TbUsers, titulo: 'Gerenciar usuários', descricao: 'Cadastre, desative e reative cidadãos.' },
    ...(ehGestor
      ? [
          { para: '/admin/administradores', Icone: TbUserShield, titulo: 'Gerenciar administradores', descricao: 'Cadastre, edite e desative Gestores e Operadores.' },
          { para: '/admin/configuracoes', Icone: TbSettings, titulo: 'Configurações', descricao: 'Prazo de cancelamento e antecedência do lembrete.' },
        ]
      : []),
  ]

  return (
    <div className="space-y-10">
      <div>
        <p className="text-sm font-semibold text-cinza-500 first-letter:uppercase">
          {dataExtensa()} · <span className="text-marca-700">{usuario?.perfil}</span>
        </p>
        <h1 className="mt-1 text-3xl font-black text-cinza-900">
          {saudacao()}, {usuario?.nome?.split(' ')[0]}
        </h1>
      </div>

      <section aria-labelledby="titulo-indicadores">
        <h2 id="titulo-indicadores" className="mb-4 text-sm font-bold uppercase tracking-wider text-cinza-500">
          Hoje
        </h2>
        <div className="grid gap-4 sm:grid-cols-3">
          <Indicador
            Icone={TbCalendarStats}
            titulo="Agendamentos hoje"
            valor={agendamentosHoje.data?.length ?? 0}
            detalhe={plural(contar(agendamentosHoje.data, (a) => a.status === 'Confirmado'), 'confirmado', 'confirmados')}
            carregando={agendamentosHoje.isLoading}
          />
          <Indicador
            Icone={TbBuildingStadium}
            titulo="Quadras ativas"
            valor={contar(quadras.data, (q) => q.status === 'Ativa')}
            detalhe={plural(quadras.data?.length ?? 0, 'cadastrada', 'cadastradas')}
            carregando={quadras.isLoading}
          />
          <Indicador
            Icone={TbUsers}
            titulo="Usuários ativos"
            valor={contar(usuarios.data, (u) => u.status === 'Ativo')}
            detalhe={plural(usuarios.data?.length ?? 0, 'cadastrado', 'cadastrados')}
            carregando={usuarios.isLoading}
          />
        </div>
      </section>

      <nav aria-labelledby="titulo-gestao">
        <h2 id="titulo-gestao" className="mb-4 text-sm font-bold uppercase tracking-wider text-cinza-500">
          Gestão
        </h2>
        <div className="grid gap-4 md:grid-cols-2">
          {atalhos.map((atalho) => (
            <Atalho key={atalho.para} {...atalho} />
          ))}
        </div>
      </nav>
    </div>
  )
}
