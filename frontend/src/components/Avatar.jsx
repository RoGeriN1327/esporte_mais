// Círculo com as iniciais da pessoa (cabeçalho e listas de usuários).
import { iniciaisDe } from '../utils/texto'

const TAMANHOS = { pequeno: 'size-8 text-xs', medio: 'size-11 text-sm' }

export default function Avatar({ nome, tamanho = 'pequeno', apagado = false }) {
  return (
    <span
      aria-hidden="true"
      className={`grid shrink-0 place-items-center rounded-full font-extrabold ${TAMANHOS[tamanho]} ${
        apagado ? 'bg-cinza-200 text-cinza-500' : 'bg-marca-600 text-white'
      }`}
    >
      {iniciaisDe(nome)}
    </span>
  )
}
