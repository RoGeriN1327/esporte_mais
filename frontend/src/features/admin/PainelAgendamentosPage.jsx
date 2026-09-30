import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

import * as adminApi from '../../api/admin.api'
import { mensagemDeErro } from '../../api/client'
import SeletorDataHorario from '../../components/SeletorDataHorario'
import { classesDeInput } from '../../components/estilos'
import { Alerta, Badge, Botao, Campo, Carregando, Modal } from '../../components/ui'
import { cpfValido, mascararCpf, somenteDigitos } from '../../utils/cpf'
import { formatarData, formatarHora } from '../../utils/datas'

const FILTROS_VAZIOS = { data: '', nome_quadra: '', status: '', cpf_usuario: '', nome_usuario: '' }
const STATUS = ['Confirmado', 'Cancelado', 'Concluído', 'Renovado']

export default function PainelAgendamentosPage() {
  const queryClient = useQueryClient()
  const [formulario, setFormulario] = useState(FILTROS_VAZIOS)
  const [filtros, setFiltros] = useState(FILTROS_VAZIOS)
  const [mensagem, setMensagem] = useState('')
  const [erroModal, setErroModal] = useState('')
  const [modal, setModal] = useState(null)
  const [cpfNovo, setCpfNovo] = useState('')
  const [quadraNova, setQuadraNova] = useState('')
  const [dataSelecionada, setDataSelecionada] = useState('')
  const [horaSelecionada, setHoraSelecionada] = useState('')

  const { data: agendamentos, isLoading } = useQuery({
    queryKey: ['admin-agendamentos', filtros],
    queryFn: () =>
      adminApi.painelAgendamentos({
        data: filtros.data || undefined,
        nome_quadra: filtros.nome_quadra || undefined,
        status: filtros.status || undefined,
        cpf_usuario: somenteDigitos(filtros.cpf_usuario) || undefined,
        nome_usuario: filtros.nome_usuario || undefined,
      }),
  })
  const { data: quadras } = useQuery({
    queryKey: ['admin-quadras'],
    queryFn: () => adminApi.listarQuadrasAdmin(),
  })
  const quadrasAtivas = (quadras || []).filter((quadra) => quadra.status === 'Ativa')

  function abrirModal(config) {
    setErroModal('')
    setDataSelecionada('')
    setHoraSelecionada('')
    setCpfNovo('')
    setQuadraNova('')
    setModal(config)
  }

  function aoMutacaoConcluida(mensagemSucesso) {
    return {
      onSuccess: () => {
        setMensagem(mensagemSucesso)
        setErroModal('')
        setModal(null)
        queryClient.invalidateQueries({ queryKey: ['admin-agendamentos'] })
      },
      onError: (excecao) => setErroModal(mensagemDeErro(excecao)),
    }
  }

  const criar = useMutation({
    mutationFn: () =>
      adminApi.criarAgendamentoAdmin({
        cpfUsuario: cpfNovo,
        idQuadra: Number(quadraNova),
        data: dataSelecionada,
        horaInicio: horaSelecionada,
      }),
    ...aoMutacaoConcluida('Agendamento criado. O cidadão foi notificado por e-mail.'),
  })

  const remarcar = useMutation({
    mutationFn: () =>
      adminApi.remarcarAgendamento(modal.agendamento.id, {
        data: dataSelecionada,
        horaInicio: horaSelecionada,
      }),
    ...aoMutacaoConcluida('Agendamento remarcado. O cidadão foi notificado por e-mail.'),
  })

  const cancelar = useMutation({
    mutationFn: () => adminApi.cancelarAgendamentoAdmin(modal.agendamento.id),
    ...aoMutacaoConcluida('Agendamento cancelado. O cidadão foi notificado por e-mail.'),
  })

  function atualizarCampo(campo, valor) {
    setFormulario((atual) => ({ ...atual, [campo]: valor }))
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold text-gray-800">Painel de agendamentos</h1>
        <Botao onClick={() => abrirModal({ modo: 'novo' })}>Novo agendamento</Botao>
      </div>

      {/* Filtros */}
      <form
        className="grid gap-4 rounded-xl bg-white p-4 shadow sm:grid-cols-2 lg:grid-cols-6"
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
        <Campo label="Quadra">
          <input
            className={classesDeInput(false)}
            value={formulario.nome_quadra}
            onChange={(evento) => atualizarCampo('nome_quadra', evento.target.value)}
          />
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
        <Campo label="CPF do cidadão">
          <input
            className={classesDeInput(false)}
            inputMode="numeric"
            value={formulario.cpf_usuario}
            onChange={(evento) => atualizarCampo('cpf_usuario', mascararCpf(evento.target.value))}
          />
        </Campo>
        <Campo label="Nome do cidadão">
          <input
            className={classesDeInput(false)}
            value={formulario.nome_usuario}
            onChange={(evento) => atualizarCampo('nome_usuario', evento.target.value)}
          />
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
            Limpar
          </Botao>
        </div>
      </form>

      <Alerta tipo="sucesso">{mensagem}</Alerta>

      {isLoading ? (
        <Carregando />
      ) : (
        <div className="overflow-x-auto rounded-xl bg-white shadow">
          <table className="w-full text-left text-sm">
            <thead className="border-b bg-gray-50 text-xs uppercase text-gray-500">
              <tr>
                <th className="px-4 py-3">Cidadão</th>
                <th className="px-4 py-3">Quadra</th>
                <th className="px-4 py-3">Data / horário</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3 text-right">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {(agendamentos || []).map((agendamento) => (
                <tr key={agendamento.id}>
                  <td className="px-4 py-3">
                    <p className="font-medium text-gray-800">{agendamento.nome_usuario}</p>
                    <p className="text-xs text-gray-500">{mascararCpf(agendamento.cpf_usuario)}</p>
                  </td>
                  <td className="px-4 py-3">
                    {agendamento.nome_quadra}{' '}
                    <span className="text-gray-500">({agendamento.esporte})</span>
                  </td>
                  <td className="px-4 py-3">
                    {formatarData(agendamento.data_hora_inicio)} ·{' '}
                    {formatarHora(agendamento.data_hora_inicio)}–{formatarHora(agendamento.data_hora_fim)}
                  </td>
                  <td className="px-4 py-3"><Badge>{agendamento.status}</Badge></td>
                  <td className="px-4 py-3">
                    {agendamento.status === 'Confirmado' && (
                      <div className="flex justify-end gap-2">
                        <Botao
                          variante="secundario"
                          onClick={() => abrirModal({ modo: 'remarcar', agendamento })}
                        >
                          Remarcar
                        </Botao>
                        <Botao
                          variante="perigo"
                          onClick={() => abrirModal({ modo: 'cancelar', agendamento })}
                        >
                          Cancelar
                        </Botao>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {(agendamentos || []).length === 0 && (
            <p className="py-8 text-center text-gray-500">Nenhum agendamento encontrado.</p>
          )}
        </div>
      )}

      {/* Modal: Novo agendamento */}
      <Modal aberto={modal?.modo === 'novo'} titulo="Novo agendamento" onFechar={() => setModal(null)}>
        <div className="space-y-4">
          <Campo label="CPF do cidadão">
            <input
              className={classesDeInput(Boolean(cpfNovo) && !cpfValido(cpfNovo))}
              inputMode="numeric"
              placeholder="000.000.000-00"
              value={cpfNovo}
              onChange={(evento) => setCpfNovo(mascararCpf(evento.target.value))}
            />
          </Campo>
          <Campo label="Quadra">
            <select
              className={classesDeInput(false)}
              value={quadraNova}
              onChange={(evento) => {
                setQuadraNova(evento.target.value)
                setDataSelecionada('')
                setHoraSelecionada('')
              }}
            >
              <option value="">Selecione...</option>
              {quadrasAtivas.map((quadra) => (
                <option key={quadra.id} value={quadra.id}>
                  {quadra.nome} — {quadra.esporte} ({quadra.bairro})
                </option>
              ))}
            </select>
          </Campo>
          {quadraNova && (
            <SeletorDataHorario
              quadraId={Number(quadraNova)}
              data={dataSelecionada}
              hora={horaSelecionada}
              onMudarData={setDataSelecionada}
              onMudarHora={setHoraSelecionada}
            />
          )}
          <Alerta tipo="erro">{erroModal}</Alerta>
          <div className="flex justify-end gap-3">
            <Botao variante="secundario" onClick={() => setModal(null)}>
              Cancelar
            </Botao>
            <Botao
              onClick={() => criar.mutate()}
              carregando={criar.isPending}
              disabled={!cpfValido(cpfNovo) || !quadraNova || !dataSelecionada || !horaSelecionada}
            >
              Confirmar agendamento
            </Botao>
          </div>
        </div>
      </Modal>

      {/* Modal: Remarcar agendamento */}
      <Modal aberto={modal?.modo === 'remarcar'} titulo="Remarcar agendamento" onFechar={() => setModal(null)}>
        {modal?.agendamento && (
          <div className="space-y-4">
            <p className="text-sm text-gray-600">
              <strong>{modal.agendamento.nome_usuario}</strong> ·{' '}
              {modal.agendamento.nome_quadra} ({modal.agendamento.esporte}) · atualmente em{' '}
              {formatarData(modal.agendamento.data_hora_inicio)} às{' '}
              {formatarHora(modal.agendamento.data_hora_inicio)}
            </p>
            <SeletorDataHorario
              quadraId={modal.agendamento.id_quadra}
              data={dataSelecionada}
              hora={horaSelecionada}
              onMudarData={setDataSelecionada}
              onMudarHora={setHoraSelecionada}
            />
            <Alerta tipo="erro">{erroModal}</Alerta>
            <div className="flex justify-end gap-3">
              <Botao variante="secundario" onClick={() => setModal(null)}>
                Cancelar
              </Botao>
              <Botao
                onClick={() => remarcar.mutate()}
                carregando={remarcar.isPending}
                disabled={!dataSelecionada || !horaSelecionada}
              >
                Confirmar remarcação
              </Botao>
            </div>
          </div>
        )}
      </Modal>

      {/* Modal: Cancelar agendamento */}
      <Modal aberto={modal?.modo === 'cancelar'} titulo="Cancelar agendamento" onFechar={() => setModal(null)}>
        {modal?.agendamento && (
          <div className="space-y-4">
            <p className="text-sm text-gray-600">
              Cancelar o agendamento de <strong>{modal.agendamento.nome_usuario}</strong> em{' '}
              <strong>{modal.agendamento.nome_quadra}</strong> no dia{' '}
              {formatarData(modal.agendamento.data_hora_inicio)} às{' '}
              {formatarHora(modal.agendamento.data_hora_inicio)}? O cidadão será notificado por
              e-mail.
            </p>
            <Alerta tipo="erro">{erroModal}</Alerta>
            <div className="flex justify-end gap-3">
              <Botao variante="secundario" onClick={() => setModal(null)}>
                Voltar
              </Botao>
              <Botao variante="perigo" onClick={() => cancelar.mutate()} carregando={cancelar.isPending}>
                Confirmar cancelamento
              </Botao>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
