// Blocos de estrutura das telas: cabeçalho com "Voltar", cartão, painel de filtros e estados vazios.
import { TbArrowLeft, TbChevronRight, TbSearch, TbSearchOff } from 'react-icons/tb'
import { Link } from 'react-router-dom'

import { Alerta, Botao, Carregando } from './ui'

export function CabecalhoPagina({ titulo, descricao, voltarPara, voltarTexto = 'Voltar', acoes }) {
  return (
    <div className="mb-8">
      {voltarPara && (
        <Link
          to={voltarPara}
          className="-ml-2 mb-3 inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-sm font-bold text-cinza-600 transition-colors hover:bg-cinza-100 hover:text-cinza-900 focus-visible:outline-2 focus-visible:outline-marca-600"
        >
          <TbArrowLeft aria-hidden="true" className="size-4" />
          {voltarTexto}
        </Link>
      )}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="min-w-0">
          <h1 className="text-[1.75rem] font-black leading-tight text-cinza-900">{titulo}</h1>
          {descricao && <p className="mt-1.5 max-w-2xl text-cinza-600">{descricao}</p>}
        </div>
        {acoes && <div className="flex shrink-0 flex-wrap gap-3">{acoes}</div>}
      </div>
    </div>
  )
}

export function Cartao({ titulo, descricao, children, className = '', ...props }) {
  return (
    <section className={`rounded-2xl border border-cinza-200 bg-white p-5 sm:p-6 ${className}`} {...props}>
      {titulo && (
        <header className="mb-5">
          <h2 className="text-lg font-extrabold text-cinza-900">{titulo}</h2>
          {descricao && <p className="mt-1 text-sm text-cinza-600">{descricao}</p>}
        </header>
      )}
      {children}
    </section>
  )
}

/** Formulário de filtros: campos em grade e, ao final, os botões (Buscar / Limpar filtros). */
export function PainelFiltros({ onBuscar, botoes, children, colunas = 'lg:grid-cols-3' }) {
  return (
    <form
      role="search"
      noValidate
      onSubmit={(evento) => {
        evento.preventDefault()
        onBuscar(new FormData(evento.currentTarget))
      }}
      className="rounded-2xl border border-cinza-200 bg-white p-5 sm:p-6"
    >
      <div className={`grid gap-4 sm:grid-cols-2 ${colunas}`}>{children}</div>
      <div className="mt-5 flex flex-col-reverse gap-3 border-t border-cinza-100 pt-5 sm:flex-row sm:justify-end">{botoes}</div>
    </form>
  )
}

/** Botões padrão do painel de filtros (Quadro 24 e equivalentes do DERS). */
export function BotoesFiltro({ onLimpar, buscando = false }) {
  return (
    <>
      <Botao type="button" variante="secundario" onClick={onLimpar}>
        Limpar filtros
      </Botao>
      <Botao type="submit" carregando={buscando}>
        {!buscando && <TbSearch aria-hidden="true" className="size-[18px]" />}
        Buscar
      </Botao>
    </>
  )
}

/** Lista de registros em que cada linha abre os detalhes (padrão das telas de consulta). */
export function ListaClicavel({ titulo, total, rotuloSingular, rotuloPlural, children }) {
  return (
    <section aria-label={titulo}>
      <p className="mb-4 text-sm font-bold text-cinza-600">
        {total} {total === 1 ? rotuloSingular : rotuloPlural}
      </p>
      <ul className="divide-y divide-cinza-100 overflow-hidden rounded-2xl border border-cinza-200 bg-white">{children}</ul>
    </section>
  )
}

export function ItemClicavel({ onClick, children }) {
  return (
    <li>
      <button
        type="button"
        onClick={onClick}
        className="flex w-full items-center gap-4 px-4 py-4 text-left transition-colors hover:bg-cinza-50 focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-marca-600 sm:px-5"
      >
        {children}
        <TbChevronRight aria-hidden="true" className="hidden size-5 shrink-0 text-cinza-400 sm:block" />
      </button>
    </li>
  )
}

/** Pares rótulo/valor dentro dos modais de detalhes. */
export function ListaDetalhes({ linhas }) {
  return (
    <dl className="divide-y divide-cinza-100 rounded-xl border border-cinza-200">
      {linhas.map(({ rotulo, valor, classe = '' }) => (
        <div key={rotulo} className="flex items-center justify-between gap-4 px-4 py-2.5 text-sm">
          <dt className="shrink-0 text-cinza-500">{rotulo}</dt>
          <dd className={`min-w-0 break-words text-right font-bold text-cinza-900 ${classe}`}>{valor}</dd>
        </div>
      ))}
    </dl>
  )
}

/** Botões de rodapé de modais e formulários (no celular, empilhados com o principal em cima). */
export function BarraAcoes({ children, separada = false }) {
  return (
    <div className={`flex flex-col-reverse gap-3 sm:flex-row sm:justify-end ${separada ? 'border-t border-cinza-100 pt-5' : ''}`}>
      {children}
    </div>
  )
}

const TONS_ESTADO = {
  marca: 'bg-marca-50 text-marca-700 ring-marca-100',
  neutro: 'bg-cinza-100 text-cinza-500 ring-cinza-200/60',
}

/** Aviso centralizado para quando ainda não há o que mostrar (ou a busca não encontrou nada). */
export function EstadoVazio({ Icone, titulo, descricao, acao, tom = 'neutro' }) {
  return (
    <div
      role="status"
      className="flex flex-col items-center rounded-2xl border border-dashed border-cinza-300 bg-white px-6 py-14 text-center"
    >
      <span className={`grid size-14 place-items-center rounded-2xl ring-8 ${TONS_ESTADO[tom]}`}>
        <Icone aria-hidden="true" className="size-7" />
      </span>
      <p className="mt-6 text-lg font-extrabold text-cinza-900">{titulo}</p>
      {descricao && <p className="mt-1.5 max-w-md text-[15px] text-cinza-600">{descricao}</p>}
      {acao && <div className="mt-6">{acao}</div>}
    </div>
  )
}

/**
 * Estados de uma tela de consulta: antes de buscar (orientação), carregando, erro,
 * nenhum resultado e, por fim, os resultados (children).
 */
export function ResultadoConsulta({ consultado, carregando, erro, vazio, inicial, textoCarregando, tituloVazio, descricaoVazio, children }) {
  if (!consultado) return <EstadoVazio tom="marca" {...inicial} />
  if (carregando) return <Carregando texto={textoCarregando} />
  if (erro) return <Alerta tipo="erro">{erro}</Alerta>
  if (vazio) return <EstadoVazio Icone={TbSearchOff} titulo={tituloVazio} descricao={descricaoVazio} />
  return children
}
