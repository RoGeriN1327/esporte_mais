from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

class Notificacao(Base):

    __tablename__ = "notificacao"
    __table_args__ = (Index("ix_notificacao_destinatario", "destinatario"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    destinatario: Mapped[str] = mapped_column(String(255), nullable=False)
    assunto: Mapped[str] = mapped_column(String(255), nullable=False)
    evento: Mapped[str] = mapped_column(String(50), nullable=False)
    sucesso: Mapped[bool] = mapped_column(Boolean, nullable=False)
    enviado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
