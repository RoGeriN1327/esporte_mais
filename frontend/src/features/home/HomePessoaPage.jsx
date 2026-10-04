// Menu principal do Usuário Pessoa (RF001, fluxo A1; botões do Quadro 11 do DERS):
// próximo agendamento ativo ao centro, quando existir, e os atalhos "Meus agendamentos" e "Agendar quadra".
import { useQuery } from '@tanstack/react-query'
import { TbCalendarOff, TbCalendarPlus, TbChevronRight, TbClock, TbListDetails, TbMapPin } from 'react-icons/tb'
import { Link } from 'react-router-dom'

import * as agendamentosApi from '../../api/agendamentos.api'
import IconeEsporte from '../../components/IconeEsporte'
import { Alerta, Badge, Carregando } from '../../components/ui'
import { useAuth } from '../../contexts/useAuth'
import { dataExtensa, formatarHora, partesDaData } from '../../utils/datas'

function ProximoAgendamento({ agendamento }) {
  const { diaSemana, dia, mes } = partesDaData(agendamento.data_hora_inicio)
  return (
    <div className="flex flex-col gap-5 sm:flex-row sm:items-center">
      <div className="flex w-full shrink-0 items-baseline justify-center gap-3 rounded-xl bg-marca-600 px-5 py-4 text-white sm:w-28 sm:items-center sm:flex-col sm:gap-0 sm:px-0 sm:py-5">
        <span className="text-sm font-bold uppercase tracking-wider text-marca-100">{diaSemana}</span>
        <span className="text-4xl font-black tabular-nums leading-none sm:mt-1">{dia}</span>
        <span className="text-sm font-bold uppercase tracking-wider text-marca-100 sm:mt-1">{mes}</span>
      </div>

      <div className="min-w-0 flex-1 space-y-3">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <h3 className="min-w-0 break-words text-xl font-extrabold text-cinza-900">{agendamento.nome_quadra}</h3>
          <Badge>{agendamento.status}</Badge>
        </div>
        <dl className="grid gap-2 text-[15px] text-cinza-700 sm:grid-cols-2">
          <div className="flex items-center gap-2">
            <dt className="sr-only">Horário</dt>
            <TbClock aria-hidden="true" className="size-5 shrink-0 text-marca-600" />
            <dd className="font-bold tabular-nums text-cinza-900">
              {formatarHora(agendamento.data_hora_inicio)} – {formatarHora(agendamento.data_hora_fim)}
            </dd>
          </div>
          <div className="flex items-center gap-2">
            <dt className="sr-only">Esporte</dt>
            <IconeEsporte esporte={agendamento.esporte} className="size-5 shrink-0 text-marca-600" />
            <dd>{agendamento.esporte}</dd>
          </div>
          <div className="flex min-w-0 items-center gap-2 sm:col-span-2">
            <dt className="sr-only">Bairro</dt>
            <TbMapPin aria-hidden="true" className="size-5 shrink-0 text-marca-600" />
            <dd className="truncate">{agendamento.bairro}</dd>
          </div>
        </dl>
      </div>
    </div>
  )
}

function SemAgendamento() {
  return (
    <div className="flex flex-col items-center gap-3 py-6 text-center">
      <span className="grid size-12 place-items-center rounded-full bg-cinza-100 text-cinza-500">
        <TbCalendarOff aria-hidden="true" className="size-6" />
      </span>
      <div>
        <p className="font-bold text-cinza-900">Você não possui agendamento ativo.</p>
        <p className="mt-1 text-sm text-cinza-600">Use “Agendar quadra” para reservar um horário.</p>
      </div>
    </div>
  )
}

function Atalho({ para, Icone, titulo, descricao, destaque = false }) {
  return (
    <Link
      to={para}
      className={`group flex items-center gap-4 rounded-xl border p-5 transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marca-600 ${
        destaque
          ? 'border-marca-600 bg-marca-600 text-white hover:border-marca-700 hover:bg-marca-700'
          : 'border-cinza-200 bg-white text-cinza-900 hover:border-marca-300 hover:bg-marca-50'
      }`}
    >
      <span
        className={`grid size-12 shrink-0 place-items-center rounded-lg ${destaque ? 'bg-white/15 text-white' : 'bg-marca-50 text-marca-700'}`}
      >
        <Icone aria-hidden="true" className="size-6" />
      </span>
      <span className="min-w-0 flex-1">
        <span className="block text-lg font-extrabold">{titulo}</span>
        <span className={`block text-sm ${destaque ? 'text-marca-100' : 'text-cinza-600'}`}>{descricao}</span>
      </span>
      <TbChevronRight
        aria-hidden="true"
        className={`size-5 shrink-0 transition-transform group-hover:translate-x-0.5 ${destaque ? 'text-white' : 'text-cinza-400'}`}
      />
    </Link>
  )
}

export default function HomePessoaPage() {
  const { usuario } = useAuth()
  const { data: proximo, isLoading, isError } = useQuery({
    queryKey: ['proximo-agendamento'],
    queryFn: agendamentosApi.proximoAgendamento,
  })

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <div>
        <p className="text-sm font-semibold text-cinza-500 first-letter:uppercase">{dataExtensa()}</p>
        <h1 className="mt-1 text-3xl font-black text-cinza-900">Olá, {usuario?.nome?.split(' ')[0]}</h1>
      </div>

      <section aria-labelledby="titulo-proximo" className="rounded-2xl border border-cinza-200 bg-white p-5 sm:p-6">
        <h2 id="titulo-proximo" className="mb-5 text-sm font-bold uppercase tracking-wider text-cinza-500">
          Próximo agendamento
        </h2>
        {isLoading ? (
          <Carregando texto="Carregando seu próximo agendamento…" />
        ) : isError ? (
          <Alerta tipo="erro">Não foi possível carregar seu próximo agendamento. Recarregue a página para tentar de novo.</Alerta>
        ) : proximo ? (
          <ProximoAgendamento agendamento={proximo} />
        ) : (
          <SemAgendamento />
        )}
      </section>

      <nav aria-label="Ações" className="grid gap-4 sm:grid-cols-2">
        <Atalho
          para="/meus-agendamentos"
          Icone={TbListDetails}
          titulo="Meus agendamentos"
          descricao="Consulte, renove ou cancele"
        />
        <Atalho
          para="/quadras"
          Icone={TbCalendarPlus}
          titulo="Agendar quadra"
          descricao="Encontre uma quadra disponível"
          destaque
        />
      </nav>
    </div>
  )
}
