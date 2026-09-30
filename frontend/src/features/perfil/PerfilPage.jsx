import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import * as agendamentosApi from '../../api/agendamentos.api'
import { mensagemDeErro } from '../../api/client'
import * as usuariosApi from '../../api/usuarios.api'
import { classesDeInput } from '../../components/estilos'
import { Alerta, Botao, Campo, Carregando, Modal } from '../../components/ui'
import { useAuth } from '../../contexts/useAuth'
import { mascararCpf } from '../../utils/cpf'

export default function PerfilPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { limparSessao } = useAuth()
  const [email, setEmail] = useState(null)
  const [mensagem, setMensagem] = useState('')
  const [erro, setErro] = useState('')
  const [modalAberto, setModalAberto] = useState(false)

  const { data: perfil, isLoading } = useQuery({
    queryKey: ['meu-perfil'],
    queryFn: usuariosApi.meuPerfil,
  })

  const { data: confirmados } = useQuery({
    queryKey: ['meus-agendamentos', 'Confirmado'],
    queryFn: () => agendamentosApi.meusAgendamentos({ status: 'Confirmado' }),
  })

  const salvarEmail = useMutation({
    mutationFn: () => usuariosApi.atualizarMeuEmail(email),
    onSuccess: () => {
      setErro('')
      setMensagem('E-mail atualizado com sucesso.')
      queryClient.invalidateQueries({ queryKey: ['meu-perfil'] })
    },
    onError: (excecao) => {
      setMensagem('')
      setErro(mensagemDeErro(excecao))
    },
  })

  const desativar = useMutation({
    mutationFn: usuariosApi.desativarMinhaConta,
    onSuccess: () => {
      limparSessao()
      navigate('/login', {
        state: { mensagem: 'Conta desativada com sucesso. Sentiremos sua falta!' },
      })
    },
    onError: (excecao) => {
      setModalAberto(false)
      setErro(mensagemDeErro(excecao))
    },
  })

  if (isLoading) return <Carregando />

  const emailAtual = email ?? perfil?.email ?? ''
  const temConfirmado = (confirmados || []).length > 0

  return (
    <div className="mx-auto max-w-lg space-y-4">
      <h1 className="text-2xl font-bold text-gray-800">Meu perfil</h1>

      <div className="space-y-4 rounded-xl bg-white p-6 shadow">
        <Campo label="Nome Completo">
          <input className={classesDeInput(false)} value={perfil?.nome || ''} disabled readOnly />
        </Campo>
        <Campo label="CPF">
          <input
            className={classesDeInput(false)}
            value={mascararCpf(perfil?.cpf || '')}
            disabled
            readOnly
          />
        </Campo>
        <Campo label="E-mail">
          <input
            type="email"
            className={classesDeInput(Boolean(erro))}
            value={emailAtual}
            onChange={(evento) => setEmail(evento.target.value)}
          />
        </Campo>

        <Alerta tipo="sucesso">{mensagem}</Alerta>
        <Alerta tipo="erro">{erro}</Alerta>

        <div className="flex flex-wrap gap-3">
          <Botao onClick={() => salvarEmail.mutate()} carregando={salvarEmail.isPending}>
            Salvar alterações
          </Botao>
          <Botao variante="perigo" onClick={() => setModalAberto(true)}>
            Desativar conta
          </Botao>
          <Botao variante="secundario" onClick={() => navigate('/')}>
            Voltar
          </Botao>
        </div>
      </div>

      {/* Modal: Desativar conta */}
      <Modal aberto={modalAberto} titulo="Desativar conta" onFechar={() => setModalAberto(false)}>
        <div className="space-y-4">
          {temConfirmado && (
            <Alerta tipo="aviso">
              Você possui agendamento com status “Confirmado”. Ao desativar a conta, ele será
              cancelado automaticamente.
            </Alerta>
          )}
          <p className="text-sm text-gray-600">
            Sua conta será desativada e você não poderá mais acessar o sistema. O histórico de
            agendamentos será preservado e a reativação pode ser solicitada à Secretaria de
            Esportes.
          </p>
          <div className="flex justify-end gap-3">
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
