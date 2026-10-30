"""Leitura do user-agent: navegador, sistema, dispositivo e detecção de robôs."""

import re
from dataclasses import dataclass

from user_agents import parse

# Além dos robôs que a biblioteca já reconhece (Googlebot, UptimeRobot...), descarta
# ferramentas e navegadores automatizados, que não são pessoas usando o sistema.
_ROBOS = re.compile(
    r"bot|crawl|spider|slurp|monitor|uptime|pingdom|curl|wget|python|httpx|aiohttp|"
    r"go-http-client|java/|okhttp|axios/|node-fetch|undici|postman|insomnia|"
    r"headless|phantomjs|puppeteer|playwright|lighthouse|vercel|facebookexternalhit|"
    r"whatsapp|telegrambot|preview",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class DadosDoDispositivo:
    navegador: str
    sistema: str
    tipo_dispositivo: str
    dispositivo: str | None


def eh_robo(user_agent: str) -> bool:
    if not user_agent.strip():
        return True
    return parse(user_agent).is_bot or bool(_ROBOS.search(user_agent))


def _com_versao(nome: str, versao: str) -> str:
    return f"{nome} {versao}".strip() if nome and nome != "Other" else "Desconhecido"


def descrever(user_agent: str) -> DadosDoDispositivo:
    ua = parse(user_agent)
    if ua.is_tablet:
        tipo = "Tablet"
    elif ua.is_mobile:
        tipo = "Celular"
    elif ua.is_pc:
        tipo = "Computador"
    else:
        tipo = "Outro"
    marca_modelo = " ".join(p for p in (ua.device.brand, ua.device.model) if p and p != "Other")
    return DadosDoDispositivo(
        navegador=_com_versao(ua.browser.family, ua.browser.version_string)[:60],
        sistema=_com_versao(ua.os.family, ua.os.version_string)[:60],
        tipo_dispositivo=tipo,
        dispositivo=(marca_modelo or None) and marca_modelo[:80],
    )
