"""Transforma um template de e-mail + dados em texto puro e HTML.

Cada e-mail tem dois arquivos em app/emails/templates/: <nome>.txt e <nome>.html, ambos
herdando do layout base (base.txt / base.html). O HTML usa escape automático, para que
dados vindos do usuário (nome, nome da quadra...) nunca sejam interpretados como HTML.
"""

from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from app.core.config import settings

_PASTA_TEMPLATES = Path(__file__).parent / "templates"

_ambiente = Environment(
    loader=FileSystemLoader(_PASTA_TEMPLATES),
    autoescape=select_autoescape(enabled_extensions=("html",), default_for_string=False),
    undefined=StrictUndefined,  # variável faltando no contexto vira erro, não texto vazio
    trim_blocks=True,
    lstrip_blocks=True,
    keep_trailing_newline=True,
)


@dataclass(frozen=True)
class EmailRenderizado:
    texto: str
    html: str


def _globais() -> dict:
    """Dados disponíveis em todos os templates (marca, links e rodapé)."""
    return {
        "url_sistema": settings.FRONTEND_URL,
        "url_logo": f"{settings.FRONTEND_URL}/marca/logo-email.png",
    }


def renderizar(template: str, /, **contexto) -> EmailRenderizado:
    """Renderiza <template>.txt e <template>.html com o mesmo contexto."""
    dados = {**_globais(), **contexto}
    texto = _ambiente.get_template(f"{template}.txt").render(dados).strip() + "\n"
    html = _ambiente.get_template(f"{template}.html").render(dados)
    return EmailRenderizado(texto=texto, html=html)
