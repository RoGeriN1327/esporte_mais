import api from './client'

export async function login(email, senha) {
  const { data } = await api.post('/auth/login', { email, senha })
  return data
}

export async function logout(refreshToken) {
  const { data } = await api.post('/auth/logout', { refresh_token: refreshToken })
  return data
}

export async function recuperarSenha(email, cpf) {
  const { data } = await api.post('/auth/recuperar-senha', { email, cpf })
  return data
}

export async function redefinirSenha(token, novaSenha, confirmarSenha) {
  const { data } = await api.post('/auth/redefinir-senha', {
    token,
    nova_senha: novaSenha,
    confirmar_senha: confirmarSenha,
  })
  return data
}
