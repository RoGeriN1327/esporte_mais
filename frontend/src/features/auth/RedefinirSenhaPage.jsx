import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'

import { mensagemDeErro } from '../../api/client'
import * as authApi from '../../api/auth.api'
import CampoSenha from '../../components/CampoSenha'
import { Alerta, Botao } from '../../components/ui'
import CartaoAuth from './CartaoAuth'

export default function RedefinirSenhaPage() {
  const [parametros] = useSearchParams()
  const token = parametros.get('token') || ''
  const navigate = useNavigate()
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)
  const { register, handleSubmit, getValues, formState: { errors } } = useForm()

  async function aoSalvar(dados) {
    setErro('')
    setEnviando(true)
    try {
      await authApi.redefinirSenha(token, dados.novaSenha, dados.confirmarSenha)
      navigate('/login', {
        state: { mensagem: 'Senha redefinida com sucesso. Faça login com a nova senha.' },
      })
    } catch (excecao) {
      setErro(mensagemDeErro(excecao))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <CartaoAuth titulo="Redefinir senha" subtitulo="Crie a sua nova senha de acesso.">
      {!token && <Alerta tipo="aviso">Link inválido. Solicite uma nova recuperação de senha.</Alerta>}
      <form className="mt-5 space-y-5" onSubmit={handleSubmit(aoSalvar)} noValidate>
        <CampoSenha
          label="Nova senha"
          erro={errors.novaSenha?.message}
          dica="Mínimo de 8 caracteres."
          autoComplete="new-password"
          {...register('novaSenha', {
            required: 'Informe a nova senha.',
            minLength: { value: 8, message: 'A senha deve ter no mínimo 8 caracteres.' },
          })}
        />
        <CampoSenha
          label="Confirmar nova senha"
          erro={errors.confirmarSenha?.message}
          autoComplete="new-password"
          {...register('confirmarSenha', {
            required: 'Confirme a nova senha.',
            validate: (valor) =>
              valor === getValues('novaSenha') || 'A confirmação de senha não confere com a senha informada.',
          })}
        />
        <Alerta tipo="erro">{erro}</Alerta>
        <Botao type="submit" carregando={enviando} disabled={!token} className="w-full">
          Salvar nova senha
        </Botao>
        <Link to="/login" className="flex h-11 w-full items-center justify-center rounded-lg border border-cinza-300 text-sm font-bold text-cinza-800 transition-colors hover:border-cinza-400 hover:bg-cinza-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marca-600">
          Cancelar
        </Link>
      </form>
    </CartaoAuth>
  )
}
