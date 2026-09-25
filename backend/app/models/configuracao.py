from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

class Configuracao(Base):

    __tablename__ = "configuracao"

    chave: Mapped[str] = mapped_column(String(64), primary_key=True)
    valor: Mapped[str] = mapped_column(String(255), nullable=False)

CHAVE_ANTECEDENCIA_CANCELAMENTO = "cancelamento_antecedencia_minima_horas"
CHAVE_ANTECEDENCIA_LEMBRETE = "lembrete_antecedencia_horas"
