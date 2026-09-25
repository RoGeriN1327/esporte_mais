import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useLocation } from 'react-router-dom'

import * as agendamentosApi from '../../api/agendamentos.api'
import { mensagemDeErro } from '../../api/client'
import SeletorDataHorario from '../../components/SeletorDataHorario'
import { Alerta, Badge, Botao, Campo, Carregando, Modal, classesDeInput } from '../../components/ui'
import { formatarData, formatarDataHora, formatarHora } from '../../utils/datas'

const FILTROS_VAZIOS = { data: '', nome_quadra: '', esporte: '', status: '' }
const STATUS = ['Confirmado', 'Cancelado', 'Concluído', 'Renovado']

export default function MeusAgendamentosPage() {
  const location = useLocation()
  const queryClient = useQueryClient()
  const [formulario, setFormulario] = useState(FILTROS_VAZIOS)
  const [filtros, setFiltros] = useState(FILTROS_VAZIOS)
  const [mensagem, setMensagem] = useState(location.state?.mensagem || '')
  const [erro, setErro] = useState('')
  const [cancelando, setCancelando] = useState(null)
  const [renovando, setRenovando] = useState(null)
  const [detalhando, setDetalhando] = useState(null)
  const [dataRenovacao, setDataRenovacao] = useState('')
  const [horaRenovacao, setHoraRenovacao] = useState('')

  const { data: agendamentos, isLoading } = useQuery({
    queryKey: ['meus-agendamentos', filtros],
    queryFn: () =>
      agendamentosApi.meusAgendamentos({
        data: filtros.data || undefined,
        nome_quadra: filtros.nome_quadra || undefined,
        esporte: filtros.esporte || undefined,
        status: filtros.status || undefined,
      }),
  })

  const esportesDoUsuario = [...new Set((agendamentos || []).map((registro) => registro.esporte))]

  function aoConcluirMutacao(mensagemSucesso) {
    return {
      onSuccess: () => {
        setErro('')
        setMensagem(mensagemSucesso)
        setCancelando(null)
        setRenovando(null)
        queryClient.invalidateQueries({ queryKey: ['meus-agendamentos'] })
        queryClient.invalidateQueries({ queryKey: ['proximo-agendamento'] })
      },
      onError: (excecao) => {
        setMensagem('')
        setErro(mensagemDeErro(excecao))
        setCancelando(null)
        setRenovando(null)
      },
    }
  }

  const cancelar = useMutation({
    mutationFn: (id) => agendamentosApi.cancelarAgendamento(id),
    ...aoConcluirMutacao('Agendamento cancelado com sucesso. O horário foi liberado.'),
  })

  const renovar = useMutation({
    mutationFn: () =>
      agendamentosApi.renovarAgendamento(renovando.id, {
        data: dataRenovacao,
        horaInicio: horaRenovacao,
      }),
    ...aoConcluirMutacao('Renovação confirmada! Um novo agendamento foi criado.'),
  })

  function atualizarCampo(campo, valor) {
    setFormulario((atual) => ({ ...atual, [campo]: valor }))
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">Meus agendamentos</h1>

      {}
      <form
        className="grid gap-4 rounded-xl bg-white p-4 shadow sm:grid-cols-2 lg:grid-cols-5"
        onSubmit={(evento) => {
          evento.preventDefault()
          setFiltros(formulario)
        }}
      >
        <Campo label="Data">
          <input
            type="date"
            className={classesDeInput(false)}
            value={formulario.data}
            onChange={(evento) => atualizarCampo('data', evento.target.value)}
          />
        </Campo>
        <Campo label="Nome da quadra">
          <input
            className={classesDeInput(false)}
            value={formulario.nome_quadra}
            onChange={(evento) => atualizarCampo('nome_quadra', evento.target.value)}
          />
        </Campo>
        <Campo label="Esporte">
          <select
            className={classesDeInput(false)}
            value={formulario.esporte}
            onChange={(evento) => atualizarCampo('esporte', evento.target.value)}
          >
            <option value="">Todos</option>
            {esportesDoUsuario.map((esporte) => (
              <option key={esporte} value={esporte}>
                {esporte}
              </option>
            ))}
          </select>
        </Campo>
        <Campo label="Status">
          <select
            className={classesDeInput(false)}
            value={formulario.status}
            onChange={(evento) => atualizarCampo('status', evento.target.value)}
          >
            <option value="">Todos</option>
            {STATUS.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>
        </Campo>
        <div className="flex items-end gap-2">
          <Botao type="submit" className="flex-1">
            Buscar
          </Botao>
          <Botao
            type="button"
            variante="secundario"
            onClick={() => {
              setFormulario(FILTROS_VAZIOS)
              setFiltros(FILTROS_VAZIOS)
            }}
          >
            Limpar filtros
          </Botao>
        </div>
      </form>

      <Alerta tipo="sucesso">{mensagem}</Alerta>
      <Alerta tipo="erro">{erro}</Alerta>

      {}
      {isLoading ? (
        <Carregando />
      ) : (agendamentos || []).length === 0 ? (
        <p className="py-8 text-center text-gray-500">Nenhum agendamento encontrado.</p>
      ) : (
        <div className="space-y-3">
          {agendamentos.map((agendamento) => (
            <div
              key={agendamento.id}
              className="flex flex-wrap items-center justify-between gap-3 rounded-xl bg-white p-4 shadow"
            >
              <div>
                <p className="font-semibold text-gray-800">
                  {agendamento.nome_quadra}{' '}
                  <span className="font-normal text-gray-500">({agendamento.esporte})</span>
                </p>
                <p className="text-sm text-gray-600">
                  {formatarData(agendamento.data_hora_inicio)} ·{' '}
                  {formatarHora(agendamento.data_hora_inicio)} às{' '}
                  {formatarHora(agendamento.data_hora_fim)} · {agendamento.bairro}
                </p>
              </div>
              <div className="flex items-center gap-3">
                <Badge>{agendamento.status}</Badge>
                <Botao variante="secundario" onClick={() => setDetalhando(agendamento)}>
                  Ver detalhes
                </Botao>
                {agendamento.status === 'Confirmado' && (
                  <Botao variante="perigo" onClick={() => setCancelando(agendamento)}>
                    Cancelar
                  </Botao>
                )}
                {agendamento.status === 'Concluído' && (
                  <Botao
                    onClick={() => {
                      setRenovando(agendamento)
                      setDataRenovacao('')
                      setHoraRenovacao('')
                    }}
                  >
                    Renovar
                  </Botao>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {}
      <Modal
        aberto={Boolean(cancelando)}
        titulo="Cancelar agendamento"
        onFechar={() => setCancelando(null)}
      >
        {cancelando && (
          <div className="space-y-4">
            <p className="text-sm text-gray-600">
              Confirmar o cancelamento do agendamento em{' '}
              <strong>{cancelando.nome_quadra}</strong> no dia{' '}
              <strong>{formatarData(cancelando.data_hora_inicio)}</strong> às{' '}
              <strong>{formatarHora(cancelando.data_hora_inicio)}</strong>?
            </p>
            <div className="flex justify-end gap-3">
              <Botao variante="secundario" onClick={() => setCancelando(null)}>
                Voltar
              </Botao>
              <Botao
                variante="perigo"
                onClick={() => cancelar.mutate(cancelando.id)}
                carregando={cancelar.isPending}
              >
                Confirmar cancelamento
              </Botao>
            </div>
          </div>
        )}
      </Modal>

      {}
      <Modal
        aberto={Boolean(renovando)}
        titulo="Renovar agendamento"
        onFechar={() => setRenovando(null)}
      >
        {renovando && (
          <div className="space-y-4">
            <Campo label="Nome da quadra">
              <input
                className={classesDeInput(false)}
                value={`${renovando.nome_quadra} — ${renovando.esporte}`}
                disabled
                readOnly
              />
            </Campo>
            <SeletorDataHorario
              quadraId={renovando.id_quadra}
              data={dataRenovacao}
              hora={horaRenovacao}
              onMudarData={setDataRenovacao}
              onMudarHora={setHoraRenovacao}
            />
            <div className="flex justify-end gap-3">
              <Botao variante="secundario" onClick={() => setRenovando(null)}>
                Fechar
              </Botao>
              <Botao
                onClick={() => renovar.mutate()}
                carregando={renovar.isPending}
                disabled={!dataRenovacao || !horaRenovacao}
              >
                Confirmar renovação
              </Botao>
            </div>
          </div>
        )}
      </Modal>

      {}
      <Modal
        aberto={Boolean(detalhando)}
        titulo="Detalhes do agendamento"
        onFechar={() => setDetalhando(null)}
      >
        {detalhando && (
          <div className="space-y-4">
            <div className="rounded-lg bg-gray-50 p-4">
              <p className="text-lg font-semibold text-gray-800">{detalhando.nome_quadra}</p>
              <p className="text-sm text-gray-600">{detalhando.esporte} · {detalhando.bairro}</p>
            </div>

            <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Data</dt>
                <dd className="mt-0.5 text-sm text-gray-800">
                  {formatarData(detalhando.data_hora_inicio)}
                </dd>
              </div>
              <div>
                <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Horário</dt>
                <dd className="mt-0.5 text-sm text-gray-800">
                  {formatarHora(detalhando.data_hora_inicio)} às {formatarHora(detalhando.data_hora_fim)}
                </dd>
              </div>
              <div>
                <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Status</dt>
                <dd className="mt-1"><Badge>{detalhando.status}</Badge></dd>
              </div>
              <div>
                <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Solicitado em</dt>
                <dd className="mt-0.5 text-sm text-gray-800">
                  {formatarDataHora(detalhando.data_criacao)}
                </dd>
              </div>
              <div className="sm:col-span-2">
                <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Código do agendamento</dt>
                <dd className="mt-0.5 font-mono text-sm text-gray-800">#{detalhando.id}</dd>
              </div>
            </dl>

            {detalhando.status === 'Confirmado' && (
              <Alerta tipo="aviso">
                Um e-mail de lembrete é enviado automaticamente antes do horário.
              </Alerta>
            )}
            {detalhando.status === 'Renovado' && (
              <Alerta tipo="aviso">
                Este agendamento foi renovado; um novo registro foi criado com nova data/horário.
              </Alerta>
            )}
            {detalhando.status === 'Cancelado' && (
              <Alerta tipo="aviso">
                Este agendamento foi cancelado e o horário foi liberado.
              </Alerta>
            )}

            <div className="flex justify-end">
              <Botao variante="secundario" onClick={() => setDetalhando(null)}>
                Fechar
              </Botao>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
