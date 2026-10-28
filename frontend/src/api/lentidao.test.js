// Unitários — monitor de requisições lentas (src/api/lentidao.js).
// O aviso de cold start deve aparecer só quando uma requisição passa de 3 segundos
// e sumir quando todas as requisições lentas terminam.
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { LIMITE_MS, assinar, finalizar, haRequisicaoLenta, iniciar, monitorar } from './lentidao'

describe('monitor de lentidão', () => {
  let ids
  beforeEach(() => {
    vi.useFakeTimers()
    ids = []
  })
  afterEach(() => {
    ids.forEach(finalizar)
    vi.useRealTimers()
  })

  function nova() {
    const id = iniciar()
    ids.push(id)
    return id
  }

  it('requisição rápida nunca aciona o aviso', () => {
    const id = nova()
    vi.advanceTimersByTime(LIMITE_MS - 1)
    finalizar(id)
    vi.advanceTimersByTime(LIMITE_MS)
    expect(haRequisicaoLenta()).toBe(false)
  })

  it('aviso aparece aos 3 segundos e some quando a requisição termina', () => {
    const id = nova()
    vi.advanceTimersByTime(LIMITE_MS - 1)
    expect(haRequisicaoLenta()).toBe(false)
    vi.advanceTimersByTime(1)
    expect(haRequisicaoLenta()).toBe(true)
    finalizar(id)
    expect(haRequisicaoLenta()).toBe(false)
  })

  it('com várias requisições lentas, o aviso só some quando a última termina', () => {
    const primeira = nova()
    const segunda = nova()
    vi.advanceTimersByTime(LIMITE_MS)
    finalizar(primeira)
    expect(haRequisicaoLenta()).toBe(true)
    finalizar(segunda)
    expect(haRequisicaoLenta()).toBe(false)
  })

  it('avisa os ouvintes só quando o estado muda', () => {
    const ouvinte = vi.fn()
    const cancelar = assinar(ouvinte)
    const primeira = nova()
    const segunda = nova()
    vi.advanceTimersByTime(LIMITE_MS)
    expect(ouvinte).toHaveBeenCalledTimes(1)
    finalizar(primeira)
    finalizar(segunda)
    expect(ouvinte).toHaveBeenCalledTimes(2)
    cancelar()
  })

  it('monitorar() cobre promessas fora do cliente api, inclusive com erro', async () => {
    let rejeitar
    const promessa = monitorar(new Promise((_, r) => (rejeitar = r)))
    vi.advanceTimersByTime(LIMITE_MS)
    expect(haRequisicaoLenta()).toBe(true)
    rejeitar(new Error('falhou'))
    await expect(promessa).rejects.toThrow('falhou')
    expect(haRequisicaoLenta()).toBe(false)
  })
})
