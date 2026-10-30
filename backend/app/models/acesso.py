"""Registro de acessos ao sistema (visitas de página e logins).

Serve para saber quem usou o sistema: IP, país, navegador, sistema operacional,
dispositivo e, quando houver, o usuário logado. Ver app.services.acesso_service.
"""

from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Acesso(Base):
    __tablename__ = "acesso"
    __table_args__ = (
        Index("ix_acesso_criado_em", "criado_em"),
        Index("ix_acesso_ip", "ip"),
        Index("ix_acesso_id_visitante", "id_visitante"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    # "pagina" (tela aberta), "login" (entrou) ou "login_recusado" (senha/e-mail errados)
    evento: Mapped[str] = mapped_column(String(20), nullable=False)
    caminho: Mapped[str | None] = mapped_column(String(255))

    ip: Mapped[str] = mapped_column(String(45), nullable=False)
    pais: Mapped[str | None] = mapped_column(String(2))
    navegador: Mapped[str] = mapped_column(String(60), nullable=False)
    sistema: Mapped[str] = mapped_column(String(60), nullable=False)
    # "Computador", "Celular", "Tablet" ou "Outro"
    tipo_dispositivo: Mapped[str] = mapped_column(String(20), nullable=False)
    # Marca e modelo quando o navegador informa (ex.: "Samsung SM-A536E", "Apple iPhone")
    dispositivo: Mapped[str | None] = mapped_column(String(80))
    user_agent: Mapped[str] = mapped_column(String(500), nullable=False)
    # Id aleatório gerado e guardado no navegador: agrupa as visitas do mesmo aparelho
    id_visitante: Mapped[str | None] = mapped_column(String(64))
    referencia: Mapped[str | None] = mapped_column(String(255))

    tipo_usuario: Mapped[str | None] = mapped_column(String(20))
    usuario_id: Mapped[int | None] = mapped_column(Integer)
    # E-mail do usuário logado ou, no login recusado, o e-mail digitado
    email: Mapped[str | None] = mapped_column(String(255))
