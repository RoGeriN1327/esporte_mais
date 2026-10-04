/** Minúsculas e sem acentos, para buscas em listas ("José" encontra "jose"). */
export function normalizarTexto(valor) {
  return String(valor ?? '')
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .trim()
}

/** Iniciais de um nome (até duas): "Marina Souza" → "MS". */
export function iniciaisDe(nome) {
  return String(nome ?? '')
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((parte) => parte[0])
    .join('')
    .toUpperCase()
}
