// Unitários — Modal (src/components/ui.jsx).
// Digitar num campo do modal re-renderiza a página dona dele, que passa um onFechar novo a
// cada render. O foco tem de continuar no campo (antes voltava para a caixa do diálogo e só
// o primeiro caractere entrava, ex.: CPF no "Novo agendamento" do painel administrativo).
import { act, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import { Modal } from './ui'

globalThis.IS_REACT_ACT_ENVIRONMENT = true

function Pagina() {
  const [aberto, setAberto] = useState(true)
  const [valor, setValor] = useState('')
  return (
    <>
      <span data-testid="fechado">{aberto ? 'não' : 'sim'}</span>
      <Modal aberto={aberto} titulo="Novo agendamento" onFechar={() => setAberto(false)}>
        <input aria-label="CPF" value={valor} onChange={(evento) => setValor(evento.target.value)} />
      </Modal>
    </>
  )
}

function digitar(campo, texto) {
  const definirValor = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set
  for (const caractere of texto) {
    act(() => {
      definirValor.call(campo, campo.value + caractere)
      campo.dispatchEvent(new Event('input', { bubbles: true }))
    })
  }
}

describe('Modal', () => {
  let container
  let raiz
  beforeEach(() => {
    container = document.createElement('div')
    document.body.appendChild(container)
    raiz = createRoot(container)
    act(() => raiz.render(<Pagina />))
  })
  afterEach(() => {
    act(() => raiz.unmount())
    container.remove()
  })

  it('foca a caixa do diálogo ao abrir', () => {
    expect(document.activeElement.getAttribute('role')).toBe('dialog')
  })

  it('mantém o foco no campo enquanto se digita', () => {
    const campo = container.querySelector('input')
    act(() => campo.focus())
    digitar(campo, '52998224725')
    expect(campo.value).toBe('52998224725')
    expect(document.activeElement).toBe(campo)
  })

  it('Esc fecha usando o onFechar mais recente', () => {
    const campo = container.querySelector('input')
    act(() => campo.focus())
    digitar(campo, '1')
    act(() => document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' })))
    expect(container.querySelector('[data-testid="fechado"]').textContent).toBe('sim')
    expect(container.querySelector('[role="dialog"]')).toBeNull()
  })
})
