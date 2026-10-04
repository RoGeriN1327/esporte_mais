// Consulta de quadras (RF003, fluxo básico; campos do Quadro 23 e botões do Quadro 24 do DERS).
// A busca só acontece ao clicar em "Buscar"; os filtros ficam só em memória (URL limpa).
import { useQuery } from '@tanstack/react-query'
import { TbAdjustmentsHorizontal, TbMapPin, TbSearch, TbSearchOff } from 'react-icons/tb'
import { useNavigate } from 'react-router-dom'

import * as quadrasApi from '../../api/quadras.api'
import IconeEsporte from '../../components/IconeEsporte'
import { CabecalhoPagina, EstadoVazio, PainelFiltros } from '../../components/Pagina'
import { classesDeInput } from '../../components/estilos'
import { Alerta, Botao, Campo, Carregando } from '../../components/ui'
import { useConsulta } from '../../hooks/useConsulta'

const CHAVES = ['esporte', 'nome', 'bairro']

function CartaoQuadra({ quadra, onSelecionar }) {
  return (
    <article className="flex flex-col rounded-2xl border border-cinza-200 bg-white p-5 transition-colors hover:border-marca-300">
      <div className="flex items-start gap-3.5">
        <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-marca-50 text-marca-700">
          <IconeEsporte esporte={quadra.esporte} className="size-6" />
        </span>
        <div className="min-w-0">
          <h2 className="break-words text-lg font-extrabold leading-snug text-cinza-900">{quadra.nome}</h2>
          <p className="text-sm font-bold text-marca-700">{quadra.esporte}</p>
        </div>
      </div>
      <p className="mt-4 flex items-start gap-1.5 text-sm text-cinza-600">
        <TbMapPin aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-cinza-400" />
        <span className="min-w-0 break-words">
          {quadra.endereco} · <span className="font-semibold text-cinza-800">{quadra.bairro}</span>
        </span>
      </p>
      <p className="mt-3 line-clamp-3 flex-1 text-sm text-cinza-600">{quadra.descricao}</p>
      <Botao className="mt-5 w-full" onClick={() => onSelecionar(quadra)}>
        Selecionar
      </Botao>
    </article>
  )
}

export default function QuadrasPage() {
  const navigate = useNavigate()
  const consulta = useConsulta(CHAVES)

  const { data: opcoes } = useQuery({ queryKey: ['quadras-filtros'], queryFn: quadrasApi.opcoesDeFiltro })
  const { data: quadras, isFetching, isError } = useQuery({
    queryKey: ['quadras', consulta.parametrosApi],
    queryFn: () => quadrasApi.listarQuadras(consulta.parametrosApi),
    enabled: consulta.consultado,
  })

  function selecionar(quadra) {
    navigate(`/quadras/${quadra.id}/agendar`, { state: { quadra } })
  }

  let resultado
  if (!consulta.consultado) {
    resultado = (
      <EstadoVazio
        tom="marca"
        Icone={TbAdjustmentsHorizontal}
        titulo="Encontre uma quadra para jogar"
        descricao="Escolha o esporte, o nome da quadra ou o bairro e clique em “Buscar”. Para ver todas as quadras, clique em “Buscar” sem preencher nada."
      />
    )
  } else if (isFetching) {
    resultado = <Carregando texto="Buscando quadras…" />
  } else if (isError) {
    resultado = <Alerta tipo="erro">Não foi possível buscar as quadras. Tente novamente em instantes.</Alerta>
  } else if (!quadras?.length) {
    resultado = (
      <EstadoVazio
        Icone={TbSearchOff}
        titulo="Nenhuma quadra encontrada"
        descricao="Não há quadras disponíveis com esses filtros. Altere a busca ou use “Limpar filtros” para ver todas."
      />
    )
  } else {
    resultado = (
      <section aria-labelledby="titulo-resultados">
        <h2 id="titulo-resultados" className="mb-4 text-sm font-bold text-cinza-600">
          {quadras.length} {quadras.length === 1 ? 'quadra encontrada' : 'quadras encontradas'}
        </h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {quadras.map((quadra) => (
            <CartaoQuadra key={quadra.id} quadra={quadra} onSelecionar={selecionar} />
          ))}
        </div>
      </section>
    )
  }

  return (
    <div>
      <CabecalhoPagina
        voltarPara="/"
        voltarTexto="Início"
        titulo="Agendar quadra"
        descricao="Consulte as quadras esportivas públicas disponíveis e selecione uma para escolher o horário."
      />

      <div className="space-y-8">
        <PainelFiltros
          key={`${consulta.versao}|${Boolean(opcoes)}`}
          onBuscar={(dados) => consulta.buscar(Object.fromEntries(dados))}
          botoes={
            <>
              <Botao type="button" variante="secundario" onClick={consulta.limpar}>
                Limpar filtros
              </Botao>
              <Botao type="submit" carregando={isFetching}>
                <TbSearch aria-hidden="true" className="size-[18px]" />
                Buscar
              </Botao>
            </>
          }
        >
          <Campo label="Esporte">
            <select name="esporte" defaultValue={consulta.filtros.esporte} className={classesDeInput(false)}>
              <option value="">Todos</option>
              {(opcoes?.esportes ?? []).map((esporte) => (
                <option key={esporte} value={esporte}>
                  {esporte}
                </option>
              ))}
            </select>
          </Campo>
          <Campo label="Nome da quadra">
            <input
              name="nome"
              defaultValue={consulta.filtros.nome}
              autoComplete="off"
              placeholder="Ex.: Ginásio Municipal…"
              className={classesDeInput(false)}
            />
          </Campo>
          <Campo label="Bairro">
            <select name="bairro" defaultValue={consulta.filtros.bairro} className={classesDeInput(false)}>
              <option value="">Todos</option>
              {(opcoes?.bairros ?? []).map((bairro) => (
                <option key={bairro} value={bairro}>
                  {bairro}
                </option>
              ))}
            </select>
          </Campo>
        </PainelFiltros>

        {resultado}
      </div>
    </div>
  )
}
