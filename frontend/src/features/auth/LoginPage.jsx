import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { mensagemDeErro } from '../../api/client'
import { Alerta, Botao, Campo, classesDeInput } from '../../components/ui'
import { useAuth } from '../../contexts/AuthContext'
import CartaoAuth from './CartaoAuth'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)
  const { register, handleSubmit, formState: { errors } } = useForm()

  async function aoEntrar(dados) {
    setErro('')
    setEnviando(true)
    try {
      const usuario = await login(dados.email, dados.senha)
      navigate(usuario.tipo === 'Administrativo' ? '/admin' : '/')
    } catch (excecao) {
      setErro(mensagemDeErro(excecao))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <CartaoAuth titulo="Entrar no sistema">
      {location.state?.mensagem && <Alerta tipo="sucesso">{location.state.mensagem}</Alerta>}
      <form className="mt-3 space-y-4" onSubmit={handleSubmit(aoEntrar)} noValidate>
        <Campo label="E-mail" erro={errors.email?.message}>
          <input
            type="email"
            autoComplete="email"
            className={classesDeInput(errors.email)}
            {...register('email', { required: 'Informe o e-mail.' })}
          />
        </Campo>
        <Campo label="Senha" erro={errors.senha?.message}>
          <input
            type="password"
            autoComplete="current-password"
            className={classesDeInput(errors.senha)}
            {...register('senha', { required: 'Informe a senha.' })}
          />
        </Campo>
        <Alerta tipo="erro">{erro}</Alerta>
        <Botao type="submit" carregando={enviando} className="w-full">
          Entrar
        </Botao>
      </form>
      <div className="mt-4 flex flex-col gap-2 text-center text-sm">
        {}
        <Link to="/cadastro" className="font-medium text-emerald-700 hover:underline">
          Criar uma conta
        </Link>
        <Link to="/recuperar-senha" className="text-gray-500 hover:underline">
          Esqueci minha senha
        </Link>
      </div>
    </CartaoAuth>
  )
}
