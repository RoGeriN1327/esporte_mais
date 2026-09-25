import { useEffect } from 'react'

export function Botao({ children, variante = 'primario', carregando = false, className = '', ...props }) {
  const estilos = {
    primario: 'bg-emerald-600 hover:bg-emerald-700 text-white',
    secundario: 'bg-white hover:bg-gray-50 text-gray-700 border border-gray-300',
    perigo: 'bg-red-600 hover:bg-red-700 text-white',
  }
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-60 ${estilos[variante]} ${className}`}
      disabled={carregando || props.disabled}
      {...props}
    >
      {carregando && <Spinner pequeno />}
      {children}
    </button>
  )
}

export function Spinner({ pequeno = false }) {
  return (
    <span
      role="status"
      aria-label="Carregando"
      className={`inline-block animate-spin rounded-full border-2 border-current border-t-transparent ${pequeno ? 'h-4 w-4' : 'h-8 w-8 text-emerald-600'}`}
    />
  )
}

export function Carregando() {
  return (
    <div className="flex justify-center py-12">
      <Spinner />
    </div>
  )
}

export function Campo({ label, erro, children }) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-gray-700">{label}</span>
      {children}
      {erro && <span className="mt-1 block text-sm text-red-600">{erro}</span>}
    </label>
  )
}

export function classesDeInput(temErro) {
  return `w-full rounded-lg border px-3 py-2 text-sm outline-none transition focus:ring-2 ${
    temErro
      ? 'border-red-500 focus:border-red-500 focus:ring-red-200'
      : 'border-gray-300 focus:border-emerald-500 focus:ring-emerald-200'
  }`
}

export function Alerta({ tipo = 'erro', children }) {
  if (!children) return null
  const estilos = {
    erro: 'bg-red-50 text-red-700 border-red-200',
    sucesso: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    aviso: 'bg-amber-50 text-amber-800 border-amber-200',
  }
  return <div className={`rounded-lg border px-4 py-3 text-sm ${estilos[tipo]}`}>{children}</div>
}

export function Modal({ aberto, titulo, onFechar, children }) {
  useEffect(() => {
    function aoTeclar(evento) {
      if (evento.key === 'Escape') onFechar?.()
    }
    if (aberto) document.addEventListener('keydown', aoTeclar)
    return () => document.removeEventListener('keydown', aoTeclar)
  }, [aberto, onFechar])

  if (!aberto) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={onFechar}>
      <div
        className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-xl bg-white p-6 shadow-xl"
        onClick={(evento) => evento.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-800">{titulo}</h2>
          <button className="text-gray-400 hover:text-gray-600" onClick={onFechar} aria-label="Fechar">
            ✕
          </button>
        </div>
        {children}
      </div>
    </div>
  )
}

const CORES_STATUS = {
  Confirmado: 'bg-emerald-100 text-emerald-800',
  Cancelado: 'bg-red-100 text-red-700',
  'Concluído': 'bg-gray-200 text-gray-700',
  Renovado: 'bg-blue-100 text-blue-700',
  Ativo: 'bg-emerald-100 text-emerald-800',
  Ativa: 'bg-emerald-100 text-emerald-800',
  Desativado: 'bg-gray-200 text-gray-600',
  Desativada: 'bg-gray-200 text-gray-600',
}

export function Badge({ children }) {
  return (
    <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${CORES_STATUS[children] || 'bg-gray-100 text-gray-700'}`}>
      {children}
    </span>
  )
}
