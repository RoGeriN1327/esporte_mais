// Estado de uma tela de consulta: filtros aplicados e se o usuário já clicou em "Buscar".
// Fica só em memória (nada vai para a barra de endereço): ao sair da tela e voltar, a
// consulta recomeça vazia. Os filtros seguem para a API apenas na chamada feita pelo JS.
import { useState } from 'react'

function vazios(chaves) {
  return Object.fromEntries(chaves.map((chave) => [chave, '']))
}

export function useConsulta(chaves, { consultarAoAbrir = false } = {}) {
  const [filtros, setFiltros] = useState(() => vazios(chaves))
  const [consultado, setConsultado] = useState(consultarAoAbrir)
  // Muda a cada busca/limpeza; usada como `key` do formulário para refletir os filtros atuais
  const [versao, setVersao] = useState(0)

  function buscar(valores) {
    setFiltros(Object.fromEntries(chaves.map((chave) => [chave, String(valores[chave] ?? '').trim()])))
    setConsultado(true)
    setVersao((atual) => atual + 1)
  }

  /** "Limpar filtros": remove os filtros e consulta tudo (comportamento do DERS). */
  function limpar() {
    setFiltros(vazios(chaves))
    setConsultado(true)
    setVersao((atual) => atual + 1)
  }

  /** Filtros preenchidos, prontos para a API (sem chaves vazias). */
  const parametrosApi = Object.fromEntries(Object.entries(filtros).filter(([, valor]) => valor))

  return { filtros, parametrosApi, consultado, buscar, limpar, versao }
}
