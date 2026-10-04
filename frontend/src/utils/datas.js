export function formatarData(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('pt-BR')
}

export function formatarHora(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
}

export function formatarDataHora(iso) {
  if (!iso) return ''
  return `${formatarData(iso)} ${formatarHora(iso)}`
}

// Formatadores criados uma vez (Intl é caro de instanciar a cada render).
const FORMATO_DIA_SEMANA = new Intl.DateTimeFormat('pt-BR', { weekday: 'short' })
const FORMATO_MES = new Intl.DateTimeFormat('pt-BR', { month: 'short' })
const FORMATO_DATA_EXTENSA = new Intl.DateTimeFormat('pt-BR', { weekday: 'long', day: 'numeric', month: 'long' })

/** Partes de uma data para blocos de calendário: { diaSemana: "sáb", dia: "04", mes: "out" }. */
export function partesDaData(iso) {
  const data = new Date(iso)
  return {
    diaSemana: FORMATO_DIA_SEMANA.format(data).replace('.', ''),
    dia: String(data.getDate()).padStart(2, '0'),
    mes: FORMATO_MES.format(data).replace('.', ''),
  }
}

/** "sábado, 4 de outubro" */
export function dataExtensa(iso = new Date()) {
  return FORMATO_DATA_EXTENSA.format(new Date(iso))
}

export function horaCurta(hora) {
  return (hora || '').slice(0, 5)
}

export function hojeISO() {
  const agora = new Date()
  agora.setMinutes(agora.getMinutes() - agora.getTimezoneOffset())
  return agora.toISOString().slice(0, 10)
}

export const DIAS_SEMANA = [
  'Segunda-feira',
  'Terça-feira',
  'Quarta-feira',
  'Quinta-feira',
  'Sexta-feira',
  'Sábado',
  'Domingo',
]
