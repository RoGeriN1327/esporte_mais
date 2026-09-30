import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import * as quadrasApi from '../../api/quadras.api'
import { classesDeInput } from '../../components/estilos'
import { Botao, Campo, Carregando } from '../../components/ui'

const FILTROS_VAZIOS = { esporte: '', nome: '', bairro: '' }

export default function QuadrasPage() {
  const navigate = useNavigate()
  const [formulario, setFormulario] = useState(FILTROS_VAZIOS)
  const [filtros, setFiltros] = useState(FILTROS_VAZIOS)

  const { data: opcoes } = useQuery({
    queryKey: ['quadras-filtros'],
    queryFn: quadrasApi.opcoesDeFiltro,
  })
  const { data: quadras, isLoading } = useQuery({
    queryKey: ['quadras', filtros],
    queryFn: () =>
      quadrasApi.listarQuadras({
        esporte: filtros.esporte || undefined,
        nome: filtros.nome || undefined,
        bairro: filtros.bairro || undefined,
      }),
  })

  function atualizarCampo(campo, valor) {
    setFormulario((atual) => ({ ...atual, [campo]: valor }))
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">Agendar quadra</h1>

      {/* Filtros */}
      <form
        className="grid gap-4 rounded-xl bg-white p-4 shadow sm:grid-cols-2 lg:grid-cols-4"
        onSubmit={(evento) => {
          evento.preventDefault()
          setFiltros(formulario)
        }}
      >
        <Campo label="Esporte">
          <select
            className={classesDeInput(false)}
            value={formulario.esporte}
            onChange={(evento) => atualizarCampo('esporte', evento.target.value)}
          >
            <option value="">Todos</option>
            {(opcoes?.esportes || []).map((esporte) => (
              <option key={esporte} value={esporte}>
                {esporte}
              </option>
            ))}
          </select>
        </Campo>
        <Campo label="Nome da quadra">
          <input
            className={classesDeInput(false)}
            value={formulario.nome}
            onChange={(evento) => atualizarCampo('nome', evento.target.value)}
          />
        </Campo>
        <Campo label="Bairro">
          <select
            className={classesDeInput(false)}
            value={formulario.bairro}
            onChange={(evento) => atualizarCampo('bairro', evento.target.value)}
          >
            <option value="">Todos</option>
            {(opcoes?.bairros || []).map((bairro) => (
              <option key={bairro} value={bairro}>
                {bairro}
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

      {isLoading ? (
        <Carregando />
      ) : (quadras || []).length === 0 ? (
        <p className="py-8 text-center text-gray-500">Nenhuma quadra disponível com esses filtros.</p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {quadras.map((quadra) => (
            <div key={quadra.id} className="flex flex-col rounded-xl bg-white p-5 shadow">
              <div className="flex items-start justify-between gap-2">
                <h2 className="text-lg font-semibold text-gray-800">{quadra.nome}</h2>
                <span className="rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-medium text-emerald-800">
                  {quadra.esporte}
                </span>
              </div>
              <p className="mt-1 text-sm text-gray-500">
                {quadra.endereco} — {quadra.bairro}
              </p>
              <p className="mt-2 flex-1 text-sm text-gray-600">{quadra.descricao}</p>
              <Botao
                className="mt-4"
                onClick={() => navigate(`/quadras/${quadra.id}/agendar`, { state: { quadra } })}
              >
                Selecionar
              </Botao>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
