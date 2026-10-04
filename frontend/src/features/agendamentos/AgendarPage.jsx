// Agendamento de horário (RF003, fluxo básico; campos do Quadro 25 e botões do Quadro 26 do DERS).
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { TbMapPin } from 'react-icons/tb'
import { useLocation, useNavigate, useParams } from 'react-router-dom'

import * as agendamentosApi from '../../api/agendamentos.api'
import { mensagemDeErro } from '../../api/client'
import * as quadrasApi from '../../api/quadras.api'
import IconeEsporte from '../../components/IconeEsporte'
import { CabecalhoPagina, Cartao } from '../../components/Pagina'
import SeletorDataHorario from '../../components/SeletorDataHorario'
import { classesDeInput } from '../../components/estilos'
import { Alerta, Botao, Campo, Carregando } from '../../components/ui'
import { dataExtensa, horaCurta } from '../../utils/datas'

export default function AgendarPage() {
  const { id } = useParams()
  const quadraId = Number(id)
  const navigate = useNavigate()
  const location = useLocation()
  const queryClient = useQueryClient()
  const [data, setData] = useState('')
  const [hora, setHora] = useState('')
  const [erro, setErro] = useState('')

  const voltarPara = '/quadras'

  const quadraDoEstado = location.state?.quadra
  const { data: quadras, isLoading } = useQuery({
    queryKey: ['quadras', {}],
    queryFn: () => quadrasApi.listarQuadras(),
    enabled: !quadraDoEstado,
  })
  const quadra = quadraDoEstado ?? quadras?.find((registro) => registro.id === quadraId)

  const confirmar = useMutation({
    mutationFn: () => agendamentosApi.criarAgendamento({ idQuadra: quadraId, data, horaInicio: hora }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proximo-agendamento'] })
      queryClient.invalidateQueries({ queryKey: ['meus-agendamentos'] })
      // consultar: abre "Meus agendamentos" já listando, para o usuário ver a reserva nova
      navigate('/meus-agendamentos', {
        state: { mensagem: 'Agendamento confirmado! Você receberá um e-mail com os dados da reserva.', consultar: true },
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
    return (
      <div className="mx-auto max-w-xl">
        <CabecalhoPagina voltarPara={voltarPara} titulo="Agendar horário" />
        <Alerta tipo="erro">Quadra não encontrada. Volte à consulta e selecione a quadra novamente.</Alerta>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-5xl">
      <CabecalhoPagina
        voltarPara={voltarPara}
        voltarTexto="Voltar para a consulta"
        titulo="Agendar horário"
        descricao="Escolha a data e um dos horários disponíveis para confirmar sua reserva."
      />

      <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
        <Cartao titulo="Quadra selecionada">
          <div className="space-y-4">
            <Campo label="Nome da quadra">
              <input className={classesDeInput(false)} value={`${quadra.nome} — ${quadra.esporte}`} disabled readOnly />
            </Campo>
            <div className="flex items-center gap-2 text-sm font-bold text-marca-700">
              <IconeEsporte esporte={quadra.esporte} className="size-5" />
              {quadra.esporte}
            </div>
            <p className="flex items-start gap-1.5 text-sm text-cinza-600">
              <TbMapPin aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-cinza-400" />
              <span className="min-w-0 break-words">
                {quadra.endereco} · <span className="font-semibold text-cinza-800">{quadra.bairro}</span>
              </span>
            </p>
            {quadra.descricao && <p className="border-t border-cinza-100 pt-4 text-sm text-cinza-600">{quadra.descricao}</p>}
          </div>
        </Cartao>

        <Cartao titulo="Data e horário">
          <div className="space-y-5">
            <SeletorDataHorario quadraId={quadraId} data={data} hora={hora} onMudarData={setData} onMudarHora={setHora} />

            {data && hora && (
              <p className="rounded-lg bg-marca-50 px-3.5 py-3 text-sm text-marca-800">
                Reserva para <strong>{dataExtensa(`${data}T12:00`)}</strong>, às{' '}
                <strong className="tabular-nums">{horaCurta(hora)}</strong>.
              </p>
            )}

            <Alerta tipo="erro">{erro}</Alerta>

            <div className="flex flex-col-reverse gap-3 border-t border-cinza-100 pt-5 sm:flex-row sm:justify-end">
              <Botao variante="secundario" onClick={() => navigate(voltarPara)}>
                Voltar
              </Botao>
              <Botao onClick={() => confirmar.mutate()} carregando={confirmar.isPending} disabled={!data || !hora}>
                {confirmar.isPending ? 'Confirmando…' : 'Confirmar agendamento'}
              </Botao>
            </div>
          </div>
        </Cartao>
      </div>
    </div>
  )
}
