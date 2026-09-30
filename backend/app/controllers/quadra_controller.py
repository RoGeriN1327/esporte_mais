from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query

from app.core.deps import SessaoDb, UsuarioLogado
from app.schemas.quadra import HorariosDisponiveisOut, OpcoesFiltroOut, QuadraOut
from app.services.quadra_service import QuadraService

router = APIRouter(prefix="/quadras", tags=["Consulta de Quadras"])


@router.get(
    "",
    response_model=list[QuadraOut],
    summary="Consultar quadras disponíveis",
    description="Lista as quadras ativas, com filtros opcionais de esporte, "
    "nome e bairro (tela de consulta de quadras).",
)
def listar_quadras(
    _usuario: UsuarioLogado,
    db: SessaoDb,
    esporte: str | None = None,
    nome: str | None = None,
    bairro: str | None = None,
) -> list[QuadraOut]:
    return QuadraService(db).listar_disponiveis(esporte=esporte, nome=nome, bairro=bairro)


@router.get(
    "/filtros",
    response_model=OpcoesFiltroOut,
    summary="Opções de filtro da consulta",
    description="Modalidades e bairros das quadras cadastradas, para os "
    "dropdowns da tela de consulta.",
)
def opcoes_de_filtro(_usuario: UsuarioLogado, db: SessaoDb) -> OpcoesFiltroOut:
    return OpcoesFiltroOut(**QuadraService(db).opcoes_de_filtro())


@router.get(
    "/{quadra_id}/horarios-disponiveis",
    response_model=HorariosDisponiveisOut,
    summary="Horários disponíveis da quadra na data",
    description="Slots de 1 hora gerados pela grade de funcionamento da quadra. "
    "Horários já ocupados ou no passado não são exibidos.",
)
def horarios_disponiveis(
    quadra_id: int,
    data: Annotated[date, Query(description="Data desejada (a partir de hoje)")],
    _usuario: UsuarioLogado,
    db: SessaoDb,
) -> HorariosDisponiveisOut:
    horarios = QuadraService(db).horarios_disponiveis(quadra_id, data)
    return HorariosDisponiveisOut(id_quadra=quadra_id, data=data, horarios=horarios)
