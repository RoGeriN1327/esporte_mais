// Utilitários de estilo compartilhados. Ficam fora de ui.jsx para que aquele
// arquivo exporte apenas componentes — requisito do Fast Refresh do Vite.
export function classesDeInput(temErro) {
  return `w-full rounded-lg border px-3 py-2 text-sm outline-none transition focus:ring-2 ${
    temErro
      ? 'border-red-500 focus:border-red-500 focus:ring-red-200'
      : 'border-gray-300 focus:border-emerald-500 focus:ring-emerald-200'
  }`
}
