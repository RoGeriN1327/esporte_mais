// Meus agendamentos (RF003: A1 visualizar, A2 renovar, A3 cancelar; Quadros 27 a 31 do DERS).
// A lista mostra só o essencial; ao clicar num agendamento abrem-se os detalhes com a ação
// disponível para o status (Cancelar se "Confirmado", Renovar se "Concluído").
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { TbCalendarSearch, TbChevronRight, TbClock, TbMapPin, TbSearch, TbSearchOff } from 'react-icons/tb'
import { useLocation } from 'react-router-dom'

import * as agendamentosApi from '../../api/agendamentos.api'
import { mensagemDeErro } from '../../api/client'
import IconeEsporte from '../../components/IconeEsporte'
import { CabecalhoPagina, EstadoVazio, PainelFiltros } from '../../components/Pagina'
import SeletorDataHorario from '../../components/SeletorDataHorario'
import { classesDeInput } from '../../components/estilos'
import { Alerta, Badge, Botao, Campo, Carregando, Modal } from '../../components/ui'
import { useConsultaNaUrl } from '../../hooks/useConsultaNaUrl'
import { dataExtensa, formatarDataHora, formatarHora, partesDaData } from '../../utils/datas'

const CHAVES = ['data', 'nome_quadra', 'esporte', 'status']
const STATUS = ['Confirmado', 'Cancelado', 'Concluído', 'Renovado']

function LinhaAgendamento({ agendamento, onAbrir }) {
  const { dia, mes } = partesDaData(agendamento.data_hora_inicio)
  return (
    <li>
      <button
        type="button"
        onClick={() => onAbrir(agendamento)}
        className="flex w-full items-center gap-4 px-4 py-4 text-left transition-colors hover:bg-cinza-50 focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-marca-600 sm:px-5"
      >
        <span className="flex w-12 shrink-0 flex-col items-center rounded-lg border border-cinza-200 py-1.5">
          <span className="text-lg font-black leading-none tabular-nums text-cinza-900">{dia}</span>
          <span className="mt-0.5 text-[11px] font-bold uppercase text-cinza-500">{mes}</span>
        </span>

        <span className="min-w-0 flex-1">
          <span className="block truncate font-extrabold text-cinza-900">{agendamento.nome_quadra}</span>
          <span className="mt-0.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-cinza-600">
            <span className="inline-flex items-center gap-1 font-semibold tabular-nums text-cinza-800">
              <TbClock aria-hidden="true" className="size-4 text-cinza-400" />
              {formatarHora(agendamento.data_hora_inicio)}–{formatarHora(agendamento.data_hora_fim)}
            </span>
            <span className="inline-flex items-center gap-1">
              <IconeEsporte esporte={agendamento.esporte} className="size-4 text-cinza-400" />
              {agendamento.esporte}
            </span>
          </span>
        </span>

        <Badge>{agendamento.status}</Badge>
        <TbChevronRight aria-hidden="true" className="hidden size-5 shrink-0 text-cinza-400 sm:block" />
      </button>
    </li>
  )
}

function Detalhes({ agendamento, onFechar, onCancelar, onRenovar }) {
  const linhas = [
    { rotulo: 'Data', valor: dataExtensa(agendamento.data_hora_inicio), classe: 'first-letter:uppercase' },
    {
      rotulo: 'Horário',
      valor: `${formatarHora(agendamento.data_hora_inicio)} às ${formatarHora(agendamento.data_hora_fim)}`,
      classe: 'tabular-nums',
    },
    { rotulo: 'Esporte', valor: agendamento.esporte },
    { rotulo: 'Bairro', valor: agendamento.bairro },
    { rotulo: 'Solicitado em', valor: formatarDataHora(agendamento.data_criacao), classe: 'tabular-nums' },
    { rotulo: 'Código', valor: `#${agendamento.id}`, classe: 'tabular-nums' },
  ]
  const avisos = {
    Confirmado: 'Você receberá um e-mail de lembrete antes do horário.',
    Renovado: 'Este agendamento foi renovado: um novo agendamento foi criado com a nova data e horário.',
    Cancelado: 'Este agendamento foi cancelado e o horário foi liberado.',
  }

  return (
    <div className="space-y-5">
      <div className="flex items-start gap-3.5">
        <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-marca-50 text-marca-700">
          <IconeEsporte esporte={agendamento.esporte} className="size-6" />
        </span>
        <div className="min-w-0 flex-1">
          <p className="break-words text-lg font-extrabold text-cinza-900">{agendamento.nome_quadra}</p>
          <p className="mt-0.5 flex items-center gap-1 text-sm text-cinza-600">
            <TbMapPin aria-hidden="true" className="size-4 text-cinza-400" />
            {agendamento.bairro}
          </p>
        </div>
        <Badge>{agendamento.status}</Badge>
      </div>

      <dl className="divide-y divide-cinza-100 rounded-xl border border-cinza-200">
        {linhas.map(({ rotulo, valor, classe = '' }) => (
          <div key={rotulo} className="flex items-center justify-between gap-4 px-4 py-2.5 text-sm">
            <dt className="shrink-0 text-cinza-500">{rotulo}</dt>
            <dd className={`min-w-0 break-words text-right font-bold text-cinza-900 ${classe}`}>{valor}</dd>
          </div>
        ))}
      </dl>

      {avisos[agendamento.status] && <Alerta tipo="info">{avisos[agendamento.status]}</Alerta>}

      <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
        <Botao variante="secundario" onClick={onFechar}>
          Fechar
        </Botao>
        {agendamento.status === 'Confirmado' && (
          <Botao variante="perigo" onClick={onCancelar}>
            Cancelar agendamento
          </Botao>
        )}
        {agendamento.status === 'Concluído' && <Botao onClick={onRenovar}>Renovar</Botao>}
      </div>
    </div>
  )
}

export default function MeusAgendamentosPage() {
  const location = useLocation()
  const queryClient = useQueryClient()
  const consulta = useConsultaNaUrl(CHAVES)
  const [mensagem, setMensagem] = useState(location.state?.mensagem ?? '')
  const [erro, setErro] = useState('')
  const [detalhando, setDetalhando] = useState(null)
  const [cancelando, setCancelando] = useState(null)
  const [renovando, setRenovando] = useState(null)
  const [dataRenovacao, setDataRenovacao] = useState('')
  const [horaRenovacao, setHoraRenovacao] = useState('')

  const { data: agendamentos, isFetching, isError } = useQuery({
    queryKey: ['meus-agendamentos', consulta.parametrosApi],
    queryFn: () => agendamentosApi.meusAgendamentos(consulta.parametrosApi),
    enabled: consulta.consultado,
  })
  // Opções do filtro "Esporte": modalidades dos agendamentos do usuário (Quadro 27)
  const { data: esportesDoUsuario } = useQuery({
    queryKey: ['meus-agendamentos', {}],
    queryFn: () => agendamentosApi.meusAgendamentos(),
    select: (todos) => [...new Set(todos.map((registro) => registro.esporte))].sort(),
  })

  function aoTerminar(mensagemSucesso) {
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
    ...aoTerminar('Agendamento cancelado. O horário foi liberado e você receberá um e-mail de confirmação.'),
  })

  const renovar = useMutation({
    mutationFn: () => agendamentosApi.renovarAgendamento(renovando.id, { data: dataRenovacao, horaInicio: horaRenovacao }),
    ...aoTerminar('Renovação confirmada! Um novo agendamento foi criado e você receberá um e-mail com os dados.'),
  })

  function abrirCancelamento() {
    setCancelando(detalhando)
    setDetalhando(null)
  }

  function abrirRenovacao() {
    setRenovando(detalhando)
    setDetalhando(null)
    setDataRenovacao('')
    setHoraRenovacao('')
  }

  let resultado
  if (!consulta.consultado) {
    resultado = (
      <EstadoVazio
        tom="marca"
        Icone={TbCalendarSearch}
        titulo="Consulte seus agendamentos"
        descricao="Use os filtros acima e clique em “Buscar”. Para ver todos os seus agendamentos, clique em “Buscar” sem preencher nada."
      />
    )
  } else if (isFetching && !agendamentos) {
    resultado = <Carregando texto="Buscando agendamentos…" />
  } else if (isError) {
    resultado = <Alerta tipo="erro">Não foi possível buscar seus agendamentos. Tente novamente em instantes.</Alerta>
  } else if (!agendamentos?.length) {
    resultado = (
      <EstadoVazio
        Icone={TbSearchOff}
        titulo="Nenhum agendamento encontrado"
        descricao="Não há agendamentos com esses filtros. Altere a busca ou use “Limpar filtros” para ver todos."
      />
    )
  } else {
    resultado = (
      <section aria-labelledby="titulo-lista">
        <h2 id="titulo-lista" className="mb-4 text-sm font-bold text-cinza-600">
          {agendamentos.length} {agendamentos.length === 1 ? 'agendamento' : 'agendamentos'}
        </h2>
        <ul className="divide-y divide-cinza-100 overflow-hidden rounded-2xl border border-cinza-200 bg-white">
          {agendamentos.map((agendamento) => (
            <LinhaAgendamento key={agendamento.id} agendamento={agendamento} onAbrir={setDetalhando} />
          ))}
        </ul>
      </section>
    )
  }

  return (
    <div>
      <CabecalhoPagina
        voltarPara="/"
        voltarTexto="Início"
        titulo="Meus agendamentos"
        descricao="Consulte seus agendamentos. Abra um agendamento para ver os detalhes, cancelar ou renovar."
      />

      <div className="space-y-8">
        <PainelFiltros
          key={`${consulta.busca}|${Boolean(esportesDoUsuario)}`}
          colunas="lg:grid-cols-4"
          onBuscar={(dados) => consulta.buscar(Object.fromEntries(dados))}
          botoes={
            <>
              <Botao type="button" variante="secundario" onClick={consulta.limpar}>
                Limpar filtros
              </Botao>
              <Botao type="submit" carregando={isFetching && consulta.consultado}>
                <TbSearch aria-hidden="true" className="size-[18px]" />
                Buscar
              </Botao>
            </>
          }
        >
          <Campo label="Data">
            <input type="date" name="data" defaultValue={consulta.filtros.data} className={classesDeInput(false)} />
          </Campo>
          <Campo label="Nome da quadra">
            <input
              name="nome_quadra"
              defaultValue={consulta.filtros.nome_quadra}
              autoComplete="off"
              placeholder="Ex.: Quadra Central…"
              className={classesDeInput(false)}
            />
          </Campo>
          <Campo label="Esporte">
            <select name="esporte" defaultValue={consulta.filtros.esporte} className={classesDeInput(false)}>
              <option value="">Todos</option>
              {(esportesDoUsuario ?? []).map((esporte) => (
                <option key={esporte} value={esporte}>
                  {esporte}
                </option>
              ))}
            </select>
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
        </PainelFiltros>

        <Alerta tipo="sucesso">{mensagem}</Alerta>
        <Alerta tipo="erro">{erro}</Alerta>

        {resultado}
      </div>

      <Modal aberto={Boolean(detalhando)} titulo="Detalhes do agendamento" onFechar={() => setDetalhando(null)}>
        {detalhando && (
          <Detalhes
            agendamento={detalhando}
            onFechar={() => setDetalhando(null)}
            onCancelar={abrirCancelamento}
            onRenovar={abrirRenovacao}
          />
        )}
      </Modal>

      {/* Quadro 31 — cancelamento */}
      <Modal aberto={Boolean(cancelando)} titulo="Cancelar agendamento" onFechar={() => setCancelando(null)}>
        {cancelando && (
          <div className="space-y-5">
            <p className="text-[15px] text-cinza-700">
              Confirma o cancelamento do agendamento em <strong className="text-cinza-900">{cancelando.nome_quadra}</strong>{' '}
              no dia <strong className="text-cinza-900">{dataExtensa(cancelando.data_hora_inicio)}</strong>, às{' '}
              <strong className="tabular-nums text-cinza-900">{formatarHora(cancelando.data_hora_inicio)}</strong>? O horário
              será liberado para outras pessoas.
            </p>
            <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
              <Botao variante="secundario" onClick={() => setCancelando(null)}>
                Voltar
              </Botao>
              <Botao variante="perigo" onClick={() => cancelar.mutate(cancelando.id)} carregando={cancelar.isPending}>
                Confirmar cancelamento
              </Botao>
            </div>
          </div>
        )}
      </Modal>

      {/* Quadros 29 e 30 — renovação */}
      <Modal aberto={Boolean(renovando)} titulo="Renovar agendamento" onFechar={() => setRenovando(null)}>
        {renovando && (
          <div className="space-y-5">
            <Campo label="Nome da quadra">
              <input className={classesDeInput(false)} value={`${renovando.nome_quadra} — ${renovando.esporte}`} disabled readOnly />
            </Campo>
            <SeletorDataHorario
              quadraId={renovando.id_quadra}
              data={dataRenovacao}
              hora={horaRenovacao}
              onMudarData={setDataRenovacao}
              onMudarHora={setHoraRenovacao}
            />
            <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
              <Botao variante="secundario" onClick={() => setRenovando(null)}>
                Fechar
              </Botao>
              <Botao onClick={() => renovar.mutate()} carregando={renovar.isPending} disabled={!dataRenovacao || !horaRenovacao}>
                Confirmar renovação
              </Botao>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
