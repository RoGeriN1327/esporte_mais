import api from './client'

export async function criarAgendamento({ idQuadra, data: dia, horaInicio }) {
  const { data } = await api.post('/agendamentos', {
    id_quadra: idQuadra,
    data: dia,
    hora_inicio: horaInicio,
  })
  return data
}

export async function meusAgendamentos(filtros = {}) {
  const { data } = await api.get('/agendamentos/me', { params: filtros })
  return data
}

export async function proximoAgendamento() {
  const { data } = await api.get('/agendamentos/me/proximo')
  return data
}

export async function cancelarAgendamento(id) {
  const { data } = await api.post(`/agendamentos/${id}/cancelar`)
  return data
}

export async function renovarAgendamento(id, { data: dia, horaInicio }) {
  const { data } = await api.post(`/agendamentos/${id}/renovar`, {
    data: dia,
    hora_inicio: horaInicio,
  })
  return data
}
