// Utilitários de estilo compartilhados. Ficam fora de ui.jsx para que aquele
// arquivo exporte apenas componentes — requisito do Fast Refresh do Vite.
export function classesDeInput(temErro, { multilinha = false } = {}) {
  return `${multilinha ? 'min-h-24 py-2.5' : 'h-11'} w-full rounded-lg border bg-white px-3.5 text-[15px] text-cinza-900 transition-colors placeholder:text-cinza-400 outline-none focus:ring-3 disabled:bg-cinza-50 disabled:text-cinza-500 ${
    temErro
      ? 'border-erro-600 focus:border-erro-600 focus:ring-erro-600/15'
      : 'border-cinza-300 hover:border-cinza-400 focus:border-marca-600 focus:ring-marca-600/15'
  }`
}
