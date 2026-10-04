// Componentes base do design system do Esporte+ (botões, campos, alertas, modal, status).
// Ícones: Tabler (react-icons/tb), traço único em todo o sistema.
import { cloneElement, isValidElement, useEffect, useId, useRef } from 'react'
import { TbAlertTriangle, TbCircleCheck, TbExclamationCircle, TbInfoCircle, TbLoader2, TbX } from 'react-icons/tb'

const ESTILOS_BOTAO = {
  primario: 'bg-marca-600 text-white hover:bg-marca-700 active:bg-marca-800',
  secundario: 'border border-cinza-300 bg-white text-cinza-800 hover:border-cinza-400 hover:bg-cinza-50 active:bg-cinza-100',
  perigo: 'bg-erro-600 text-white hover:bg-erro-700',
  perigoContorno: 'border border-erro-200 bg-white text-erro-700 hover:border-erro-600 hover:bg-erro-50',
  fantasma: 'text-marca-700 hover:bg-marca-50 active:bg-marca-100',
}

export function Botao({ children, variante = 'primario', carregando = false, className = '', ...props }) {
  return (
    <button
      className={`inline-flex h-11 items-center justify-center gap-2 rounded-lg px-4 text-sm font-bold transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marca-600 disabled:cursor-not-allowed disabled:opacity-60 ${ESTILOS_BOTAO[variante]} ${className}`}
      disabled={carregando || props.disabled}
      aria-busy={carregando || undefined}
      {...props}
    >
      {carregando && <Spinner pequeno />}
      {children}
    </button>
  )
}

export function Spinner({ pequeno = false }) {
  return (
    <TbLoader2
      aria-hidden="true"
      className={`shrink-0 animate-spin ${pequeno ? 'size-4' : 'size-8 text-marca-600'}`}
    />
  )
}

export function Carregando({ texto = 'Carregando…' }) {
  return (
    <div role="status" className="flex flex-col items-center justify-center gap-3 py-12 text-sm text-cinza-500">
      <Spinner />
      {texto}
    </div>
  )
}

const CONTROLES = new Set(['input', 'select', 'textarea'])

/**
 * Rótulo + campo + mensagem. Quando o filho é um <input>/<select>/<textarea>, o id, o
 * aria-invalid e o aria-describedby são ligados automaticamente; para campos compostos,
 * passe `id` e aplique-o no controle.
 */
export function Campo({ label, erro, dica, id, children }) {
  const idGerado = useId()
  const idCampo = id ?? idGerado
  const idMensagem = `${idCampo}-mensagem`
  const temMensagem = Boolean(erro || dica)
  // Só controles de formulário recebem o id; um wrapper (ex.: <div> do CampoSenha) não,
  // senão o id ficaria duplicado e o rótulo deixaria de apontar para o campo.
  const controleSimples = isValidElement(children) && CONTROLES.has(children.type)
  const filho = controleSimples
    ? cloneElement(children, {
        id: children.props.id ?? idCampo,
        'aria-invalid': erro ? true : undefined,
        'aria-describedby': temMensagem ? idMensagem : undefined,
      })
    : children

  return (
    <div>
      <label htmlFor={idCampo} className="mb-1.5 block text-sm font-semibold text-cinza-800">
        {label}
      </label>
      {filho}
      {dica && !erro && (
        <p id={idMensagem} className="mt-1.5 text-xs text-cinza-500">
          {dica}
        </p>
      )}
      {erro && (
        <p id={idMensagem} role="alert" className="mt-1.5 flex items-center gap-1 text-sm font-medium text-erro-700">
          <TbExclamationCircle aria-hidden="true" className="size-4 shrink-0" />
          {erro}
        </p>
      )}
    </div>
  )
}

const ESTILOS_ALERTA = {
  erro: { classes: 'border-erro-200 bg-erro-50 text-erro-700', Icone: TbExclamationCircle },
  sucesso: { classes: 'border-marca-200 bg-marca-50 text-marca-800', Icone: TbCircleCheck },
  aviso: { classes: 'border-aviso-200 bg-aviso-50 text-aviso-700', Icone: TbAlertTriangle },
  info: { classes: 'border-cinza-200 bg-cinza-50 text-cinza-700', Icone: TbInfoCircle },
}

export function Alerta({ tipo = 'erro', children }) {
  if (!children) return null
  const { classes, Icone } = ESTILOS_ALERTA[tipo]
  return (
    <div
      role={tipo === 'erro' ? 'alert' : 'status'}
      aria-live="polite"
      className={`flex items-start gap-2.5 rounded-lg border px-3.5 py-3 text-sm font-medium ${classes}`}
    >
      <Icone aria-hidden="true" className="mt-px size-5 shrink-0" />
      <div className="min-w-0 break-words">{children}</div>
    </div>
  )
}

export function Modal({ aberto, titulo, onFechar, largo = false, children }) {
  const idTitulo = useId()
  const caixa = useRef(null)

  useEffect(() => {
    if (!aberto) return
    function aoTeclar(evento) {
      if (evento.key === 'Escape') onFechar?.()
    }
    document.addEventListener('keydown', aoTeclar)
    caixa.current?.focus()
    return () => document.removeEventListener('keydown', aoTeclar)
  }, [aberto, onFechar])

  if (!aberto) return null
  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center overscroll-contain bg-cinza-900/50 p-0 sm:items-center sm:p-4"
      onClick={onFechar}
    >
      <div
        ref={caixa}
        role="dialog"
        aria-modal="true"
        aria-labelledby={idTitulo}
        tabIndex={-1}
        className={`max-h-[90vh] w-full ${largo ? 'max-w-2xl' : 'max-w-lg'} overflow-y-auto overscroll-contain rounded-t-2xl border border-cinza-200 bg-white p-6 outline-none sm:rounded-xl`}
        onClick={(evento) => evento.stopPropagation()}
      >
        <div className="mb-5 flex items-start justify-between gap-4">
          <h2 id={idTitulo} className="text-lg font-extrabold text-cinza-900">
            {titulo}
          </h2>
          <button
            type="button"
            onClick={onFechar}
            aria-label="Fechar"
            className="-m-1.5 rounded-md p-1.5 text-cinza-500 transition-colors hover:bg-cinza-100 hover:text-cinza-800 focus-visible:outline-2 focus-visible:outline-marca-600"
          >
            <TbX aria-hidden="true" className="size-5" />
          </button>
        </div>
        {children}
      </div>
    </div>
  )
}

const ESTILOS_STATUS = {
  Confirmado: 'bg-marca-50 text-marca-700 ring-marca-200',
  Ativo: 'bg-marca-50 text-marca-700 ring-marca-200',
  Ativa: 'bg-marca-50 text-marca-700 ring-marca-200',
  Renovado: 'bg-white text-marca-700 ring-marca-300',
  Cancelado: 'bg-erro-50 text-erro-700 ring-erro-200',
  'Concluído': 'bg-cinza-100 text-cinza-700 ring-cinza-200',
  Desativado: 'bg-cinza-100 text-cinza-600 ring-cinza-200',
  Desativada: 'bg-cinza-100 text-cinza-600 ring-cinza-200',
}

export function Badge({ children }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md px-2 py-0.5 text-xs font-bold ring-1 ring-inset ${ESTILOS_STATUS[children] || 'bg-cinza-100 text-cinza-700 ring-cinza-200'}`}
    >
      <span aria-hidden="true" className="size-1.5 rounded-full bg-current" />
      {children}
    </span>
  )
}
