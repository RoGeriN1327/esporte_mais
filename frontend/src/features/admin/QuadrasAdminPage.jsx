// Gerenciar quadras (RF004: listar, cadastrar, editar e desativar; filtros do Quadro 23,
// botões dos Quadros 32, 34 e 35 e campos do Quadro 33 do DERS).
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { TbBuildingStadium, TbMapPin, TbPlus } from 'react-icons/tb'

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
import { classesDeInput } from '../../components/estilos'
import { Alerta, Badge, Botao, Campo, Modal } from '../../components/ui'
import { useConsulta } from '../../hooks/useConsulta'
import { DIAS_SEMANA, horaCurta } from '../../utils/datas'

// Mesma lista de ESPORTES_VALIDOS em backend/app/schemas/quadra.py
const ESPORTES = ['Futebol', 'Futsal', 'Basquete', 'Vôlei', 'Tênis', 'Handebol']
const CHAVES = ['esporte', 'nome', 'bairro']

const GRADE_VAZIA = DIAS_SEMANA.map((_, dia) => ({ dia_semana: dia, ativo: false, hora_inicio: '08:00', hora_fim: '22:00' }))

function gradeInicial(faixas) {
  if (!faixas?.length) return GRADE_VAZIA
  return GRADE_VAZIA.map((linha) => {
    const faixa = faixas.find((registro) => registro.dia_semana === linha.dia_semana)
    return faixa ? { ...linha, ativo: true, hora_inicio: horaCurta(faixa.hora_inicio), hora_fim: horaCurta(faixa.hora_fim) } : linha
  })
}

const CLASSE_HORA =
  'h-10 w-[7.5rem] rounded-lg border border-cinza-300 bg-white px-2.5 text-sm tabular-nums text-cinza-900 transition-colors outline-none focus:border-marca-600 focus:ring-3 focus:ring-marca-600/15 disabled:bg-cinza-50 disabled:text-cinza-400'

function FormularioQuadra({ inicial, edicao, aoSalvar, aoCancelar, salvando, erro }) {
  const [nome, setNome] = useState(inicial?.nome ?? '')
  const [endereco, setEndereco] = useState(inicial?.endereco ?? '')
  const [bairro, setBairro] = useState(inicial?.bairro ?? '')
  const [descricao, setDescricao] = useState(inicial?.descricao ?? '')
  const [esportes, setEsportes] = useState(inicial?.esporte ? [inicial.esporte] : [])
  const [grade, setGrade] = useState(() => gradeInicial(inicial?.faixas))

  function alternarEsporte(esporte) {
    if (edicao) {
      setEsportes([esporte])
      return
    }
    setEsportes((atuais) => (atuais.includes(esporte) ? atuais.filter((item) => item !== esporte) : [...atuais, esporte]))
  }

  function atualizarGrade(dia, campo, valor) {
    setGrade((atual) => atual.map((linha) => (linha.dia_semana === dia ? { ...linha, [campo]: valor } : linha)))
  }

  function aoEnviar(evento) {
    evento.preventDefault()
    const faixas = grade
      .filter((linha) => linha.ativo)
      .map((linha) => ({ dia_semana: linha.dia_semana, hora_inicio: `${linha.hora_inicio}:00`, hora_fim: `${linha.hora_fim}:00` }))
    const base = { nome, endereco, bairro, descricao, faixas }
    aoSalvar(edicao ? { ...base, esporte: esportes[0] } : { ...base, esportes })
  }

  const gradeVazia = !grade.some((linha) => linha.ativo)

  return (
    <form className="space-y-6" onSubmit={aoEnviar} noValidate>
      <div className="grid gap-5 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <Campo label="Nome da quadra">
            <input className={classesDeInput(false)} autoComplete="off" maxLength={100} value={nome} onChange={(e) => setNome(e.target.value)} />
          </Campo>
        </div>
        <Campo label="Endereço completo">
          <input className={classesDeInput(false)} autoComplete="off" maxLength={255} value={endereco} onChange={(e) => setEndereco(e.target.value)} />
        </Campo>
        <Campo label="Bairro">
          <input className={classesDeInput(false)} autoComplete="off" maxLength={100} value={bairro} onChange={(e) => setBairro(e.target.value)} />
        </Campo>
      </div>

      <fieldset>
        <legend className="text-sm font-semibold text-cinza-800">{edicao ? 'Esporte' : 'Esportes'}</legend>
        <p className="mb-2.5 mt-0.5 text-xs text-cinza-500">
          {edicao ? 'Cada registro de quadra tem um único esporte.' : 'Selecione um ou mais. É criado um registro de quadra para cada esporte.'}
        </p>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
          {ESPORTES.map((esporte) => {
            const selecionado = esportes.includes(esporte)
            return (
              <button
                key={esporte}
                type="button"
                aria-pressed={selecionado}
                onClick={() => alternarEsporte(esporte)}
                className={`flex h-11 items-center gap-2 rounded-lg border px-3 text-sm font-bold transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marca-600 ${
                  selecionado ? 'border-marca-600 bg-marca-600 text-white' : 'border-cinza-300 bg-white text-cinza-800 hover:border-marca-400 hover:bg-marca-50'
                }`}
              >
                <IconeEsporte esporte={esporte} className="size-5 shrink-0" />
                {esporte}
              </button>
            )
          })}
        </div>
      </fieldset>

      <Campo label="Descrição" dica={`${descricao.length}/300 caracteres`}>
        <textarea
          className={classesDeInput(false, { multilinha: true })}
          rows={3}
          maxLength={300}
          value={descricao}
          onChange={(e) => setDescricao(e.target.value)}
        />
      </Campo>

      <fieldset>
        <legend className="text-sm font-semibold text-cinza-800">Horários disponíveis</legend>
        <p className="mb-2.5 mt-0.5 text-xs text-cinza-500">Marque os dias de funcionamento e defina o horário de cada um.</p>
        <div className="divide-y divide-cinza-100 rounded-xl border border-cinza-200">
          {grade.map((linha) => (
            <div key={linha.dia_semana} className="flex flex-wrap items-center gap-x-4 gap-y-2 px-3.5 py-2.5">
              <label className="flex min-w-36 flex-1 cursor-pointer items-center gap-2.5 text-sm font-semibold text-cinza-800">
                <input
                  type="checkbox"
                  checked={linha.ativo}
                  onChange={(e) => atualizarGrade(linha.dia_semana, 'ativo', e.target.checked)}
                  className="size-[18px] accent-marca-600"
                />
                {DIAS_SEMANA[linha.dia_semana]}
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="time"
                  aria-label={`${DIAS_SEMANA[linha.dia_semana]}: início`}
                  className={CLASSE_HORA}
                  disabled={!linha.ativo}
                  value={linha.hora_inicio}
                  onChange={(e) => atualizarGrade(linha.dia_semana, 'hora_inicio', e.target.value)}
                />
                <span className="text-sm text-cinza-400">até</span>
                <input
                  type="time"
                  aria-label={`${DIAS_SEMANA[linha.dia_semana]}: fim`}
                  className={CLASSE_HORA}
                  disabled={!linha.ativo}
                  value={linha.hora_fim}
                  onChange={(e) => atualizarGrade(linha.dia_semana, 'hora_fim', e.target.value)}
                />
              </div>
            </div>
          ))}
        </div>
      </fieldset>

      <Alerta tipo="erro">{erro}</Alerta>

      <BarraAcoes separada>
        <Botao type="button" variante="secundario" onClick={aoCancelar}>
          Cancelar
        </Botao>
        <Botao type="submit" carregando={salvando} disabled={esportes.length === 0 || gradeVazia}>
          {salvando ? 'Salvando…' : 'Salvar'}
        </Botao>
      </BarraAcoes>
    </form>
  )
}

function DetalhesQuadra({ quadra, onFechar, onEditar, onDesativar }) {
  const faixas = [...(quadra.faixas ?? [])].sort((a, b) => a.dia_semana - b.dia_semana)
  return (
    <div className="space-y-5">
      <div className="flex items-start gap-3.5">
        <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-marca-50 text-marca-700">
          <IconeEsporte esporte={quadra.esporte} className="size-6" />
        </span>
        <div className="min-w-0 flex-1">
          <p className="break-words text-lg font-extrabold text-cinza-900">{quadra.nome}</p>
          <p className="text-sm font-bold text-marca-700">{quadra.esporte}</p>
        </div>
        <Badge>{quadra.status}</Badge>
      </div>

      <ListaDetalhes
        linhas={[
          { rotulo: 'Endereço', valor: quadra.endereco },
          { rotulo: 'Bairro', valor: quadra.bairro },
          { rotulo: 'Código', valor: `#${quadra.id}`, classe: 'tabular-nums' },
        ]}
      />

      {quadra.descricao && <p className="text-sm text-cinza-600">{quadra.descricao}</p>}

      <div>
        <p className="mb-2 text-sm font-bold text-cinza-800">Horários disponíveis</p>
        <ul className="grid gap-1.5 sm:grid-cols-2">
          {faixas.map((faixa) => (
            <li key={faixa.dia_semana} className="flex justify-between gap-2 rounded-lg bg-cinza-50 px-3 py-2 text-sm">
              <span className="text-cinza-600">{DIAS_SEMANA[faixa.dia_semana]}</span>
              <span className="font-bold tabular-nums text-cinza-900">
                {horaCurta(faixa.hora_inicio)}–{horaCurta(faixa.hora_fim)}
              </span>
            </li>
          ))}
        </ul>
      </div>

      <BarraAcoes>
        <Botao variante="secundario" onClick={onFechar}>
          Fechar
        </Botao>
        {quadra.status === 'Ativa' && (
          <Botao variante="perigoContorno" onClick={onDesativar}>
            Desativar
          </Botao>
        )}
        <Botao onClick={onEditar}>Editar</Botao>
      </BarraAcoes>
    </div>
  )
}

export default function QuadrasAdminPage() {
  const queryClient = useQueryClient()
  const consulta = useConsulta(CHAVES)
  const [mensagem, setMensagem] = useState('')
  const [erroModal, setErroModal] = useState('')
  const [modal, setModal] = useState(null)

  const { data: quadras, isFetching, isError } = useQuery({
    queryKey: ['admin-quadras', consulta.parametrosApi],
    queryFn: () => adminApi.listarQuadrasAdmin(consulta.parametrosApi),
    enabled: consulta.consultado,
  })
  const { data: opcoes } = useQuery({
    queryKey: ['admin-quadras', {}],
    queryFn: () => adminApi.listarQuadrasAdmin(),
    select: (todas) => [...new Set(todas.map((quadra) => quadra.bairro))].sort(),
  })

  function abrir(config) {
    setErroModal('')
    setModal(config)
  }

  function aoTerminar(mensagemSucesso) {
    return {
      onSuccess: () => {
        setMensagem(mensagemSucesso)
        setModal(null)
        queryClient.invalidateQueries({ queryKey: ['admin-quadras'] })
      },
      onError: (excecao) => setErroModal(mensagemDeErro(excecao)),
    }
  }

  const cadastrar = useMutation({ mutationFn: adminApi.cadastrarQuadra, ...aoTerminar('Quadra cadastrada com sucesso.') })
  const editar = useMutation({ mutationFn: ({ id, payload }) => adminApi.editarQuadra(id, payload), ...aoTerminar('Quadra atualizada com sucesso.') })
  const desativar = useMutation({ mutationFn: (id) => adminApi.desativarQuadra(id), ...aoTerminar('Quadra desativada. Novos agendamentos estão impedidos.') })

  return (
    <div>
      <CabecalhoPagina
        voltarPara="/admin"
        voltarTexto="Início"
        titulo="Gerenciar quadras"
        descricao="Consulte as quadras cadastradas. Abra uma quadra para ver os detalhes, editar ou desativar."
        acoes={
          <Botao onClick={() => abrir({ modo: 'novo' })}>
            <TbPlus aria-hidden="true" className="size-[18px]" />
            Nova Quadra
          </Botao>
        }
      />

      <div className="space-y-8">
        <PainelFiltros
          key={`${consulta.versao}|${Boolean(opcoes)}`}
          onBuscar={(dados) => consulta.buscar(Object.fromEntries(dados))}
          botoes={<BotoesFiltro onLimpar={consulta.limpar} buscando={isFetching && consulta.consultado} />}
        >
          <Campo label="Esporte">
            <select name="esporte" defaultValue={consulta.filtros.esporte} className={classesDeInput(false)}>
              <option value="">Todos</option>
              {ESPORTES.map((esporte) => (
                <option key={esporte} value={esporte}>
                  {esporte}
                </option>
              ))}
            </select>
          </Campo>
          <Campo label="Nome da quadra">
            <input name="nome" defaultValue={consulta.filtros.nome} autoComplete="off" placeholder="Ex.: Ginásio Municipal…" className={classesDeInput(false)} />
          </Campo>
          <Campo label="Bairro">
            <select name="bairro" defaultValue={consulta.filtros.bairro} className={classesDeInput(false)}>
              <option value="">Todos</option>
              {(opcoes ?? []).map((bairro) => (
                <option key={bairro} value={bairro}>
                  {bairro}
                </option>
              ))}
            </select>
          </Campo>
        </PainelFiltros>

        <Alerta tipo="sucesso">{mensagem}</Alerta>

        <ResultadoConsulta
          consultado={consulta.consultado}
          carregando={isFetching && !quadras}
          erro={isError && 'Não foi possível buscar as quadras. Tente novamente em instantes.'}
          vazio={!quadras?.length}
          inicial={{
            Icone: TbBuildingStadium,
            titulo: 'Consulte as quadras cadastradas',
            descricao: 'Use os filtros e clique em “Buscar”. Para listar todas as quadras, clique em “Buscar” sem preencher nada.',
          }}
          textoCarregando="Buscando quadras…"
          tituloVazio="Nenhuma quadra encontrada"
          descricaoVazio="Não há quadras com esses filtros. Altere a busca ou use “Limpar filtros” para ver todas."
        >
          <ListaClicavel titulo="Quadras" total={quadras?.length} rotuloSingular="quadra" rotuloPlural="quadras">
            {quadras?.map((quadra) => (
              <ItemClicavel key={quadra.id} onClick={() => abrir({ modo: 'detalhes', quadra })}>
                <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-marca-50 text-marca-700">
                  <IconeEsporte esporte={quadra.esporte} className="size-6" />
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate font-extrabold text-cinza-900">{quadra.nome}</span>
                  <span className="mt-0.5 flex flex-wrap items-center gap-x-3 text-sm text-cinza-600">
                    <span className="font-semibold text-marca-700">{quadra.esporte}</span>
                    <span className="inline-flex min-w-0 items-center gap-1">
                      <TbMapPin aria-hidden="true" className="size-4 shrink-0 text-cinza-400" />
                      <span className="truncate">{quadra.bairro}</span>
                    </span>
                  </span>
                </span>
                <Badge>{quadra.status}</Badge>
              </ItemClicavel>
            ))}
          </ListaClicavel>
        </ResultadoConsulta>
      </div>

      <Modal aberto={modal?.modo === 'detalhes'} titulo="Detalhes da quadra" onFechar={() => setModal(null)}>
        {modal?.modo === 'detalhes' && (
          <DetalhesQuadra
            quadra={modal.quadra}
            onFechar={() => setModal(null)}
            onEditar={() => abrir({ modo: 'editar', quadra: modal.quadra })}
            onDesativar={() => abrir({ modo: 'desativar', quadra: modal.quadra })}
          />
        )}
      </Modal>

      <Modal
        aberto={modal?.modo === 'novo' || modal?.modo === 'editar'}
        titulo={modal?.modo === 'novo' ? 'Nova quadra' : 'Editar quadra'}
        onFechar={() => setModal(null)}
        largo
      >
        {(modal?.modo === 'novo' || modal?.modo === 'editar') && (
          <FormularioQuadra
            inicial={modal.quadra}
            edicao={modal.modo === 'editar'}
            salvando={cadastrar.isPending || editar.isPending}
            erro={erroModal}
            aoCancelar={() => setModal(null)}
            aoSalvar={(payload) => (modal.modo === 'novo' ? cadastrar.mutate(payload) : editar.mutate({ id: modal.quadra.id, payload }))}
          />
        )}
      </Modal>

      {/* Quadro 35 — confirmação de desativação */}
      <Modal aberto={modal?.modo === 'desativar'} titulo="Desativar quadra" onFechar={() => setModal(null)}>
        {modal?.modo === 'desativar' && (
          <div className="space-y-5">
            <p className="text-[15px] text-cinza-700">
              Desativar <strong className="text-cinza-900">{modal.quadra.nome}</strong> ({modal.quadra.esporte})? Novos agendamentos
              serão impedidos; os agendamentos existentes não são afetados.
            </p>
            <Alerta tipo="erro">{erroModal}</Alerta>
            <BarraAcoes>
              <Botao variante="secundario" onClick={() => setModal(null)}>
                Cancelar
              </Botao>
              <Botao variante="perigo" onClick={() => desativar.mutate(modal.quadra.id)} carregando={desativar.isPending}>
                Confirmar
              </Botao>
            </BarraAcoes>
          </div>
        )}
      </Modal>
    </div>
  )
}
