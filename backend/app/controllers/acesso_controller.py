from fastapi import APIRouter, Request, Response

from app.core.deps import UsuarioOpcional
from app.core.rate_limit import limiter
from app.schemas.acesso import AcessoRequest
from app.services.acesso_service import EVENTO_PAGINA, TELAS_REGISTRADAS, AcessoService

router = APIRouter(prefix="/acessos", tags=["Acessos"])


@router.post(
    "",
    status_code=204,
    summary="Registrar tela aberta",
    description="Chamado pelo front ao abrir a página inicial (/) ou a página Sobre (/sobre); "
    "outras telas são ignoradas. Grava IP, país, navegador, sistema, dispositivo e, se houver "
    "login, o usuário. Robôs e monitores são ignorados. "
    "Não exige login e nunca falha por causa do registro.",
)
@limiter.limit("60/minute")
def registrar_acesso(request: Request, dados: AcessoRequest, usuario: UsuarioOpcional) -> Response:
    if dados.caminho not in TELAS_REGISTRADAS:
        return Response(status_code=204)
    AcessoService().registrar(
        request,
        EVENTO_PAGINA,
        caminho=dados.caminho,
        id_visitante=dados.id_visitante,
        referencia=dados.referencia,
        tipo_usuario=usuario.tipo.value if usuario else None,
        usuario_id=usuario.id if usuario else None,
        email=usuario.email if usuario else None,
    )
    return Response(status_code=204)
