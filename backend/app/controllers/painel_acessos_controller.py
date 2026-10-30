"""Painel secreto de consulta dos acessos, servido pelo próprio backend.

Não aparece no site nem na documentação da API (include_in_schema=False). Ver
app.services.painel_acessos_service para as regras de caminho, chave e bloqueio.
"""

import secrets
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import HTMLResponse

from app.core.deps import SessaoDb
from app.core.rate_limit import ip_do_cliente, limiter
from app.schemas.acesso import ConsultaPainelOut, ConsultaPainelRequest
from app.services.painel_acessos_service import PainelAcessosService

router = APIRouter(prefix="/interno", include_in_schema=False)

_PAGINA = (Path(__file__).parents[1] / "paginas" / "painel_acessos.html").read_text("utf-8")


def _nao_encontrado() -> HTTPException:
    # Mesma resposta do FastAPI para uma rota que não existe.
    return HTTPException(status_code=404, detail="Not Found")


def _cabecalhos_privados(nonce: str | None = None) -> dict[str, str]:
    cabecalhos = {"Cache-Control": "no-store", "X-Robots-Tag": "noindex, nofollow"}
    if nonce:
        cabecalhos["Content-Security-Policy"] = (
            f"default-src 'none'; script-src 'nonce-{nonce}'; style-src 'nonce-{nonce}'; "
            "connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
        )
    return cabecalhos


@router.get("/{caminho}", response_class=HTMLResponse)
@limiter.limit("20/minute")
def abrir_painel(request: Request, caminho: str, db: SessaoDb) -> HTMLResponse:
    if not PainelAcessosService(db).caminho_valido(caminho, ip_do_cliente(request)):
        raise _nao_encontrado()
    nonce = secrets.token_urlsafe(16)
    return HTMLResponse(_PAGINA.replace("{{NONCE}}", nonce), headers=_cabecalhos_privados(nonce))


@router.post("/{caminho}/dados", response_model=ConsultaPainelOut)
@limiter.limit("20/minute")
def consultar_painel(
    request: Request,
    response: Response,
    caminho: str,
    dados: ConsultaPainelRequest,
    db: SessaoDb,
) -> ConsultaPainelOut:
    servico = PainelAcessosService(db)
    ip = ip_do_cliente(request)
    if not servico.caminho_valido(caminho, ip) or not servico.chave_valida(dados.chave, ip):
        raise _nao_encontrado()
    resultado = servico.consultar(dados.desde, dados.ate, dados.evento, dados.so_logados)
    response.headers.update(_cabecalhos_privados())
    return ConsultaPainelOut.model_validate(resultado, from_attributes=True)
