// Registro de acessos à página inicial e à página Sobre (ver backend
// app/services/acesso_service.py). As demais telas não são registradas.
//
// Só vai o caminho da tela, nunca a query string (o link de redefinição de senha
// leva o token nela). Falhas são ignoradas: o registro nunca atrapalha o uso.
import api from './client'

const CHAVE_VISITANTE = 'esporte_visitante'

// Manter igual a TELAS_REGISTRADAS no backend (app/services/acesso_service.py).
export const TELAS_REGISTRADAS = new Set(['/', '/sobre'])

// Id aleatório do navegador, para agrupar as visitas do mesmo aparelho.
// localStorage pode estar bloqueado (aba anônima, cookies desligados): segue sem id.
function idDoVisitante() {
  try {
    let id = localStorage.getItem(CHAVE_VISITANTE)
    if (!id) {
      id = crypto.randomUUID()
      localStorage.setItem(CHAVE_VISITANTE, id)
    }
    return id
  } catch {
    return null
  }
}

// Página de origem só quando veio de outro site, sem query string.
function origemExterna() {
  try {
    const origem = new URL(document.referrer)
    if (origem.origin === window.location.origin) return null
    return `${origem.origin}${origem.pathname}`.slice(0, 255)
  } catch {
    return null
  }
}

export function registrarAcesso(caminho) {
  api
    .post(
      '/acessos',
      { caminho: caminho.slice(0, 255), id_visitante: idDoVisitante(), referencia: origemExterna() },
      { semAvisoDeLentidao: true },
    )
    .catch(() => {})
}
