from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.core.deps import AdminLogado, SessaoDb
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
    _admin: AdminLogado,
    db: SessaoDb,
    data: date | None = None,
    nome_quadra: str | None = None,
    esporte: str | None = None,
    status_agendamento: Annotated[StatusAgendamento | None, Query(alias="status")] = None,
    cpf_usuario: str | None = None,
    nome_usuario: str | None = None,
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
    dados: AgendamentoAdminCreate, admin: AdminLogado, db: SessaoDb
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
    agendamento_id: int, dados: RemarcacaoRequest, admin: AdminLogado, db: SessaoDb
) -> AgendamentoAdminOut:
    agendamento = AgendamentoService(db).remarcar(
        admin, agendamento_id, dados.data, dados.hora_inicio
    )
    return AgendamentoAdminOut.de_modelo(agendamento)


@router.post(
    "/{agendamento_id}/cancelar",
    response_model=AgendamentoAdminOut,
    summary="Cancelar agendamento (administração)",
    description="Cancela um agendamento confirmado a qualquer momento (o prazo "
    "mínimo de antecedência vale apenas para o cidadão). O cidadão recebe e-mail "
    "de cancelamento.",
)
def cancelar_agendamento_admin(
    agendamento_id: int, admin: AdminLogado, db: SessaoDb
) -> AgendamentoAdminOut:
    return AgendamentoAdminOut.de_modelo(
        AgendamentoService(db).cancelar_como_admin(admin, agendamento_id)
    )
