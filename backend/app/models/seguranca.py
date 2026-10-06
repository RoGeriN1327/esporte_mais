"""Proteção contra força bruta por IP (ver AuthService.login)."""

from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class FalhaLogin(Base):
    """Tentativa de login recusada (e-mail inexistente, senha errada ou conta bloqueada)."""

    __tablename__ = "falha_login"
    __table_args__ = (Index("ix_falha_login_ip_criado_em", "ip", "criado_em"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ip: Mapped[str] = mapped_column(String(45), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class IpBloqueado(Base):
    """IP bloqueado sem prazo nas rotas públicas de autenticação; só o Gestor desbloqueia."""

    __tablename__ = "ip_bloqueado"

    ip: Mapped[str] = mapped_column(String(45), primary_key=True)
    motivo: Mapped[str] = mapped_column(String(255), nullable=False)
    bloqueado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
