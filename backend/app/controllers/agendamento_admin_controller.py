from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import UsuarioAtual, require_admin
from app.models.enums import StatusAgendamento
from app.schemas.agendamento import (
    AgendamentoAdminCreate,
    AgendamentoAdminOut,
    RemarcacaoRequest,
)
from app.services.agendamento_service import AgendamentoService
from app.utils.cpf import normalizar_cpf

router = APIRouter(prefix="/admin/agendamentos", tags=["Painel de Agendamentos"])

@router.get(
    "",
    response_model=list[AgendamentoAdminOut],
    summary="Painel consolidado de agendamentos",
    description="Todos os agendamentos do sistema, com filtros de data, quadra, "
    "esporte, status e cidadão (nome ou CPF). Acessível a Gestor e Operador.",
)
def painel_agendamentos(
    data: date | None = Query(default=None),
    nome_quadra: str | None = Query(default=None),
    esporte: str | None = Query(default=None),
    status_agendamento: StatusAgendamento | None = Query(default=None, alias="status"),
    cpf_usuario: str | None = Query(default=None),
    nome_usuario: str | None = Query(default=None),
    _admin: UsuarioAtual = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[AgendamentoAdminOut]:
    agendamentos = AgendamentoService(db).listar_consolidado(
        dia=data,
        nome_quadra=nome_quadra,
        esporte=esporte,
        status=status_agendamento,
        cpf_usuario=normalizar_cpf(cpf_usuario) if cpf_usuario else None,
        nome_usuario=nome_usuario,
    )
    return [AgendamentoAdminOut.de_modelo(a) for a in agendamentos]

@router.post(
    "",
    response_model=AgendamentoAdminOut,
    status_code=status.HTTP_201_CREATED,
    summary="Realizar agendamento para um cidadão",
    description="Cria um agendamento em nome de um Usuário Pessoa (por CPF), com "
    "as mesmas regras do fluxo normal. O cidadão recebe e-mail de "
    "confirmação e o administrador responsável fica registrado.",
)
def criar_agendamento_admin(
    dados: AgendamentoAdminCreate,
    admin: UsuarioAtual = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AgendamentoAdminOut:
    agendamento = AgendamentoService(db).criar_para_usuario(
        admin, dados.cpf_usuario, dados.id_quadra, dados.data, dados.hora_inicio
    )
    return AgendamentoAdminOut.de_modelo(agendamento)

@router.post(
    "/{agendamento_id}/remarcar",
    response_model=AgendamentoAdminOut,
    summary="Remarcar agendamento",
    description="Altera data e horário de um agendamento confirmado, na mesma "
    "quadra, validando a disponibilidade. O cidadão recebe e-mail com o novo horário.",
)
def remarcar_agendamento(
    agendamento_id: int,
    dados: RemarcacaoRequest,
    admin: UsuarioAtual = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AgendamentoAdminOut:
    agendamento = AgendamentoService(db).remarcar(
        admin, agendamento_id, dados.data, dados.hora_inicio
    )
    return AgendamentoAdminOut.de_modelo(agendamento)

@router.post(
    "/{agendamento_id}/cancelar",
    response_model=AgendamentoAdminOut,
    summary="Cancelar agendamento (administração)",
    description="Cancela um agendamento confirmado a qualquer momento (a "
    "restringe apenas o cidadão). O cidadão recebe e-mail de cancelamento.",
)
def cancelar_agendamento_admin(
    agendamento_id: int,
    admin: UsuarioAtual = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AgendamentoAdminOut:
    return AgendamentoAdminOut.de_modelo(
        AgendamentoService(db).cancelar_como_admin(admin, agendamento_id)
    )
