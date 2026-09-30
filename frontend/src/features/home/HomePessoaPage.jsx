import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import * as agendamentosApi from '../../api/agendamentos.api'
import { Badge, Carregando } from '../../components/ui'
import { useAuth } from '../../contexts/useAuth'
import { formatarData, formatarHora } from '../../utils/datas'

export default function HomePessoaPage() {
  const { usuario } = useAuth()
  const { data: proximo, isLoading } = useQuery({
    queryKey: ['proximo-agendamento'],
    queryFn: agendamentosApi.proximoAgendamento,
  })

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">Olá, {usuario?.nome?.split(' ')[0]}!</h1>

      <section className="rounded-xl bg-white p-6 shadow">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500">
          Próximo agendamento
        </h2>
        {isLoading ? (
          <Carregando />
        ) : proximo ? (
          <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-lg font-semibold text-gray-800">
                {proximo.nome_quadra} <span className="text-gray-500">({proximo.esporte})</span>
              </p>
              <p className="text-gray-600">
                {formatarData(proximo.data_hora_inicio)} · {formatarHora(proximo.data_hora_inicio)}
                {' às '}
                {formatarHora(proximo.data_hora_fim)} · {proximo.bairro}
              </p>
            </div>
            <Badge>{proximo.status}</Badge>
          </div>
        ) : (
          <p className="mt-3 text-gray-500">
            Você não possui agendamento ativo. Que tal reservar uma quadra?
          </p>
        )}
      </section>

      <div className="grid gap-4 sm:grid-cols-2">
        <Link
          to="/quadras"
          className="rounded-xl bg-emerald-600 p-6 text-center text-lg font-semibold text-white shadow transition hover:bg-emerald-700"
        >
          Agendar quadra
        </Link>
        <Link
          to="/meus-agendamentos"
          className="rounded-xl bg-white p-6 text-center text-lg font-semibold text-emerald-700 shadow transition hover:bg-gray-50"
        >
          Meus agendamentos
        </Link>
      </div>
    </div>
  )
}
