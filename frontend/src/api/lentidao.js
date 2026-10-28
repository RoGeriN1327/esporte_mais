// Monitor de requisições lentas (cold start da API).
//
// No plano gratuito do Render a API "dorme" sem uso e a primeira resposta pode levar
// de 30 a 60 segundos. Se uma requisição passar de LIMITE_MS, o AvisoLentidao avisa o
// usuário que o sistema está iniciando; o aviso some quando todas as requisições lentas
// terminam. Cada requisição chama iniciar() ao sair e finalizar(id) ao terminar.
export const LIMITE_MS = 3000

let proximoId = 0
const temporizadores = new Map()
const lentas = new Set()
const ouvintes = new Set()

function notificar() {
  ouvintes.forEach((ouvinte) => ouvinte())
}

/** Marca o início de uma requisição; devolve o id para finalizar(). */
export function iniciar() {
  proximoId += 1
  const id = proximoId
  temporizadores.set(
    id,
    setTimeout(() => {
      temporizadores.delete(id)
      lentas.add(id)
      if (lentas.size === 1) notificar()
    }, LIMITE_MS),
  )
  return id
}

/** Marca o fim (sucesso ou erro) de uma requisição. Ignora ids desconhecidos. */
export function finalizar(id) {
  if (temporizadores.has(id)) {
    clearTimeout(temporizadores.get(id))
    temporizadores.delete(id)
  }
  if (lentas.delete(id) && lentas.size === 0) notificar()
}

/** true enquanto houver alguma requisição pendente há mais de LIMITE_MS. */
export function haRequisicaoLenta() {
  return lentas.size > 0
}

/** Assinatura no formato do useSyncExternalStore. */
export function assinar(ouvinte) {
  ouvintes.add(ouvinte)
  return () => ouvintes.delete(ouvinte)
}

/** Monitora uma promessa qualquer (ex.: chamadas feitas com axios fora do cliente api). */
export async function monitorar(promessa) {
  const id = iniciar()
  try {
    return await promessa
  } finally {
    finalizar(id)
  }
}
