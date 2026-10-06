import api from './client'

export async function listarAdministradores() {
  const { data } = await api.get('/admin/administradores')
  return data
}

export async function cadastrarAdministrador({ nome, cpf, email, perfil }) {
  const { data } = await api.post('/admin/administradores', { nome, cpf, email, perfil })
  return data
}

export async function editarAdministrador(id, { nome, cpf, email, perfil }) {
  const { data } = await api.put(`/admin/administradores/${id}`, { nome, cpf, email, perfil })
  return data
}

export async function desativarAdministrador(id) {
  const { data } = await api.post(`/admin/administradores/${id}/desativar`)
  return data
}

export async function listarUsuariosPessoa() {
  const { data } = await api.get('/admin/usuarios-pessoa')
  return data
}

export async function cadastrarUsuarioPessoa({ nome, cpf, email }) {
  const { data } = await api.post('/admin/usuarios-pessoa', { nome, cpf, email })
  return data
}

export async function desativarUsuarioPessoa(id) {
  const { data } = await api.post(`/admin/usuarios-pessoa/${id}/desativar`)
  return data
}

export async function reativarUsuarioPessoa(id) {
  const { data } = await api.post(`/admin/usuarios-pessoa/${id}/reativar`)
  return data
}

export async function listarQuadrasAdmin(filtros = {}) {
  const { data } = await api.get('/admin/quadras', { params: filtros })
  return data
}

export async function cadastrarQuadra(payload) {
  const { data } = await api.post('/admin/quadras', payload)
  return data
}

export async function editarQuadra(id, payload) {
  const { data } = await api.put(`/admin/quadras/${id}`, payload)
  return data
}

export async function desativarQuadra(id) {
  const { data } = await api.post(`/admin/quadras/${id}/desativar`)
  return data
}

export async function painelAgendamentos(filtros = {}) {
  const { data } = await api.get('/admin/agendamentos', { params: filtros })
  return data
}

export async function criarAgendamentoAdmin({ cpfUsuario, idQuadra, data: dia, horaInicio }) {
  const { data } = await api.post('/admin/agendamentos', {
    cpf_usuario: cpfUsuario,
    id_quadra: idQuadra,
    data: dia,
    hora_inicio: horaInicio,
  })
  return data
}

export async function remarcarAgendamento(id, { data: dia, horaInicio }) {
  const { data } = await api.post(`/admin/agendamentos/${id}/remarcar`, {
    data: dia,
    hora_inicio: horaInicio,
  })
  return data
}

export async function cancelarAgendamentoAdmin(id) {
  const { data } = await api.post(`/admin/agendamentos/${id}/cancelar`)
  return data
}

export async function obterConfiguracoes() {
  const { data } = await api.get('/admin/configuracoes')
  return data
}

export async function atualizarConfiguracoes(payload) {
  const { data } = await api.put('/admin/configuracoes', payload)
  return data
}

export async function listarIpsBloqueados() {
  const { data } = await api.get('/admin/ips-bloqueados')
  return data
}

export async function desbloquearIp(ip) {
  const { data } = await api.delete(`/admin/ips-bloqueados/${encodeURIComponent(ip)}`)
  return data
}
