from datetime import datetime

from sqlalchemy import DateTime, Enum, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import TipoUsuario

def _tipo_usuario_enum() -> Enum:
    return Enum(TipoUsuario, name="tipo_usuario", values_callable=lambda e: [m.value for m in e])

class RefreshToken(Base):

    __tablename__ = "refresh_token"
    __table_args__ = (Index("ix_refresh_token_tipo_usuario_usuario_id", "tipo_usuario", "usuario_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)

    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    tipo_usuario: Mapped[TipoUsuario] = mapped_column(_tipo_usuario_enum(), nullable=False)

    usuario_id: Mapped[int] = mapped_column(Integer, nullable=False)
    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revogado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

class TokenRevogado(Base):

    __tablename__ = "token_revogado"

    id: Mapped[int] = mapped_column(primary_key=True)
    jti: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)

    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revogado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

class TokenRedefinicaoSenha(Base):

    __tablename__ = "token_redefinicao_senha"

    id: Mapped[int] = mapped_column(primary_key=True)

    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    tipo_usuario: Mapped[TipoUsuario] = mapped_column(_tipo_usuario_enum(), nullable=False)

    usuario_id: Mapped[int] = mapped_column(Integer, nullable=False)
    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    usado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
