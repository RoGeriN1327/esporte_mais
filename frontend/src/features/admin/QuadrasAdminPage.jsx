import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

import * as adminApi from '../../api/admin.api'
import { mensagemDeErro } from '../../api/client'
import { Alerta, Badge, Botao, Campo, Carregando, Modal, classesDeInput } from '../../components/ui'
import { DIAS_SEMANA, horaCurta } from '../../utils/datas'

const ESPORTES = ['Futebol', 'Futsal', 'Basquete', 'Vôlei', 'Tênis', 'Handebol']

const GRADE_VAZIA = DIAS_SEMANA.map((_, dia) => ({
  dia_semana: dia,
  ativo: false,
  hora_inicio: '08:00',
  hora_fim: '22:00',
}))

function FormularioQuadra({ inicial, edicao, aoSalvar, aoCancelar, salvando, erro }) {
  const [nome, setNome] = useState(inicial?.nome || '')
  const [endereco, setEndereco] = useState(inicial?.endereco || '')
  const [bairro, setBairro] = useState(inicial?.bairro || '')
  const [descricao, setDescricao] = useState(inicial?.descricao || '')
  const [esportes, setEsportes] = useState(inicial?.esporte ? [inicial.esporte] : [])
  const [grade, setGrade] = useState(() => {
    if (!inicial?.faixas?.length) return GRADE_VAZIA
    return GRADE_VAZIA.map((linha) => {
      const faixa = inicial.faixas.find((registro) => registro.dia_semana === linha.dia_semana)
      return faixa
        ? { ...linha, ativo: true, hora_inicio: horaCurta(faixa.hora_inicio), hora_fim: horaCurta(faixa.hora_fim) }
        : linha
    })
  })

  function alternarEsporte(esporte) {
    if (edicao) {
      setEsportes([esporte])
      return
    }
    setEsportes((atuais) =>
      atuais.includes(esporte) ? atuais.filter((item) => item !== esporte) : [...atuais, esporte],
    )
  }

  function atualizarGrade(dia, campo, valor) {
    setGrade((atual) =>
      atual.map((linha) => (linha.dia_semana === dia ? { ...linha, [campo]: valor } : linha)),
    )
  }

  function montarPayload() {
    const faixas = grade
      .filter((linha) => linha.ativo)
      .map((linha) => ({
        dia_semana: linha.dia_semana,
        hora_inicio: `${linha.hora_inicio}:00`,
        hora_fim: `${linha.hora_fim}:00`,
      }))
    const base = { nome, endereco, bairro, descricao, faixas }
    return edicao ? { ...base, esporte: esportes[0] } : { ...base, esportes }
  }

  const gradeVazia = !grade.some((linha) => linha.ativo)

  return (
    <div className="space-y-4">
      {}
      <Campo label="Nome da quadra">
        <input className={classesDeInput(false)} value={nome} onChange={(e) => setNome(e.target.value)} />
      </Campo>
      <Campo label="Endereço completo">
        <input className={classesDeInput(false)} value={endereco} onChange={(e) => setEndereco(e.target.value)} />
      </Campo>
      <Campo label="Bairro">
        <input className={classesDeInput(false)} value={bairro} onChange={(e) => setBairro(e.target.value)} />
      </Campo>
      <Campo label={edicao ? 'Esporte' : 'Esportes (um registro por esporte)'}>
        <div className="flex flex-wrap gap-2">
          {ESPORTES.map((esporte) => (
            <button
              key={esporte}
              type="button"
              className={`rounded-lg border px-3 py-1.5 text-sm font-medium transition ${
                esportes.includes(esporte)
                  ? 'border-emerald-600 bg-emerald-600 text-white'
                  : 'border-gray-300 bg-white text-gray-700 hover:border-emerald-500'
              }`}
              onClick={() => alternarEsporte(esporte)}
            >
              {esporte}
            </button>
          ))}
        </div>
      </Campo>
      <Campo label={`Descrição (${descricao.length}/300)`}>
        <textarea
          className={classesDeInput(false)}
          rows={3}
          maxLength={300}
          value={descricao}
          onChange={(e) => setDescricao(e.target.value)}
        />
      </Campo>

      {}
      <div>
        <span className="mb-2 block text-sm font-medium text-gray-700">
          Horários disponíveis (grade por dia da semana)
        </span>
        <div className="space-y-1.5">
          {grade.map((linha) => (
            <div key={linha.dia_semana} className="flex flex-wrap items-center gap-2 text-sm">
              <label className="flex w-36 items-center gap-2">
                <input
                  type="checkbox"
                  checked={linha.ativo}
                  onChange={(e) => atualizarGrade(linha.dia_semana, 'ativo', e.target.checked)}
                />
                {DIAS_SEMANA[linha.dia_semana]}
              </label>
              <input
                type="time"
                className="rounded border border-gray-300 px-2 py-1"
                disabled={!linha.ativo}
                value={linha.hora_inicio}
                onChange={(e) => atualizarGrade(linha.dia_semana, 'hora_inicio', e.target.value)}
              />
              <span className="text-gray-400">até</span>
              <input
                type="time"
                className="rounded border border-gray-300 px-2 py-1"
                disabled={!linha.ativo}
                value={linha.hora_fim}
                onChange={(e) => atualizarGrade(linha.dia_semana, 'hora_fim', e.target.value)}
              />
            </div>
          ))}
        </div>
      </div>

      <Alerta tipo="erro">{erro}</Alerta>

      {}
      <div className="flex justify-end gap-3">
        <Botao variante="secundario" onClick={aoCancelar}>
          Cancelar
        </Botao>
        <Botao
          onClick={() => aoSalvar(montarPayload())}
          carregando={salvando}
          disabled={esportes.length === 0 || gradeVazia}
        >
          Salvar
        </Botao>
      </div>
    </div>
  )
}

export default function QuadrasAdminPage() {
  const queryClient = useQueryClient()
  const [filtroNome, setFiltroNome] = useState('')
  const [mensagem, setMensagem] = useState('')
  const [erroModal, setErroModal] = useState('')
  const [modal, setModal] = useState(null)

  const { data: quadras, isLoading } = useQuery({
    queryKey: ['admin-quadras'],
    queryFn: () => adminApi.listarQuadrasAdmin(),
  })

  function aoMutacaoConcluida(mensagemSucesso) {
    return {
      onSuccess: () => {
        setMensagem(mensagemSucesso)
        setErroModal('')
        setModal(null)
        queryClient.invalidateQueries({ queryKey: ['admin-quadras'] })
      },
      onError: (excecao) => setErroModal(mensagemDeErro(excecao)),
    }
  }

  const cadastrar = useMutation({
    mutationFn: adminApi.cadastrarQuadra,
    ...aoMutacaoConcluida('Quadra cadastrada com sucesso.'),
  })
  const editar = useMutation({
    mutationFn: ({ id, payload }) => adminApi.editarQuadra(id, payload),
    ...aoMutacaoConcluida('Quadra atualizada com sucesso.'),
  })
  const desativar = useMutation({
    mutationFn: (id) => adminApi.desativarQuadra(id),
    ...aoMutacaoConcluida('Quadra desativada com sucesso.'),
  })

  const listaFiltrada = (quadras || []).filter((quadra) =>
    quadra.nome.toLowerCase().includes(filtroNome.toLowerCase()),
  )

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold text-gray-800">Gerenciar quadras</h1>
        {}
        <Botao onClick={() => { setErroModal(''); setModal({ modo: 'novo' }) }}>Nova Quadra</Botao>
      </div>

      <input
        className={`${classesDeInput(false)} max-w-sm`}
        placeholder="Filtrar por nome..."
        value={filtroNome}
        onChange={(evento) => setFiltroNome(evento.target.value)}
      />

      <Alerta tipo="sucesso">{mensagem}</Alerta>

      {isLoading ? (
        <Carregando />
      ) : (
        <div className="overflow-x-auto rounded-xl bg-white shadow">
          <table className="w-full text-left text-sm">
            <thead className="border-b bg-gray-50 text-xs uppercase text-gray-500">
              <tr>
                <th className="px-4 py-3">Quadra</th>
                <th className="px-4 py-3">Esporte</th>
                <th className="px-4 py-3">Bairro</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3 text-right">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {listaFiltrada.map((quadra) => (
                <tr key={quadra.id}>
                  <td className="px-4 py-3 font-medium text-gray-800">{quadra.nome}</td>
                  <td className="px-4 py-3">{quadra.esporte}</td>
                  <td className="px-4 py-3">{quadra.bairro}</td>
                  <td className="px-4 py-3"><Badge>{quadra.status}</Badge></td>
                  <td className="px-4 py-3">
                    {}
                    <div className="flex justify-end gap-2">
                      <Botao
                        variante="secundario"
                        onClick={() => { setErroModal(''); setModal({ modo: 'editar', quadra }) }}
                      >
                        Editar
                      </Botao>
                      {quadra.status === 'Ativa' && (
                        <Botao
                          variante="perigo"
                          onClick={() => { setErroModal(''); setModal({ modo: 'desativar', quadra }) }}
                        >
                          Desativar
                        </Botao>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {listaFiltrada.length === 0 && (
            <p className="py-8 text-center text-gray-500">Nenhuma quadra cadastrada.</p>
          )}
        </div>
      )}

      {}
      <Modal
        aberto={modal?.modo === 'novo' || modal?.modo === 'editar'}
        titulo={modal?.modo === 'novo' ? 'Nova quadra' : 'Editar quadra'}
        onFechar={() => setModal(null)}
      >
        {modal && modal.modo !== 'desativar' && (
          <FormularioQuadra
            inicial={modal.quadra}
            edicao={modal.modo === 'editar'}
            salvando={cadastrar.isPending || editar.isPending}
            erro={erroModal}
            aoCancelar={() => setModal(null)}
            aoSalvar={(payload) =>
              modal.modo === 'novo'
                ? cadastrar.mutate(payload)
                : editar.mutate({ id: modal.quadra.id, payload })
            }
          />
        )}
      </Modal>

      {}
      <Modal
        aberto={modal?.modo === 'desativar'}
        titulo="Desativar quadra"
        onFechar={() => setModal(null)}
      >
        {modal?.quadra && (
          <div className="space-y-4">
            <p className="text-sm text-gray-600">
              Desativar <strong>{modal.quadra.nome} ({modal.quadra.esporte})</strong>? Novos
              agendamentos serão impedidos; os agendamentos existentes não são afetados.
            </p>
            <Alerta tipo="erro">{erroModal}</Alerta>
            <div className="flex justify-end gap-3">
              <Botao variante="secundario" onClick={() => setModal(null)}>
                Cancelar
              </Botao>
              <Botao
                variante="perigo"
                onClick={() => desativar.mutate(modal.quadra.id)}
                carregando={desativar.isPending}
              >
                Confirmar
              </Botao>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
