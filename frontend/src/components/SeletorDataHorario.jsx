import { useQuery } from '@tanstack/react-query'

import * as quadrasApi from '../api/quadras.api'
import { hojeISO, horaCurta } from '../utils/datas'
import { Campo, Spinner, classesDeInput } from './ui'

export default function SeletorDataHorario({ quadraId, data, hora, onMudarData, onMudarHora }) {
  const { data: disponibilidade, isFetching } = useQuery({
    queryKey: ['horarios-disponiveis', quadraId, data],
    queryFn: () => quadrasApi.horariosDisponiveis(quadraId, data),
    enabled: Boolean(quadraId && data),
  })
  const horarios = disponibilidade?.horarios || []

  return (
    <div className="space-y-4">
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

      {data && (
        <div>
          <span className="mb-2 block text-sm font-medium text-gray-700">Horários disponíveis</span>
          {isFetching ? (
            <Spinner />
          ) : horarios.length === 0 ? (
            <p className="text-sm text-gray-500">
              Nenhum horário disponível nesta data. Escolha outra data.
            </p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {horarios.map((horario) => (
                <button
                  key={horario}
                  type="button"
                  className={`rounded-lg border px-3 py-1.5 text-sm font-medium transition ${
                    hora === horario
                      ? 'border-emerald-600 bg-emerald-600 text-white'
                      : 'border-gray-300 bg-white text-gray-700 hover:border-emerald-500'
                  }`}
                  onClick={() => onMudarHora(horario)}
                >
                  {horaCurta(horario)}
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
