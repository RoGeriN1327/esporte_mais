import api from './client'

export async function cadastrar({ nome, cpf, email, senha, confirmarSenha }) {
  const { data } = await api.post('/usuarios', {
    nome,
    cpf,
    email,
    senha,
    confirmar_senha: confirmarSenha,
  })
  return data
}

export async function meuPerfil() {
  const { data } = await api.get('/usuarios/me')
  return data
}

export async function atualizarMeuEmail(email) {
  const { data } = await api.patch('/usuarios/me', { email })
  return data
}

export async function desativarMinhaConta() {
  const { data } = await api.post('/usuarios/me/desativar')
  return data
}
