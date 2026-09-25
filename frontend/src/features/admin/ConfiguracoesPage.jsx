import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'

import * as adminApi from '../../api/admin.api'
import { mensagemDeErro } from '../../api/client'
import { Alerta, Botao, Campo, Carregando, classesDeInput } from '../../components/ui'

export default function ConfiguracoesPage() {
  const queryClient = useQueryClient()
  const [prazoCancelamento, setPrazoCancelamento] = useState('')
  const [antecedenciaLembrete, setAntecedenciaLembrete] = useState('')
  const [mensagem, setMensagem] = useState('')
  const [erro, setErro] = useState('')

  const { data: configuracoes, isLoading } = useQuery({
    queryKey: ['configuracoes'],
    queryFn: adminApi.obterConfiguracoes,
  })

  useEffect(() => {
    if (configuracoes) {
      setPrazoCancelamento(String(configuracoes.cancelamento_antecedencia_minima_horas))
      setAntecedenciaLembrete(String(configuracoes.lembrete_antecedencia_horas))
    }
  }, [configuracoes])

  const salvar = useMutation({
    mutationFn: () =>
      adminApi.atualizarConfiguracoes({
        cancelamento_antecedencia_minima_horas: Number(prazoCancelamento),
        lembrete_antecedencia_horas: Number(antecedenciaLembrete),
      }),
    onSuccess: () => {
      setErro('')
      setMensagem('Configurações atualizadas com sucesso.')
      queryClient.invalidateQueries({ queryKey: ['configuracoes'] })
    },
    onError: (excecao) => {
      setMensagem('')
      setErro(mensagemDeErro(excecao))
    },
  })

  if (isLoading) return <Carregando />

  return (
    <div className="mx-auto max-w-xl space-y-4">
      <h1 className="text-2xl font-bold text-gray-800">Configurações</h1>

      <div className="space-y-4 rounded-xl bg-white p-6 shadow">
        <Campo label="Prazo mínimo de cancelamento (horas de antecedência)">
          <input
            type="number"
            min={0}
            max={168}
            className={classesDeInput(false)}
            value={prazoCancelamento}
            onChange={(evento) => setPrazoCancelamento(evento.target.value)}
          />
        </Campo>
        <p className="-mt-2 text-xs text-gray-500">
          O cidadão só pode cancelar seu agendamento com esta antecedência mínima. A administração
          pode cancelar a qualquer momento.
        </p>

        <Campo label="Antecedência do lembrete automático (horas)">
          <input
            type="number"
            min={1}
            max={168}
            className={classesDeInput(false)}
            value={antecedenciaLembrete}
            onChange={(evento) => setAntecedenciaLembrete(evento.target.value)}
          />
        </Campo>
        <p className="-mt-2 text-xs text-gray-500">
          O sistema envia um e-mail de lembrete ao cidadão quando faltam menos horas do que o
          valor configurado para o horário do agendamento.
        </p>

        <Alerta tipo="sucesso">{mensagem}</Alerta>
        <Alerta tipo="erro">{erro}</Alerta>

        <div className="flex justify-end">
          <Botao onClick={() => salvar.mutate()} carregando={salvar.isPending}>
            Salvar alterações
          </Botao>
        </div>
      </div>
    </div>
  )
}
