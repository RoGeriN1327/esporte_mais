// Unitários — CPF no frontend (src/utils/cpf.js).
// A validação do navegador precisa concordar com a do backend (app/utils/cpf.py):
// os mesmos casos usados nos testes do backend são repetidos aqui.
import { describe, expect, it } from 'vitest'

import { cpfValido, mascararCpf, somenteDigitos } from './cpf'

describe('somenteDigitos', () => {
  it('remove máscara e caracteres não numéricos, tratando valor ausente como vazio', () => {
    expect(somenteDigitos('529.982.247-25')).toBe('52998224725')
    expect(somenteDigitos(' 529 982/247a25 ')).toBe('52998224725')
    for (const vazio of [undefined, null, '']) expect(somenteDigitos(vazio)).toBe('')
  })
})

describe('mascararCpf', () => {
  it('aplica a máscara progressivamente durante a digitação', () => {
    const casos = [
      ['5', '5'],
      ['529', '529'],
      ['5299', '529.9'],
      ['529982', '529.982'],
      ['5299822', '529.982.2'],
      ['529982247', '529.982.247'],
      ['5299822472', '529.982.247-2'],
      ['52998224725', '529.982.247-25'],
    ]
    for (const [digitado, esperado] of casos) expect(mascararCpf(digitado), digitado).toBe(esperado)
  })

  it('ignora dígitos além do 11º e reaplica a máscara sobre valor já formatado', () => {
    expect(mascararCpf('529982247259999')).toBe('529.982.247-25')
    expect(mascararCpf('529.982.247-25')).toBe('529.982.247-25')
    expect(mascararCpf('529 982 247 25')).toBe('529.982.247-25')
  })
})

describe('cpfValido', () => {
  it('aceita CPFs válidos, com ou sem máscara', () => {
    for (const cpf of ['52998224725', '11144477735', '39053344705', '529.982.247-25']) {
      expect(cpfValido(cpf), cpf).toBe(true)
    }
  })

  it('rejeita dígitos verificadores errados', () => {
    expect(cpfValido('52998224735')).toBe(false) // 1º dígito
    expect(cpfValido('52998224726')).toBe(false) // 2º dígito
  })

  it('rejeita sequências repetidas', () => {
    for (const digito of '0123456789') expect(cpfValido(digito.repeat(11)), digito).toBe(false)
  })

  it('trata resto 10 como dígito 0 (mesmos casos do backend)', () => {
    expect(cpfValido('10000000108')).toBe(true)
    expect(cpfValido('10000000118')).toBe(false)
    expect(cpfValido('10000002810')).toBe(true)
    expect(cpfValido('10000002811')).toBe(false)
  })

  it('rejeita quantidade de dígitos diferente de 11', () => {
    for (const cpf of ['5299822472', '529982247250', '', undefined]) {
      expect(cpfValido(cpf), String(cpf)).toBe(false)
    }
  })
})
