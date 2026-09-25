from datetime import time

from sqlalchemy import (
    CheckConstraint,
    Enum,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    Time,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import StatusQuadra

class Quadra(Base):

    __tablename__ = "quadra"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    endereco: Mapped[str] = mapped_column(String(255), nullable=False)
    bairro: Mapped[str] = mapped_column(String(100), nullable=False)
    esporte: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[StatusQuadra] = mapped_column(
        Enum(StatusQuadra, name="status_quadra", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        server_default=StatusQuadra.ATIVA.value,
    )

    faixas_horarias: Mapped[list["QuadraFaixaHoraria"]] = relationship(
        back_populates="quadra", cascade="all, delete-orphan"
    )

class QuadraFaixaHoraria(Base):

    __tablename__ = "quadra_faixa_horaria"
    __table_args__ = (

        CheckConstraint("dia_semana BETWEEN 0 AND 6", name="dia_semana_valido"),
        CheckConstraint("hora_fim > hora_inicio", name="horas_validas"),
        Index("ix_quadra_faixa_horaria_id_quadra", "id_quadra"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    id_quadra: Mapped[int] = mapped_column(
        ForeignKey("quadra.id", ondelete="CASCADE"), nullable=False
    )

    dia_semana: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    hora_inicio: Mapped[time] = mapped_column(Time, nullable=False)
    hora_fim: Mapped[time] = mapped_column(Time, nullable=False)

    quadra: Mapped[Quadra] = relationship(back_populates="faixas_horarias")
