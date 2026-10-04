// Configurações do sistema (só Gestor): prazo mínimo de cancelamento pelo cidadão (RN004)
// e antecedência do lembrete automático por e-mail (RF005).
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { TbBellRinging, TbHourglass } from 'react-icons/tb'

import * as adminApi from '../../api/admin.api'
import { mensagemDeErro } from '../../api/client'
import { BarraAcoes, CabecalhoPagina, Cartao } from '../../components/Pagina'
import { classesDeInput } from '../../components/estilos'
import { Alerta, Botao, Carregando } from '../../components/ui'

export default function ConfiguracoesPage() {
  const { data: configuracoes, isLoading, error } = useQuery({
    queryKey: ['configuracoes'],
    queryFn: adminApi.obterConfiguracoes,
  })

  return (
    <div className="mx-auto max-w-2xl">
      <CabecalhoPagina
        voltarPara="/admin"
        voltarTexto="Início"
        titulo="Configurações"
        descricao="Regras de prazo aplicadas aos agendamentos de todas as quadras."
      />
      {isLoading ? (
        <Carregando />
      ) : error ? (
        <Alerta tipo="erro">{mensagemDeErro(error)}</Alerta>
      ) : (
        // O formulário só é montado com os dados carregados, já com os valores iniciais.
        <FormularioConfiguracoes configuracoes={configuracoes} />
      )}
    </div>
  )
}

function CampoHoras({ id, Icone, titulo, descricao, valor, onMudar, min, max }) {
  return (
    <div className="flex flex-col gap-4 py-6 first:pt-0 last:pb-0 sm:flex-row sm:items-start sm:justify-between">
      <div className="flex gap-3.5">
        <span className="grid size-10 shrink-0 place-items-center rounded-lg bg-marca-50 text-marca-700">
          <Icone aria-hidden="true" className="size-5" />
        </span>
        <div>
          <label htmlFor={id} className="font-extrabold text-cinza-900">
            {titulo}
          </label>
          <p id={`${id}-descricao`} className="mt-1 max-w-sm text-sm text-cinza-600">
            {descricao}
          </p>
        </div>
      </div>
      <div className="relative w-full shrink-0 sm:w-36">
        <input
          id={id}
          type="number"
          inputMode="numeric"
          min={min}
          max={max}
          aria-describedby={`${id}-descricao`}
          className={`${classesDeInput(false)} pr-16 text-right font-bold tabular-nums`}
          value={valor}
          onChange={(evento) => onMudar(evento.target.value)}
        />
        <span aria-hidden="true" className="pointer-events-none absolute inset-y-0 right-3.5 flex items-center text-sm font-semibold text-cinza-500">
          horas
        </span>
      </div>
    </div>
  )
}

function FormularioConfiguracoes({ configuracoes }) {
  const queryClient = useQueryClient()
  const [prazoCancelamento, setPrazoCancelamento] = useState(String(configuracoes.cancelamento_antecedencia_minima_horas))
  const [antecedenciaLembrete, setAntecedenciaLembrete] = useState(String(configuracoes.lembrete_antecedencia_horas))
  const [mensagem, setMensagem] = useState('')
  const [erro, setErro] = useState('')

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

  return (
    <form
      noValidate
      onSubmit={(evento) => {
        evento.preventDefault()
        salvar.mutate()
      }}
      className="space-y-6"
    >
      <Cartao>
        <div className="divide-y divide-cinza-100">
          <CampoHoras
            id="config-cancelamento"
            Icone={TbHourglass}
            titulo="Prazo mínimo de cancelamento"
            descricao="O cidadão só pode cancelar o próprio agendamento com esta antecedência. A administração pode cancelar a qualquer momento. De 0 a 168 horas."
            valor={prazoCancelamento}
            onMudar={setPrazoCancelamento}
            min={0}
            max={168}
          />
          <CampoHoras
            id="config-lembrete"
            Icone={TbBellRinging}
            titulo="Antecedência do lembrete"
            descricao="O cidadão recebe um e-mail de lembrete quando faltar este tempo para o horário agendado. De 1 a 168 horas."
            valor={antecedenciaLembrete}
            onMudar={setAntecedenciaLembrete}
            min={1}
            max={168}
          />
        </div>
      </Cartao>

      <Alerta tipo="sucesso">{mensagem}</Alerta>
      <Alerta tipo="erro">{erro}</Alerta>

      <BarraAcoes>
        <Botao type="submit" carregando={salvar.isPending}>
          {salvar.isPending ? 'Salvando…' : 'Salvar alterações'}
        </Botao>
      </BarraAcoes>
    </form>
  )
}
