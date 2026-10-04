// Ícone de cada modalidade cadastrável (ESPORTES_VALIDOS do backend).
import { TbBallBasketball, TbBallFootball, TbBallTennis, TbBallVolleyball, TbPlayHandball, TbTrophy } from 'react-icons/tb'

const ICONES = {
  Futebol: TbBallFootball,
  Futsal: TbBallFootball,
  Basquete: TbBallBasketball,
  Vôlei: TbBallVolleyball,
  Tênis: TbBallTennis,
  Handebol: TbPlayHandball,
}

export default function IconeEsporte({ esporte, className = 'size-5' }) {
  const Icone = ICONES[esporte] ?? TbTrophy
  return <Icone aria-hidden="true" className={className} />
}
