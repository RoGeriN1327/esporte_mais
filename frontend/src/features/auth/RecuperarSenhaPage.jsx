import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link } from 'react-router-dom'

import { mensagemDeErro } from '../../api/client'
import * as authApi from '../../api/auth.api'
import { classesDeInput } from '../../components/estilos'
import { Alerta, Botao, Campo } from '../../components/ui'
import { cpfValido, mascararCpf } from '../../utils/cpf'
import CartaoAuth from './CartaoAuth'

export default function RecuperarSenhaPage() {
  const [mensagem, setMensagem] = useState('')
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)
  const { register, handleSubmit, setValue, formState: { errors } } = useForm()

  async function aoEnviar(dados) {
    setErro('')
    setEnviando(true)
    try {
      const resposta = await authApi.recuperarSenha(dados.email, dados.cpf)
      setMensagem(resposta.mensagem)
    } catch (excecao) {
      setErro(mensagemDeErro(excecao))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <CartaoAuth
      voltarPara="/login"
      titulo="Recuperar senha"
      subtitulo="Informe o e-mail e o CPF cadastrados para receber o link de redefinição (válido por 1 hora)."
    >
      {mensagem ? (
        <div className="space-y-5">
          <Alerta tipo="sucesso">{mensagem}</Alerta>
          <Link to="/login" className="flex h-11 w-full items-center justify-center rounded-lg border border-cinza-300 text-sm font-bold text-cinza-800 transition-colors hover:border-cinza-400 hover:bg-cinza-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marca-600">
            Voltar para o login
          </Link>
        </div>
      ) : (
        <form className="space-y-5" onSubmit={handleSubmit(aoEnviar)} noValidate>
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
          <Campo label="CPF" erro={errors.cpf?.message}>
            <input
              className={classesDeInput(errors.cpf)}
              inputMode="numeric"
              autoComplete="off"
              placeholder="000.000.000-00"
              {...register('cpf', {
                required: 'Informe o CPF.',
                validate: (valor) => cpfValido(valor) || 'CPF inválido. Informe 11 dígitos numéricos válidos.',
                onChange: (evento) => setValue('cpf', mascararCpf(evento.target.value)),
              })}
            />
          </Campo>
          <Alerta tipo="erro">{erro}</Alerta>
          <Botao type="submit" carregando={enviando} className="w-full">
            Enviar link
          </Botao>
        </form>
      )}
    </CartaoAuth>
  )
}
