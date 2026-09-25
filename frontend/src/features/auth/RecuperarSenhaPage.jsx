import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link } from 'react-router-dom'

import { mensagemDeErro } from '../../api/client'
import * as authApi from '../../api/auth.api'
import { Alerta, Botao, Campo, classesDeInput } from '../../components/ui'
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
      titulo="Recuperar senha"
      subtitulo="Informe o e-mail e o CPF cadastrados para receber o link de redefinição (válido por 1 hora)."
    >
      {mensagem ? (
        <div className="space-y-4">
          <Alerta tipo="sucesso">{mensagem}</Alerta>
          <Link to="/login" className="block text-center text-sm text-gray-500 hover:underline">
            Voltar para o login
          </Link>
        </div>
      ) : (
        <form className="space-y-4" onSubmit={handleSubmit(aoEnviar)} noValidate>
          <Campo label="E-mail" erro={errors.email?.message}>
            <input
              type="email"
              className={classesDeInput(errors.email)}
              {...register('email', { required: 'Informe o e-mail.' })}
            />
          </Campo>
          <Campo label="CPF" erro={errors.cpf?.message}>
            <input
              className={classesDeInput(errors.cpf)}
              inputMode="numeric"
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
          <Link to="/login" className="block text-center text-sm text-gray-500 hover:underline">
            Voltar
          </Link>
        </form>
      )}
    </CartaoAuth>
  )
}
