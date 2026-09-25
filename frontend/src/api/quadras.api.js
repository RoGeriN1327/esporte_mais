import api from './client'

export async function listarQuadras(filtros = {}) {
  const { data } = await api.get('/quadras', { params: filtros })
  return data
}

export async function opcoesDeFiltro() {
  const { data } = await api.get('/quadras/filtros')
  return data
}

export async function horariosDisponiveis(quadraId, data_) {
  const { data } = await api.get(`/quadras/${quadraId}/horarios-disponiveis`, {
    params: { data: data_ },
  })
  return data
}
