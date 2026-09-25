from datetime import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Quadra, QuadraFaixaHoraria, StatusQuadra

class QuadraRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def obter_por_id(self, quadra_id: int) -> Quadra | None:
        return self.db.get(Quadra, quadra_id)

    def listar_todas(
        self,
        *,
        esporte: str | None = None,
        nome: str | None = None,
        bairro: str | None = None,
    ) -> list[Quadra]:
        consulta = select(Quadra)
        if esporte:
            consulta = consulta.where(Quadra.esporte == esporte)
        if nome:
            consulta = consulta.where(Quadra.nome.ilike(f"%{nome}%"))
        if bairro:
            consulta = consulta.where(Quadra.bairro.ilike(f"%{bairro}%"))
        return list(self.db.scalars(consulta.order_by(Quadra.nome, Quadra.esporte)))

    def criar(
        self,
        *,
        nome: str,
        descricao: str,
        endereco: str,
        bairro: str,
        esporte: str,
        faixas: list[tuple[int, time, time]],
    ) -> Quadra:
        quadra = Quadra(
            nome=nome,
            descricao=descricao,
            endereco=endereco,
            bairro=bairro,
            esporte=esporte,
            status=StatusQuadra.ATIVA,
        )
        quadra.faixas_horarias = [
            QuadraFaixaHoraria(dia_semana=dia, hora_inicio=inicio, hora_fim=fim)
            for dia, inicio, fim in faixas
        ]
        self.db.add(quadra)
        self.db.flush()
        return quadra

    def atualizar(self, quadra: Quadra, **campos) -> Quadra:
        for campo, valor in campos.items():
            setattr(quadra, campo, valor)
        self.db.flush()
        return quadra

    def substituir_faixas(self, quadra: Quadra, faixas: list[tuple[int, time, time]]) -> Quadra:
        quadra.faixas_horarias = [
            QuadraFaixaHoraria(dia_semana=dia, hora_inicio=inicio, hora_fim=fim)
            for dia, inicio, fim in faixas
        ]
        self.db.flush()
        return quadra

    def listar_ativas(
        self,
        *,
        esporte: str | None = None,
        nome: str | None = None,
        bairro: str | None = None,
    ) -> list[Quadra]:
        consulta = select(Quadra).where(Quadra.status == StatusQuadra.ATIVA)
        if esporte:
            consulta = consulta.where(Quadra.esporte == esporte)
        if nome:
            consulta = consulta.where(Quadra.nome.ilike(f"%{nome}%"))
        if bairro:
            consulta = consulta.where(Quadra.bairro == bairro)
        return list(self.db.scalars(consulta.order_by(Quadra.nome, Quadra.esporte)))

    def esportes_distintos(self) -> list[str]:
        return list(
            self.db.scalars(
                select(Quadra.esporte)
                .where(Quadra.status == StatusQuadra.ATIVA)
                .distinct()
                .order_by(Quadra.esporte)
            )
        )

    def bairros_distintos(self) -> list[str]:
        return list(
            self.db.scalars(
                select(Quadra.bairro)
                .where(Quadra.status == StatusQuadra.ATIVA)
                .distinct()
                .order_by(Quadra.bairro)
            )
        )

    def faixas_do_dia(self, quadra_id: int, dia_semana: int) -> list[QuadraFaixaHoraria]:
        return list(
            self.db.scalars(
                select(QuadraFaixaHoraria)
                .where(
                    QuadraFaixaHoraria.id_quadra == quadra_id,
                    QuadraFaixaHoraria.dia_semana == dia_semana,
                )
                .order_by(QuadraFaixaHoraria.hora_inicio)
            )
        )
