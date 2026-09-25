from sqlalchemy.orm import Session

from app.models import Configuracao

class ConfiguracaoRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def obter_valor(self, chave: str) -> str | None:
        registro = self.db.get(Configuracao, chave)
        return registro.valor if registro is not None else None

    def definir_valor(self, chave: str, valor: str) -> None:
        registro = self.db.get(Configuracao, chave)
        if registro is None:
            self.db.add(Configuracao(chave=chave, valor=valor))
        else:
            registro.valor = valor
        self.db.flush()
