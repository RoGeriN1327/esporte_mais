import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'

import { mensagemDeErro } from '../../api/client'
import * as authApi from '../../api/auth.api'
import CampoSenha from '../../components/CampoSenha'
import { Alerta, Botao, Carregando } from '../../components/ui'
import CartaoAuth from './CartaoAuth'

const CLASSE_BOTAO_SECUNDARIO =
  'flex h-11 w-full items-center justify-center rounded-lg border border-cinza-300 text-sm font-bold text-cinza-800 transition-colors hover:border-cinza-400 hover:bg-cinza-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marca-600'

export default function RedefinirSenhaPage() {
  const [parametros] = useSearchParams()
  const token = parametros.get('token') || ''
  const navigate = useNavigate()
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)
  const { register, handleSubmit, getValues, formState: { errors } } = useForm()

  // Confere o link ao abrir a página, antes de o usuário digitar a nova senha.
  const validacao = useQuery({
    queryKey: ['validar-link-redefinicao', token],
    queryFn: () => authApi.validarLinkRedefinicao(token),
    enabled: Boolean(token),
    retry: false,
    staleTime: Infinity,
    refetchOnWindowFocus: false,
  })

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

  if (token && validacao.isPending) {
    return (
      <CartaoAuth titulo="Redefinir senha" subtitulo="Crie a sua nova senha de acesso.">
        <Carregando texto="Verificando o link…" />
      </CartaoAuth>
    )
  }

  // 400 = link inválido/expirado; outros erros (rede, API fora do ar) não dizem nada sobre o link.
  const linkInvalido = !token || validacao.error?.response?.status === 400
  if (linkInvalido || validacao.isError) {
    return (
      <CartaoAuth titulo="Redefinir senha" subtitulo="Crie a sua nova senha de acesso.">
        <div className="mt-5 space-y-5">
          {linkInvalido ? (
            <Alerta tipo="aviso">
              Link inválido ou expirado. Solicite uma nova recuperação de senha.
            </Alerta>
          ) : (
            <Alerta tipo="erro">Não foi possível verificar o link. Tente novamente.</Alerta>
          )}
          {linkInvalido ? (
            <Link to="/recuperar-senha" className={CLASSE_BOTAO_SECUNDARIO}>
              Solicitar novo link
            </Link>
          ) : (
            <Botao
              type="button"
              carregando={validacao.isFetching}
              onClick={() => validacao.refetch()}
              className="w-full"
            >
              Tentar novamente
            </Botao>
          )}
          <Link to="/login" className={CLASSE_BOTAO_SECUNDARIO}>
            Voltar ao login
          </Link>
        </div>
      </CartaoAuth>
    )
  }

  return (
    <CartaoAuth titulo="Redefinir senha" subtitulo="Crie a sua nova senha de acesso.">
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
        <Botao type="submit" carregando={enviando} className="w-full">
          Salvar nova senha
        </Botao>
        <Link to="/login" className={CLASSE_BOTAO_SECUNDARIO}>
          Cancelar
        </Link>
      </form>
    </CartaoAuth>
  )
}
