// Perfil do Usuário Pessoa (RF001: A1 visualizar, A2 editar e-mail, A3 desativar conta;
// campos do Quadro 13 e botões dos Quadros 14 e 15 do DERS).
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { TbAlertTriangle } from 'react-icons/tb'
import { useNavigate } from 'react-router-dom'

import * as agendamentosApi from '../../api/agendamentos.api'
import { mensagemDeErro } from '../../api/client'
import * as usuariosApi from '../../api/usuarios.api'
import { CabecalhoPagina, Cartao } from '../../components/Pagina'
import { classesDeInput } from '../../components/estilos'
import { Alerta, Botao, Campo, Carregando, Modal } from '../../components/ui'
import { useAuth } from '../../contexts/useAuth'
import { mascararCpf } from '../../utils/cpf'

const FORMATO_EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export default function PerfilPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { limparSessao } = useAuth()
  const [email, setEmail] = useState(null)
  const [mensagem, setMensagem] = useState('')
  const [erroEmail, setErroEmail] = useState('')
  const [erroDesativar, setErroDesativar] = useState('')
  const [modalAberto, setModalAberto] = useState(false)

  const { data: perfil, isLoading } = useQuery({ queryKey: ['meu-perfil'], queryFn: usuariosApi.meuPerfil })
  const { data: confirmados } = useQuery({
    queryKey: ['meus-agendamentos', { status: 'Confirmado' }],
    queryFn: () => agendamentosApi.meusAgendamentos({ status: 'Confirmado' }),
  })

  const salvarEmail = useMutation({
    mutationFn: (novoEmail) => usuariosApi.atualizarMeuEmail(novoEmail),
    onSuccess: () => {
      setErroEmail('')
      setMensagem('E-mail atualizado com sucesso.')
      queryClient.invalidateQueries({ queryKey: ['meu-perfil'] })
    },
    onError: (excecao) => {
      setMensagem('')
      setErroEmail(mensagemDeErro(excecao))
    },
  })

  const desativar = useMutation({
    mutationFn: usuariosApi.desativarMinhaConta,
    onSuccess: () => {
      limparSessao()
      navigate('/login', { state: { mensagem: 'Sua conta foi desativada. Para reativá-la, procure a Secretaria de Esportes.' } })
    },
    onError: (excecao) => {
      setModalAberto(false)
      setErroDesativar(mensagemDeErro(excecao))
    },
  })

  if (isLoading) return <Carregando />

  const emailAtual = email ?? perfil?.email ?? ''
  const temConfirmado = (confirmados ?? []).length > 0

  function aoSalvar(evento) {
    evento.preventDefault()
    setMensagem('')
    const valor = emailAtual.trim()
    if (!FORMATO_EMAIL.test(valor)) {
      setErroEmail('Informe um e-mail válido, no formato nome@exemplo.com.')
      return
    }
    setErroEmail('')
    salvarEmail.mutate(valor)
  }

  return (
    <div className="mx-auto max-w-2xl">
      <CabecalhoPagina voltarPara="/" titulo="Meu perfil" descricao="Seus dados de cadastro no Esporte+." />

      <div className="space-y-6">
        <Cartao titulo="Dados pessoais" descricao="Nome e CPF não podem ser alterados. Você pode atualizar seu e-mail.">
          <form className="space-y-5" onSubmit={aoSalvar} noValidate>
            <div className="grid gap-5 sm:grid-cols-2">
              <Campo label="Nome completo">
                <input className={classesDeInput(false)} value={perfil?.nome ?? ''} disabled readOnly />
              </Campo>
              <Campo label="CPF">
                <input className={`${classesDeInput(false)} tabular-nums`} value={mascararCpf(perfil?.cpf ?? '')} disabled readOnly />
              </Campo>
            </div>
            <Campo label="E-mail" erro={erroEmail}>
              <input
                type="email"
                name="email"
                inputMode="email"
                autoComplete="email"
                spellCheck={false}
                className={classesDeInput(Boolean(erroEmail))}
                value={emailAtual}
                onChange={(evento) => setEmail(evento.target.value)}
              />
            </Campo>

            <Alerta tipo="sucesso">{mensagem}</Alerta>

            <div className="flex flex-col gap-3 border-t border-cinza-100 pt-5 sm:flex-row sm:justify-end">
              <Botao type="submit" carregando={salvarEmail.isPending}>
                {salvarEmail.isPending ? 'Salvando…' : 'Salvar alterações'}
              </Botao>
            </div>
          </form>
        </Cartao>

        <Cartao className="border-erro-200">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-lg font-extrabold text-cinza-900">Desativar conta</h2>
              <p className="mt-1 text-sm text-cinza-600">
                Você deixará de acessar o sistema. Seu histórico de agendamentos é preservado.
              </p>
            </div>
            <Botao variante="perigo" className="shrink-0" onClick={() => setModalAberto(true)}>
              Desativar conta
            </Botao>
          </div>
          {erroDesativar && (
            <div className="mt-4">
              <Alerta tipo="erro">{erroDesativar}</Alerta>
            </div>
          )}
        </Cartao>
      </div>

      {/* Quadro 15 — confirmação de desativação */}
      <Modal aberto={modalAberto} titulo="Desativar conta" onFechar={() => setModalAberto(false)}>
        <div className="space-y-5">
          {temConfirmado && (
            <Alerta tipo="aviso">
              Você possui agendamento com status “Confirmado”. Ao desativar a conta, ele será cancelado automaticamente.
            </Alerta>
          )}
          <div className="flex gap-3">
            <TbAlertTriangle aria-hidden="true" className="mt-0.5 size-5 shrink-0 text-erro-600" />
            <p className="text-[15px] text-cinza-700">
              Sua conta será desativada e você não poderá mais acessar o sistema. O histórico de agendamentos será preservado,
              e a reativação pode ser solicitada à Secretaria de Esportes.
            </p>
          </div>
          <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
            <Botao variante="secundario" onClick={() => setModalAberto(false)}>
              Cancelar
            </Botao>
            <Botao variante="perigo" onClick={() => desativar.mutate()} carregando={desativar.isPending}>
              Confirmar Inativação
            </Botao>
          </div>
        </div>
      </Modal>
    </div>
  )
}
