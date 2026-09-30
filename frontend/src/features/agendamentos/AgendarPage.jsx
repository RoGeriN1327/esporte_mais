import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'

import * as agendamentosApi from '../../api/agendamentos.api'
import { mensagemDeErro } from '../../api/client'
import * as quadrasApi from '../../api/quadras.api'
import SeletorDataHorario from '../../components/SeletorDataHorario'
import { classesDeInput } from '../../components/estilos'
import { Alerta, Botao, Campo, Carregando } from '../../components/ui'

export default function AgendarPage() {
  const { id } = useParams()
  const quadraId = Number(id)
  const navigate = useNavigate()
  const location = useLocation()
  const queryClient = useQueryClient()
  const [data, setData] = useState('')
  const [hora, setHora] = useState('')
  const [erro, setErro] = useState('')

  const quadraDoEstado = location.state?.quadra
  const { data: quadras, isLoading } = useQuery({
    queryKey: ['quadras', {}],
    queryFn: () => quadrasApi.listarQuadras(),
    enabled: !quadraDoEstado,
  })
  const quadra = quadraDoEstado || (quadras || []).find((registro) => registro.id === quadraId)

  const confirmar = useMutation({
    mutationFn: () => agendamentosApi.criarAgendamento({ idQuadra: quadraId, data, horaInicio: hora }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proximo-agendamento'] })
      navigate('/meus-agendamentos', {
        state: { mensagem: 'Agendamento confirmado com sucesso! Você receberá um e-mail de confirmação.' },
      })
    },
    onError: (excecao) => {
      setErro(mensagemDeErro(excecao))
      // O horário pode ter sido ocupado por outra pessoa: recarrega a lista.
      setHora('')
      queryClient.invalidateQueries({ queryKey: ['horarios-disponiveis', quadraId] })
    },
  })

  if (!quadraDoEstado && isLoading) return <Carregando />
  if (!quadra) {
    return <Alerta tipo="erro">Quadra não encontrada. Volte à consulta e selecione novamente.</Alerta>
  }

  return (
    <div className="mx-auto max-w-lg space-y-4">
      <h1 className="text-2xl font-bold text-gray-800">Agendar horário</h1>

      <div className="space-y-4 rounded-xl bg-white p-6 shadow">
        <Campo label="Nome da quadra">
          <input
            className={classesDeInput(false)}
            value={`${quadra.nome} — ${quadra.esporte}`}
            disabled
            readOnly
          />
        </Campo>
        <p className="text-sm text-gray-500">
          {quadra.endereco} — {quadra.bairro}
        </p>

        <SeletorDataHorario
          quadraId={quadraId}
          data={data}
          hora={hora}
          onMudarData={setData}
          onMudarHora={setHora}
        />

        <Alerta tipo="erro">{erro}</Alerta>

        <div className="flex gap-3">
          <Botao
            onClick={() => confirmar.mutate()}
            carregando={confirmar.isPending}
            disabled={!data || !hora}
            className="flex-1"
          >
            Confirmar agendamento
          </Botao>
          <Botao variante="secundario" onClick={() => navigate('/quadras')}>
            Voltar
          </Botao>
        </div>
      </div>
    </div>
  )
}
