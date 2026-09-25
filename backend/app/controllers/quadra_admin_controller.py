from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import UsuarioAtual, require_admin
from app.schemas.auth import MensagemResponse
from app.schemas.quadra import QuadraAdminCreate, QuadraAdminOut, QuadraAdminUpdate
from app.services.quadra_service import QuadraService

router = APIRouter(prefix="/admin/quadras", tags=["Gestão de Quadras"])

@router.get(
    "",
    response_model=list[QuadraAdminOut],
    summary="Listar quadras (administração)",
    description="Lista todas as quadras, ativas e desativadas, com filtros de "
    "esporte, nome e bairro e a grade de horários de cada registro.",
)
def listar_quadras_admin(
    esporte: str | None = Query(default=None),
    nome: str | None = Query(default=None),
    bairro: str | None = Query(default=None),
    _admin: UsuarioAtual = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[QuadraAdminOut]:
    return QuadraService(db).listar_para_gestao(esporte=esporte, nome=nome, bairro=bairro)

@router.post(
    "",
    response_model=list[QuadraAdminOut],
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar quadra",
    description="Cadastra a quadra com a grade de horários (Quadro 33). A seleção "
    "de múltiplos esportes gera um registro independente por esporte.",
)
def cadastrar_quadra(
    dados: QuadraAdminCreate,
    _admin: UsuarioAtual = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[QuadraAdminOut]:
    return QuadraService(db).cadastrar(dados)

@router.put(
    "/{quadra_id}",
    response_model=QuadraAdminOut,
    summary="Editar quadra",
    description="Edita os dados e a grade de horários de um registro de quadra "
    "(um esporte por registro). Agendamentos existentes não são afetados.",
)
def editar_quadra(
    quadra_id: int,
    dados: QuadraAdminUpdate,
    _admin: UsuarioAtual = Depends(require_admin),
    db: Session = Depends(get_db),
) -> QuadraAdminOut:
    return QuadraService(db).editar(quadra_id, dados)

@router.post(
    "/{quadra_id}/desativar",
    response_model=MensagemResponse,
    summary="Desativar quadra",
    description="Desativa a quadra, impedindo novos agendamentos. Agendamentos "
    "existentes não são afetados.",
)
def desativar_quadra(
    quadra_id: int,
    _admin: UsuarioAtual = Depends(require_admin),
    db: Session = Depends(get_db),
) -> MensagemResponse:
    QuadraService(db).desativar(quadra_id)
    return MensagemResponse(mensagem="Quadra desativada com sucesso.")
