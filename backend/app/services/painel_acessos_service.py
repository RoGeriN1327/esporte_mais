"""Painel secreto de consulta dos acessos (ver app.controllers.painel_acessos_controller).

Fica fora do sistema: só abre com o caminho e a chave definidos nas variáveis
PAINEL_ACESSOS_CAMINHO e PAINEL_ACESSOS_CHAVE. Caminho errado, chave errada, IP
bloqueado ou painel desligado têm a mesma resposta (404), para não dar pistas.
"""

import hmac
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories import AcessoRepository, SegurancaRepository

# Abaixo disso o caminho ou a chave seriam fáceis de adivinhar: o painel fica desligado.
TAMANHO_MINIMO = 16
LIMITE_DE_LINHAS = 1000
# Marca as chaves erradas na tabela de falhas de login (que alimenta o bloqueio de IP).
MARCA_FALHA = "(chave do painel de acessos)"
JANELA_FALHAS = timedelta(hours=24)


def _iguais(recebido: str, esperado: str) -> bool:
    """Comparação em tempo constante: o tempo da resposta não revela acertos parciais."""
    return hmac.compare_digest(recebido.encode(), esperado.encode())


def painel_ligado() -> bool:
    return (
        len(settings.PAINEL_ACESSOS_CAMINHO) >= TAMANHO_MINIMO
        and len(settings.PAINEL_ACESSOS_CHAVE) >= TAMANHO_MINIMO
    )


class PainelAcessosService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.seguranca = SegurancaRepository(db)
        self.acessos = AcessoRepository(db)

    def caminho_valido(self, caminho: str, ip: str) -> bool:
        return (
            painel_ligado()
            and _iguais(caminho, settings.PAINEL_ACESSOS_CAMINHO)
            and not self.seguranca.ip_esta_bloqueado(ip)
        )

    def chave_valida(self, chave: str, ip: str) -> bool:
        """Confere a chave; a cada erro guarda a falha e, no limite, bloqueia o IP."""
        if _iguais(chave, settings.PAINEL_ACESSOS_CHAVE):
            return True
        self.seguranca.registrar_falha_login(ip, MARCA_FALHA)
        erros = self.seguranca.contar_falhas(ip, MARCA_FALHA, datetime.now(UTC) - JANELA_FALHAS)
        if erros >= settings.PAINEL_MAX_CHAVES_ERRADAS:
            self.seguranca.bloquear_ip(
                ip, f"{erros} tentativas inválidas de acesso restrito em 24h"
            )
        self.db.commit()
        return False

    def consultar(
        self, desde: date | None, ate: date | None, evento: str | None, so_logados: bool
    ) -> dict:
        fuso = ZoneInfo(settings.TIMEZONE)
        filtros = {
            "desde": datetime.combine(desde, time(), fuso) if desde else None,
            # "até" inclui o dia inteiro
            "ate": datetime.combine(ate + timedelta(days=1), time(), fuso) if ate else None,
            "evento": evento,
            "so_logados": so_logados,
        }
        return {
            "resumo": self.acessos.resumir(**filtros),
            "usuarios": self.acessos.resumir_por_usuario(**filtros),
            "acessos": self.acessos.listar(limite=LIMITE_DE_LINHAS, **filtros),
            "limite": LIMITE_DE_LINHAS,
        }
