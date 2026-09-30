from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import StatusAgendamento
from app.models.quadra import Quadra
from app.models.usuario_pessoa import UsuarioPessoa


class Agendamento(Base):
    __tablename__ = "agendamento"
    __table_args__ = (
        # Índices únicos PARCIAIS (só status Confirmado): um horário por quadra e
        # um agendamento ativo por usuário, mesmo com requisições simultâneas.
        Index(
            "uq_agendamento_quadra_horario_confirmado",
            "id_quadra",
            "data_hora_inicio",
            unique=True,
            postgresql_where="status = 'Confirmado'",
        ),
        Index(
            "uq_agendamento_usuario_confirmado",
            "id_usuario",
            unique=True,
            postgresql_where="status = 'Confirmado'",
        ),
        Index("ix_agendamento_id_usuario", "id_usuario"),
        Index("ix_agendamento_id_quadra_inicio", "id_quadra", "data_hora_inicio"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuario_pessoa.id"), nullable=False)
    id_quadra: Mapped[int] = mapped_column(ForeignKey("quadra.id"), nullable=False)
    # Preenchido quando a administração cria, remarca ou cancela o agendamento
    id_admin_responsavel: Mapped[int | None] = mapped_column(
        ForeignKey("usuario_administrativo.id"), nullable=True
    )
    data_hora_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    data_hora_fim: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[StatusAgendamento] = mapped_column(
        Enum(
            StatusAgendamento,
            name="status_agendamento",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        server_default=StatusAgendamento.CONFIRMADO.value,
    )
    data_criacao: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    # Evita reenviar o lembrete a cada execução do job
    lembrete_enviado_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    quadra: Mapped[Quadra] = relationship()
    usuario: Mapped[UsuarioPessoa] = relationship()
