from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import StatusUsuario

class UsuarioPessoa(Base):
    __tablename__ = "usuario_pessoa"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    cpf: Mapped[str] = mapped_column(String(11), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    senha: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[StatusUsuario] = mapped_column(
        Enum(StatusUsuario, name="status_usuario", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        server_default=StatusUsuario.ATIVO.value,
    )
    data_cadastro: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    tentativas_login: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    bloqueado_ate: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
