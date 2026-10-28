import api from './client'

/** Regras de agendamento exibidas na página pública (não exige login). */
export async function obterRegras() {
  const { data } = await api.get('/regras')
  return data
}
