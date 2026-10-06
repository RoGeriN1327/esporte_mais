// Tela de login (RF002; campos e botões dos Quadros 7 e 8 do DERS).
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { mensagemDeErro } from '../../api/client'
import CampoSenha from '../../components/CampoSenha'
import { classesDeInput } from '../../components/estilos'
import { Alerta, Botao, Campo } from '../../components/ui'
import { useAuth } from '../../contexts/useAuth'
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
    <CartaoAuth titulo="Entrar" subtitulo="Acesse com o e-mail e a senha da sua conta.">
      <div className="space-y-5">
        {location.state?.mensagem && <Alerta tipo="sucesso">{location.state.mensagem}</Alerta>}
        {location.state?.aviso && <Alerta tipo="aviso">{location.state.aviso}</Alerta>}

        <form className="space-y-5" onSubmit={handleSubmit(aoEntrar)} noValidate>
          <Campo label="E-mail" erro={errors.email?.message}>
            <input
              type="email"
              inputMode="email"
              autoComplete="email"
              spellCheck={false}
              placeholder="nome@exemplo.com"
              className={classesDeInput(errors.email)}
              {...register('email', { required: 'Informe o e-mail.' })}
            />
          </Campo>

          <div className="relative">
            <CampoSenha label="Senha" erro={errors.senha?.message} {...register('senha', { required: 'Informe a senha.' })} />
            <Link
              to="/recuperar-senha"
              className="absolute right-0 top-0 rounded text-sm font-semibold text-marca-700 underline-offset-4 hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marca-600"
            >
              Esqueci minha senha
            </Link>
          </div>

          <Alerta tipo="erro">{erro}</Alerta>

          <Botao type="submit" carregando={enviando} className="w-full">
            {enviando ? 'Entrando…' : 'Entrar'}
          </Botao>
        </form>

        <div className="flex items-center gap-3 text-xs font-semibold uppercase tracking-wider text-cinza-400">
          <span className="h-px flex-1 bg-cinza-200" />
          ou
          <span className="h-px flex-1 bg-cinza-200" />
        </div>

        <Link
          to="/cadastro"
          className="flex h-11 w-full items-center justify-center rounded-lg border border-cinza-300 text-sm font-bold text-cinza-800 transition-colors hover:border-cinza-400 hover:bg-cinza-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marca-600"
        >
          Criar uma conta
        </Link>
      </div>
    </CartaoAuth>
  )
}
