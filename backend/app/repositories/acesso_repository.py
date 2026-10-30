from sqlalchemy.orm import Session

from app.models import Acesso


class AcessoRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def registrar(self, **campos) -> None:
        self.db.add(Acesso(**campos))
        self.db.flush()
