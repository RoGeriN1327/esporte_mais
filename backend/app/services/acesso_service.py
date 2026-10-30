"""Registro de acessos ao sistema: telas abertas e logins (com sucesso ou recusados).

Grava em sessão de banco própria e nunca lança exceção: uma falha aqui não pode
atrapalhar a requisição do usuário. Robôs e ferramentas automáticas (monitor de
disponibilidade, rotina que mantém a API acordada, curl, crawlers) são ignorados,
assim como a rota /health, que não passa por aqui.
"""

import logging

from fastapi import Request

from app.core.database import SessionLocal
from app.core.rate_limit import ip_do_cliente
from app.repositories import AcessoRepository
from app.utils.user_agent import descrever, eh_robo

logger = logging.getLogger("esporte_mais.acesso")

EVENTO_PAGINA = "pagina"
EVENTO_LOGIN = "login"
EVENTO_LOGIN_RECUSADO = "login_recusado"

# Só as telas de entrada no sistema: registrar todas geraria dados demais.
# Manter igual a TELAS_REGISTRADAS em frontend/src/api/acessos.api.js.
TELAS_REGISTRADAS = frozenset({"/", "/sobre"})


def _cortar(valor: str | None, tamanho: int) -> str | None:
    valor = (valor or "").strip()
    return valor[:tamanho] or None


class AcessoService:
    def registrar(
        self,
        request: Request,
        evento: str,
        *,
        caminho: str | None = None,
        id_visitante: str | None = None,
        referencia: str | None = None,
        tipo_usuario: str | None = None,
        usuario_id: int | None = None,
        email: str | None = None,
    ) -> bool:
        """Retorna True se o acesso foi gravado (False para robôs ou em caso de falha)."""
        try:
            user_agent = request.headers.get("user-agent", "")
            if eh_robo(user_agent):
                return False
            dispositivo = descrever(user_agent)
            with SessionLocal() as db:
                AcessoRepository(db).registrar(
                    evento=evento,
                    caminho=_cortar(caminho, 255),
                    ip=ip_do_cliente(request)[:45],
                    pais=_cortar(request.headers.get("cf-ipcountry"), 2),
                    navegador=dispositivo.navegador,
                    sistema=dispositivo.sistema,
                    tipo_dispositivo=dispositivo.tipo_dispositivo,
                    dispositivo=dispositivo.dispositivo,
                    user_agent=user_agent[:500],
                    id_visitante=_cortar(id_visitante, 64),
                    referencia=_cortar(referencia, 255),
                    tipo_usuario=tipo_usuario,
                    usuario_id=usuario_id,
                    email=_cortar(email, 255),
                )
                db.commit()
            return True
        except Exception:
            logger.exception("Falha ao registrar acesso (%s)", evento)
            return False
