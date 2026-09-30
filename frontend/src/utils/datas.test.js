// Unitários — formatação de datas (src/utils/datas.js).
// A API devolve instantes em UTC (ex.: "2030-03-05T12:00:00Z"); a tela deve
// exibi-los no horário de Brasília. O fuso é fixado em vite.config.js.
import { afterEach, describe, expect, it, vi } from 'vitest'

import {
  DIAS_SEMANA,
  formatarData,
  formatarDataHora,
  formatarHora,
  hojeISO,
  horaCurta,
} from './datas'

describe('formatação de data/hora vinda da API', () => {
  it('converte o instante UTC para data e hora de Brasília (UTC-3)', () => {
    expect(formatarData('2030-03-05T12:00:00Z')).toBe('05/03/2030')
    expect(formatarHora('2030-03-05T12:00:00Z')).toBe('09:00')
    expect(formatarDataHora('2030-03-05T09:00:00-03:00')).toBe('05/03/2030 09:00')
  })

  it('agendamento às 23h de Brasília continua no mesmo dia, embora já seja o dia seguinte em UTC', () => {
    // 23:00 de 05/03 em Brasília = 02:00 de 06/03 em UTC.
    expect(formatarData('2030-03-06T02:00:00Z')).toBe('05/03/2030')
    expect(formatarHora('2030-03-06T02:00:00Z')).toBe('23:00')
  })

  it('retorna texto vazio quando não há valor', () => {
    for (const formatar of [formatarData, formatarHora, formatarDataHora, horaCurta]) {
      for (const vazio of [null, undefined, '']) expect(formatar(vazio)).toBe('')
    }
  })
})

describe('horaCurta', () => {
  it('reduz "HH:MM:SS" da API para "HH:MM"', () => {
    expect(horaCurta('09:00:00')).toBe('09:00')
    expect(horaCurta('18:30')).toBe('18:30')
  })
})

describe('hojeISO', () => {
  afterEach(() => {
    vi.useRealTimers()
  })

  it('usa a data local (não a UTC) no formato aaaa-mm-dd', () => {
    vi.useFakeTimers()
    // 23:30 de 04/03 em Brasília já é 05/03 em UTC; "hoje" deve ser 04/03, senão o
    // calendário bloquearia o dia atual para agendamentos no fim da noite.
    vi.setSystemTime(new Date('2030-03-05T02:30:00Z'))
    expect(hojeISO()).toBe('2030-03-04')
    vi.setSystemTime(new Date('2030-12-31T15:00:00Z'))
    expect(hojeISO()).toBe('2030-12-31')
  })
})

describe('DIAS_SEMANA', () => {
  it('segue a numeração da API: 0 = segunda-feira ... 6 = domingo', () => {
    expect(DIAS_SEMANA).toHaveLength(7)
    expect(DIAS_SEMANA[0]).toBe('Segunda-feira')
    expect(DIAS_SEMANA[6]).toBe('Domingo')
  })
})
