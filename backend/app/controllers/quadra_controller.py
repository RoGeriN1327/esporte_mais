from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import UsuarioAtual, get_current_user
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
    esporte: str | None = Query(default=None),
    nome: str | None = Query(default=None),
    bairro: str | None = Query(default=None),
    _usuario: UsuarioAtual = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[QuadraOut]:
    return QuadraService(db).listar_disponiveis(esporte=esporte, nome=nome, bairro=bairro)

@router.get(
    "/filtros",
    response_model=OpcoesFiltroOut,
    summary="Opções de filtro da consulta",
    description="Modalidades e bairros das quadras cadastradas, para os "
    "dropdowns da tela de consulta.",
)
def opcoes_de_filtro(
    _usuario: UsuarioAtual = Depends(get_current_user), db: Session = Depends(get_db)
) -> OpcoesFiltroOut:
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
    data: date = Query(description="Data desejada (a partir de hoje)"),
    _usuario: UsuarioAtual = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HorariosDisponiveisOut:
    horarios = QuadraService(db).horarios_disponiveis(quadra_id, data)
    return HorariosDisponiveisOut(id_quadra=quadra_id, data=data, horarios=horarios)
