from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import StatusUsuario, UsuarioPessoa

class UsuarioPessoaRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def obter_por_id(self, usuario_id: int) -> UsuarioPessoa | None:
        return self.db.get(UsuarioPessoa, usuario_id)

    def obter_por_email(self, email: str) -> UsuarioPessoa | None:
        return self.db.scalar(select(UsuarioPessoa).where(UsuarioPessoa.email == email))

    def obter_por_cpf(self, cpf: str) -> UsuarioPessoa | None:
        return self.db.scalar(select(UsuarioPessoa).where(UsuarioPessoa.cpf == cpf))

    def listar(self) -> list[UsuarioPessoa]:
        return list(self.db.scalars(select(UsuarioPessoa).order_by(UsuarioPessoa.id)))

    def criar(self, *, nome: str, cpf: str, email: str, senha_hash: str) -> UsuarioPessoa:
        usuario = UsuarioPessoa(
            nome=nome,
            cpf=cpf,
            email=email,
            senha=senha_hash,
            status=StatusUsuario.ATIVO,
        )
        self.db.add(usuario)
        self.db.flush()
        self.db.refresh(usuario)
        return usuario

    def atualizar(self, usuario: UsuarioPessoa, **campos) -> UsuarioPessoa:
        for campo, valor in campos.items():
            setattr(usuario, campo, valor)
        self.db.flush()
        return usuario
