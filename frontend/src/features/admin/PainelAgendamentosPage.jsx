// Gerenciar agendamentos (RF004: painel administrativo com visão consolidada de todos os
// agendamentos, com opções de edição — remarcação — e cancelamento; e agendamento em nome do cidadão).
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { TbCalendarSearch, TbClock, TbPlus } from 'react-icons/tb'

import * as adminApi from '../../api/admin.api'
import { mensagemDeErro } from '../../api/client'
import IconeEsporte from '../../components/IconeEsporte'
import {
  BarraAcoes,
  BotoesFiltro,
  CabecalhoPagina,
  ItemClicavel,
  ListaClicavel,
  ListaDetalhes,
  PainelFiltros,
  ResultadoConsulta,
} from '../../components/Pagina'
import SeletorDataHorario from '../../components/SeletorDataHorario'
import { classesDeInput } from '../../components/estilos'
import { Alerta, Badge, Botao, Campo, Modal } from '../../components/ui'
import { useConsulta } from '../../hooks/useConsulta'
import { cpfValido, mascararCpf, somenteDigitos } from '../../utils/cpf'
import { dataExtensa, formatarDataHora, formatarHora, partesDaData } from '../../utils/datas'

const CHAVES = ['data', 'nome_quadra', 'status', 'cpf_usuario', 'nome_usuario']
const STATUS = ['Confirmado', 'Cancelado', 'Concluído', 'Renovado']

function ResumoAgendamento({ agendamento }) {
  return (
    <p className="rounded-lg bg-cinza-50 px-3.5 py-3 text-sm text-cinza-700">
      <strong className="text-cinza-900">{agendamento.nome_usuario}</strong> · {agendamento.nome_quadra} ({agendamento.esporte}) ·{' '}
      {dataExtensa(agendamento.data_hora_inicio)}, às <span className="tabular-nums">{formatarHora(agendamento.data_hora_inicio)}</span>
    </p>
  )
}

export default function PainelAgendamentosPage() {
  const queryClient = useQueryClient()
  const consulta = useConsulta(CHAVES)
  const [mensagem, setMensagem] = useState('')
  const [erroModal, setErroModal] = useState('')
  const [modal, setModal] = useState(null)
  const [cpfNovo, setCpfNovo] = useState('')
  const [quadraNova, setQuadraNova] = useState('')
  const [dataSelecionada, setDataSelecionada] = useState('')
  const [horaSelecionada, setHoraSelecionada] = useState('')

  const parametros = { ...consulta.parametrosApi }
  if (parametros.cpf_usuario) parametros.cpf_usuario = somenteDigitos(parametros.cpf_usuario)

  const { data: agendamentos, isFetching, isError } = useQuery({
    queryKey: ['admin-agendamentos', parametros],
    queryFn: () => adminApi.painelAgendamentos(parametros),
    enabled: consulta.consultado,
  })
  const { data: quadrasAtivas } = useQuery({
    queryKey: ['admin-quadras', {}],
    queryFn: () => adminApi.listarQuadrasAdmin(),
    select: (todas) => todas.filter((quadra) => quadra.status === 'Ativa'),
  })

  function abrir(config) {
    setErroModal('')
    setDataSelecionada('')
    setHoraSelecionada('')
    setCpfNovo('')
    setQuadraNova('')
    setModal(config)
  }

  function aoTerminar(mensagemSucesso) {
    return {
      onSuccess: () => {
        setMensagem(mensagemSucesso)
        setModal(null)
        queryClient.invalidateQueries({ queryKey: ['admin-agendamentos'] })
      },
      onError: (excecao) => setErroModal(mensagemDeErro(excecao)),
    }
  }

  const criar = useMutation({
    mutationFn: () =>
      adminApi.criarAgendamentoAdmin({ cpfUsuario: cpfNovo, idQuadra: Number(quadraNova), data: dataSelecionada, horaInicio: horaSelecionada }),
    ...aoTerminar('Agendamento criado. O cidadão foi notificado por e-mail.'),
  })
  const remarcar = useMutation({
    mutationFn: () => adminApi.remarcarAgendamento(modal.agendamento.id, { data: dataSelecionada, horaInicio: horaSelecionada }),
    ...aoTerminar('Agendamento remarcado. O cidadão foi notificado por e-mail.'),
  })
  const cancelar = useMutation({
    mutationFn: () => adminApi.cancelarAgendamentoAdmin(modal.agendamento.id),
    ...aoTerminar('Agendamento cancelado. O cidadão foi notificado por e-mail.'),
  })

  const detalhe = modal?.modo === 'detalhes' ? modal.agendamento : null

  return (
    <div>
      <CabecalhoPagina
        voltarPara="/admin"
        voltarTexto="Início"
        titulo="Gerenciar agendamentos"
        descricao="Consulte os agendamentos de todas as quadras. Abra um agendamento para ver os detalhes, remarcar ou cancelar."
        acoes={
          <Botao onClick={() => abrir({ modo: 'novo' })}>
            <TbPlus aria-hidden="true" className="size-[18px]" />
            Novo agendamento
          </Botao>
        }
      />

      <div className="space-y-8">
        <PainelFiltros
          key={consulta.versao}
          onBuscar={(dados) => consulta.buscar(Object.fromEntries(dados))}
          botoes={<BotoesFiltro onLimpar={consulta.limpar} buscando={isFetching && consulta.consultado} />}
        >
          <Campo label="Data">
            <input type="date" name="data" defaultValue={consulta.filtros.data} className={classesDeInput(false)} />
          </Campo>
          <Campo label="Quadra">
            <input name="nome_quadra" defaultValue={consulta.filtros.nome_quadra} autoComplete="off" placeholder="Nome da quadra…" className={classesDeInput(false)} />
          </Campo>
          <Campo label="Status">
            <select name="status" defaultValue={consulta.filtros.status} className={classesDeInput(false)}>
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
              name="cpf_usuario"
              defaultValue={consulta.filtros.cpf_usuario}
              inputMode="numeric"
              autoComplete="off"
              placeholder="000.000.000-00"
              onChange={(evento) => (evento.target.value = mascararCpf(evento.target.value))}
              className={`${classesDeInput(false)} tabular-nums`}
            />
          </Campo>
          <Campo label="Nome do cidadão">
            <input name="nome_usuario" defaultValue={consulta.filtros.nome_usuario} autoComplete="off" placeholder="Nome completo ou parte…" className={classesDeInput(false)} />
          </Campo>
        </PainelFiltros>

        <Alerta tipo="sucesso">{mensagem}</Alerta>

        <ResultadoConsulta
          consultado={consulta.consultado}
          carregando={isFetching && !agendamentos}
          erro={isError && 'Não foi possível buscar os agendamentos. Tente novamente em instantes.'}
          vazio={!agendamentos?.length}
          inicial={{
            Icone: TbCalendarSearch,
            titulo: 'Consulte os agendamentos',
            descricao: 'Filtre por data, quadra, status ou cidadão e clique em “Buscar”. Para listar todos, clique em “Buscar” sem preencher nada.',
          }}
          textoCarregando="Buscando agendamentos…"
          tituloVazio="Nenhum agendamento encontrado"
          descricaoVazio="Não há agendamentos com esses filtros. Altere a busca ou use “Limpar filtros” para ver todos."
        >
          <ListaClicavel titulo="Agendamentos" total={agendamentos?.length} rotuloSingular="agendamento" rotuloPlural="agendamentos">
            {agendamentos?.map((agendamento) => {
              const { dia, mes } = partesDaData(agendamento.data_hora_inicio)
              return (
                <ItemClicavel key={agendamento.id} onClick={() => abrir({ modo: 'detalhes', agendamento })}>
                  <span className="flex w-12 shrink-0 flex-col items-center rounded-lg border border-cinza-200 py-1.5">
                    <span className="text-lg font-black leading-none tabular-nums text-cinza-900">{dia}</span>
                    <span className="mt-0.5 text-[11px] font-bold uppercase text-cinza-500">{mes}</span>
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block truncate font-extrabold text-cinza-900">{agendamento.nome_usuario}</span>
                    <span className="mt-0.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-cinza-600">
                      <span className="inline-flex items-center gap-1 font-semibold tabular-nums text-cinza-800">
                        <TbClock aria-hidden="true" className="size-4 text-cinza-400" />
                        {formatarHora(agendamento.data_hora_inicio)}–{formatarHora(agendamento.data_hora_fim)}
                      </span>
                      <span className="inline-flex min-w-0 items-center gap-1">
                        <IconeEsporte esporte={agendamento.esporte} className="size-4 shrink-0 text-cinza-400" />
                        <span className="truncate">{agendamento.nome_quadra}</span>
                      </span>
                    </span>
                  </span>
                  <Badge>{agendamento.status}</Badge>
                </ItemClicavel>
              )
            })}
          </ListaClicavel>
        </ResultadoConsulta>
      </div>

      <Modal aberto={Boolean(detalhe)} titulo="Detalhes do agendamento" onFechar={() => setModal(null)}>
        {detalhe && (
          <div className="space-y-5">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="break-words text-lg font-extrabold text-cinza-900">{detalhe.nome_usuario}</p>
                <p className="text-sm tabular-nums text-cinza-600">CPF {mascararCpf(detalhe.cpf_usuario)}</p>
              </div>
              <Badge>{detalhe.status}</Badge>
            </div>
            <ListaDetalhes
              linhas={[
                { rotulo: 'Quadra', valor: detalhe.nome_quadra },
                { rotulo: 'Esporte', valor: detalhe.esporte },
                { rotulo: 'Bairro', valor: detalhe.bairro },
                { rotulo: 'Data', valor: dataExtensa(detalhe.data_hora_inicio), classe: 'first-letter:uppercase' },
                { rotulo: 'Horário', valor: `${formatarHora(detalhe.data_hora_inicio)} às ${formatarHora(detalhe.data_hora_fim)}`, classe: 'tabular-nums' },
                { rotulo: 'Solicitado em', valor: formatarDataHora(detalhe.data_criacao), classe: 'tabular-nums' },
                { rotulo: 'Origem', valor: detalhe.id_admin_responsavel ? 'Administração' : 'Cidadão' },
                { rotulo: 'Código', valor: `#${detalhe.id}`, classe: 'tabular-nums' },
              ]}
            />
            <BarraAcoes>
              <Botao variante="secundario" onClick={() => setModal(null)}>
                Fechar
              </Botao>
              {detalhe.status === 'Confirmado' && (
                <>
                  <Botao variante="perigoContorno" onClick={() => abrir({ modo: 'cancelar', agendamento: detalhe })}>
                    Cancelar agendamento
                  </Botao>
                  <Botao onClick={() => abrir({ modo: 'remarcar', agendamento: detalhe })}>Remarcar</Botao>
                </>
              )}
            </BarraAcoes>
          </div>
        )}
      </Modal>

      <Modal aberto={modal?.modo === 'novo'} titulo="Novo agendamento" onFechar={() => setModal(null)}>
        <div className="space-y-5">
          <Campo label="CPF do cidadão" erro={cpfNovo.length === 14 && !cpfValido(cpfNovo) ? 'CPF inválido. Confira os 11 dígitos.' : ''}>
            <input
              className={`${classesDeInput(cpfNovo.length === 14 && !cpfValido(cpfNovo))} tabular-nums`}
              inputMode="numeric"
              autoComplete="off"
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
              <option value="">Selecione…</option>
              {(quadrasAtivas ?? []).map((quadra) => (
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
          <BarraAcoes separada>
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
          </BarraAcoes>
        </div>
      </Modal>

      <Modal aberto={modal?.modo === 'remarcar'} titulo="Remarcar agendamento" onFechar={() => setModal(null)}>
        {modal?.modo === 'remarcar' && (
          <div className="space-y-5">
            <ResumoAgendamento agendamento={modal.agendamento} />
            <SeletorDataHorario
              quadraId={modal.agendamento.id_quadra}
              data={dataSelecionada}
              hora={horaSelecionada}
              onMudarData={setDataSelecionada}
              onMudarHora={setHoraSelecionada}
            />
            <Alerta tipo="erro">{erroModal}</Alerta>
            <BarraAcoes separada>
              <Botao variante="secundario" onClick={() => setModal(null)}>
                Cancelar
              </Botao>
              <Botao onClick={() => remarcar.mutate()} carregando={remarcar.isPending} disabled={!dataSelecionada || !horaSelecionada}>
                Confirmar remarcação
              </Botao>
            </BarraAcoes>
          </div>
        )}
      </Modal>

      <Modal aberto={modal?.modo === 'cancelar'} titulo="Cancelar agendamento" onFechar={() => setModal(null)}>
        {modal?.modo === 'cancelar' && (
          <div className="space-y-5">
            <ResumoAgendamento agendamento={modal.agendamento} />
            <p className="text-[15px] text-cinza-700">Confirma o cancelamento? O horário será liberado e o cidadão será notificado por e-mail.</p>
            <Alerta tipo="erro">{erroModal}</Alerta>
            <BarraAcoes>
              <Botao variante="secundario" onClick={() => setModal(null)}>
                Voltar
              </Botao>
              <Botao variante="perigo" onClick={() => cancelar.mutate()} carregando={cancelar.isPending}>
                Confirmar cancelamento
              </Botao>
            </BarraAcoes>
          </div>
        )}
      </Modal>
    </div>
  )
}
