// Estado de uma tela de consulta guardado na URL (?buscar=1&esporte=...):
// a consulta só roda depois que o usuário clica em "Buscar", e voltar para a tela
// (ou recarregar, ou compartilhar o link) mantém os filtros e os resultados.
import { useSearchParams } from 'react-router-dom'

const MARCADOR = 'buscar'

export function useConsultaNaUrl(chaves) {
  const [params, setParams] = useSearchParams()

  const filtros = Object.fromEntries(chaves.map((chave) => [chave, params.get(chave) ?? '']))
  const consultado = params.has(MARCADOR)

  function buscar(valores) {
    const proximos = new URLSearchParams({ [MARCADOR]: '1' })
    chaves.forEach((chave) => {
      const valor = String(valores[chave] ?? '').trim()
      if (valor) proximos.set(chave, valor)
    })
    setParams(proximos)
  }

  /** "Limpar filtros": remove os filtros e consulta tudo (comportamento do DERS). */
  function limpar() {
    setParams(new URLSearchParams({ [MARCADOR]: '1' }))
  }

  /** Filtros preenchidos, prontos para a API (sem chaves vazias). */
  const parametrosApi = Object.fromEntries(Object.entries(filtros).filter(([, valor]) => valor))

  return { filtros, parametrosApi, consultado, buscar, limpar, busca: params.toString() }
}
