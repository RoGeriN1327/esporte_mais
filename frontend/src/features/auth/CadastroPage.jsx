import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useNavigate } from 'react-router-dom'

import { mensagemDeErro } from '../../api/client'
import * as usuariosApi from '../../api/usuarios.api'
import { Alerta, Botao, Campo, classesDeInput } from '../../components/ui'
import { cpfValido, mascararCpf } from '../../utils/cpf'
import CartaoAuth from './CartaoAuth'

export default function CadastroPage() {
  const navigate = useNavigate()
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)
  const { register, handleSubmit, setValue, getValues, formState: { errors } } = useForm()

  async function aoCadastrar(dados) {
    setErro('')
    setEnviando(true)
    try {
      await usuariosApi.cadastrar({
        nome: dados.nome,
        cpf: dados.cpf,
        email: dados.email,
        senha: dados.senha,
        confirmarSenha: dados.confirmarSenha,
      })

      navigate('/login', { state: { mensagem: 'Conta criada com sucesso! Faça login para continuar.' } })
    } catch (excecao) {
      setErro(mensagemDeErro(excecao))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <CartaoAuth titulo="Criar uma conta" subtitulo="Informe seus dados para se cadastrar.">
      <form className="space-y-4" onSubmit={handleSubmit(aoCadastrar)} noValidate>
        <Campo label="Nome Completo" erro={errors.nome?.message}>
          <input
            className={classesDeInput(errors.nome)}
            maxLength={100}
            {...register('nome', { required: 'Informe o nome completo.' })}
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
        <Campo label="E-mail" erro={errors.email?.message}>
          <input
            type="email"
            className={classesDeInput(errors.email)}
            {...register('email', {
              required: 'Informe o e-mail.',
              pattern: { value: /.+@.+\..+/, message: 'Informe um e-mail válido.' },
            })}
          />
        </Campo>
        <Campo label="Senha" erro={errors.senha?.message}>
          <input
            type="password"
            autoComplete="new-password"
            className={classesDeInput(errors.senha)}
            {...register('senha', {
              required: 'Informe a senha.',
              minLength: { value: 8, message: 'A senha deve ter no mínimo 8 caracteres.' },
            })}
          />
        </Campo>
        <Campo label="Confirmar senha" erro={errors.confirmarSenha?.message}>
          <input
            type="password"
            autoComplete="new-password"
            className={classesDeInput(errors.confirmarSenha)}
            {...register('confirmarSenha', {
              required: 'Confirme a senha.',
              validate: (valor) =>
                valor === getValues('senha') || 'A confirmação de senha não confere com a senha informada.',
            })}
          />
        </Campo>
        <Alerta tipo="erro">{erro}</Alerta>
        <Botao type="submit" carregando={enviando} className="w-full">
          Cadastrar
        </Botao>
      </form>
      <div className="mt-4 text-center text-sm">
        <Link to="/login" className="text-gray-500 hover:underline">
          Voltar
        </Link>
      </div>
    </CartaoAuth>
  )
}
