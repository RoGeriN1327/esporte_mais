from fastapi import APIRouter, status

from app.core.deps import AdminLogado, SessaoDb
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
    _admin: AdminLogado,
    db: SessaoDb,
    esporte: str | None = None,
    nome: str | None = None,
    bairro: str | None = None,
) -> list[QuadraAdminOut]:
    return QuadraService(db).listar_para_gestao(esporte=esporte, nome=nome, bairro=bairro)


@router.post(
    "",
    response_model=list[QuadraAdminOut],
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar quadra",
    description="Cadastra a quadra com a grade de horários. A seleção "
    "de múltiplos esportes gera um registro independente por esporte.",
)
def cadastrar_quadra(
    dados: QuadraAdminCreate, _admin: AdminLogado, db: SessaoDb
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
    quadra_id: int, dados: QuadraAdminUpdate, _admin: AdminLogado, db: SessaoDb
) -> QuadraAdminOut:
    return QuadraService(db).editar(quadra_id, dados)


@router.post(
    "/{quadra_id}/desativar",
    response_model=MensagemResponse,
    summary="Desativar quadra",
    description="Desativa a quadra, impedindo novos agendamentos. Agendamentos "
    "existentes não são afetados.",
)
def desativar_quadra(quadra_id: int, _admin: AdminLogado, db: SessaoDb) -> MensagemResponse:
    QuadraService(db).desativar(quadra_id)
    return MensagemResponse(mensagem="Quadra desativada com sucesso.")
