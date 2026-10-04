// Escolha de data + horário disponível (agendamento e renovação; Quadros 25 e 29 do DERS).
import { useQuery } from '@tanstack/react-query'
import { TbCalendarOff, TbClockHour4 } from 'react-icons/tb'

import * as quadrasApi from '../api/quadras.api'
import { hojeISO, horaCurta } from '../utils/datas'
import { classesDeInput } from './estilos'
import { Campo, Spinner } from './ui'

export default function SeletorDataHorario({ quadraId, data, hora, onMudarData, onMudarHora }) {
  const { data: disponibilidade, isFetching } = useQuery({
    queryKey: ['horarios-disponiveis', quadraId, data],
    queryFn: () => quadrasApi.horariosDisponiveis(quadraId, data),
    enabled: Boolean(quadraId && data),
  })
  const horarios = disponibilidade?.horarios ?? []

  let conteudoHorarios
  if (!data) {
    conteudoHorarios = (
      <p className="flex items-center gap-2 rounded-lg bg-cinza-50 px-3.5 py-3 text-sm text-cinza-600">
        <TbClockHour4 aria-hidden="true" className="size-5 shrink-0 text-cinza-400" />
        Selecione uma data para ver os horários disponíveis.
      </p>
    )
  } else if (isFetching) {
    conteudoHorarios = (
      <p role="status" className="flex items-center gap-2 py-3 text-sm text-cinza-600">
        <Spinner pequeno />
        Carregando horários…
      </p>
    )
  } else if (horarios.length === 0) {
    conteudoHorarios = (
      <p role="status" className="flex items-center gap-2 rounded-lg bg-aviso-50 px-3.5 py-3 text-sm font-medium text-aviso-700">
        <TbCalendarOff aria-hidden="true" className="size-5 shrink-0" />
        Nenhum horário disponível nesta data. Escolha outra data.
      </p>
    )
  } else {
    conteudoHorarios = (
      <div className="grid grid-cols-3 gap-2 sm:grid-cols-4">
        {horarios.map((horario) => {
          const selecionado = hora === horario
          return (
            <button
              key={horario}
              type="button"
              aria-pressed={selecionado}
              onClick={() => onMudarHora(horario)}
              className={`h-11 rounded-lg border text-[15px] font-bold tabular-nums transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marca-600 ${
                selecionado
                  ? 'border-marca-600 bg-marca-600 text-white'
                  : 'border-cinza-300 bg-white text-cinza-800 hover:border-marca-400 hover:bg-marca-50'
              }`}
            >
              {horaCurta(horario)}
            </button>
          )
        })}
      </div>
    )
  }

  return (
    <div className="space-y-5">
      <Campo label="Data">
        <input
          type="date"
          className={classesDeInput(false)}
          min={hojeISO()}
          value={data}
          onChange={(evento) => {
            onMudarData(evento.target.value)
            onMudarHora('')
          }}
        />
      </Campo>
      <fieldset>
        <legend className="mb-1.5 text-sm font-semibold text-cinza-800">Horários disponíveis</legend>
        <div aria-live="polite">{conteudoHorarios}</div>
      </fieldset>
    </div>
  )
}
