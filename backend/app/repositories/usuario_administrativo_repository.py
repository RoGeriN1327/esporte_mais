from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import PerfilAdministrativo, StatusUsuario, UsuarioAdministrativo

class UsuarioAdministrativoRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def obter_por_id(self, usuario_id: int) -> UsuarioAdministrativo | None:
        return self.db.get(UsuarioAdministrativo, usuario_id)

    def obter_por_email(self, email: str) -> UsuarioAdministrativo | None:
        return self.db.scalar(
            select(UsuarioAdministrativo).where(UsuarioAdministrativo.email == email)
        )

    def obter_por_cpf(self, cpf: str) -> UsuarioAdministrativo | None:
        return self.db.scalar(
            select(UsuarioAdministrativo).where(UsuarioAdministrativo.cpf == cpf)
        )

    def listar(self) -> list[UsuarioAdministrativo]:
        return list(
            self.db.scalars(select(UsuarioAdministrativo).order_by(UsuarioAdministrativo.id))
        )

    def criar(
        self,
        *,
        nome: str,
        cpf: str,
        email: str,
        senha_hash: str,
        perfil: PerfilAdministrativo,
    ) -> UsuarioAdministrativo:
        usuario = UsuarioAdministrativo(
            nome=nome,
            cpf=cpf,
            email=email,
            senha=senha_hash,
            perfil=perfil,
            status=StatusUsuario.ATIVO,
        )
        self.db.add(usuario)
        self.db.flush()
        self.db.refresh(usuario)
        return usuario

    def atualizar(self, usuario: UsuarioAdministrativo, **campos) -> UsuarioAdministrativo:
        for campo, valor in campos.items():
            setattr(usuario, campo, valor)
        self.db.flush()
        return usuario
