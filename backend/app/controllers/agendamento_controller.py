from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.core.deps import PessoaLogada, SessaoDb
from app.models.enums import StatusAgendamento
from app.schemas.agendamento import AgendamentoCreate, AgendamentoOut, RenovacaoRequest
from app.services.agendamento_service import AgendamentoService

router = APIRouter(prefix="/agendamentos", tags=["Agendamentos"])


@router.post(
    "",
    response_model=AgendamentoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Realizar agendamento",
    description="Registra o agendamento no horário selecionado, validando a "
    "disponibilidade e o limite de um agendamento ativo por usuário. "
    "Envia e-mail de confirmação.",
)
def criar_agendamento(
    dados: AgendamentoCreate, usuario: PessoaLogada, db: SessaoDb
) -> AgendamentoOut:
    agendamento = AgendamentoService(db).criar(
        usuario, dados.id_quadra, dados.data, dados.hora_inicio
    )
    return AgendamentoOut.de_modelo(agendamento)


@router.get(
    "/me",
    response_model=list[AgendamentoOut],
    summary="Meus agendamentos",
    description="Lista os agendamentos do usuário autenticado com filtros de "
    "data, nome da quadra, esporte e status.",
)
def meus_agendamentos(
    usuario: PessoaLogada,
    db: SessaoDb,
    data: date | None = None,
    nome_quadra: str | None = None,
    esporte: str | None = None,
    status_agendamento: Annotated[StatusAgendamento | None, Query(alias="status")] = None,
) -> list[AgendamentoOut]:
    agendamentos = AgendamentoService(db).listar_meus(
        usuario.id,
        dia=data,
        nome_quadra=nome_quadra,
        esporte=esporte,
        status=status_agendamento,
    )
    return [AgendamentoOut.de_modelo(a) for a in agendamentos]


@router.get(
    "/me/proximo",
    response_model=AgendamentoOut | None,
    summary="Próximo agendamento ativo",
    description="Próximo agendamento confirmado do usuário (exibido no menu "
    "principal), ou nulo se não houver.",
)
def proximo_agendamento(usuario: PessoaLogada, db: SessaoDb) -> AgendamentoOut | None:
    agendamento = AgendamentoService(db).proximo(usuario.id)
    return AgendamentoOut.de_modelo(agendamento) if agendamento is not None else None


@router.post(
    "/{agendamento_id}/cancelar",
    response_model=AgendamentoOut,
    summary="Cancelar agendamento",
    description="Cancela um agendamento confirmado, respeitando a antecedência "
    "mínima definida pela administração. Libera o horário e envia "
    "e-mail de cancelamento.",
)
def cancelar_agendamento(
    agendamento_id: int, usuario: PessoaLogada, db: SessaoDb
) -> AgendamentoOut:
    return AgendamentoOut.de_modelo(AgendamentoService(db).cancelar(usuario, agendamento_id))


@router.post(
    "/{agendamento_id}/renovar",
    response_model=AgendamentoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Renovar agendamento",
    description="Renova um agendamento concluído: o registro original passa a "
    '"Renovado" e um novo agendamento confirmado é criado na mesma quadra, na '
    "data e horário escolhidos. Envia e-mail de renovação.",
)
def renovar_agendamento(
    agendamento_id: int, dados: RenovacaoRequest, usuario: PessoaLogada, db: SessaoDb
) -> AgendamentoOut:
    novo = AgendamentoService(db).renovar(usuario, agendamento_id, dados.data, dados.hora_inicio)
    return AgendamentoOut.de_modelo(novo)
