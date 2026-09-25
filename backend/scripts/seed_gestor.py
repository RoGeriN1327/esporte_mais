import bcrypt
from sqlalchemy import select

from app.core.config import settings
from app.core.database import SessionLocal
from app.models import PerfilAdministrativo, UsuarioAdministrativo

def main() -> None:
    with SessionLocal() as db:
        existente = db.scalar(
            select(UsuarioAdministrativo).where(
                UsuarioAdministrativo.email == settings.GESTOR_INICIAL_EMAIL
            )
        )
        if existente is not None:
            print(
                f"Gestor inicial ja existe (id={existente.id}, "
                f"email={existente.email}); nada a fazer."
            )
            return

        senha_hash = bcrypt.hashpw(
            settings.GESTOR_INICIAL_SENHA.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        gestor = UsuarioAdministrativo(
            nome=settings.GESTOR_INICIAL_NOME,
            cpf=settings.GESTOR_INICIAL_CPF,
            email=settings.GESTOR_INICIAL_EMAIL,
            senha=senha_hash,
            perfil=PerfilAdministrativo.GESTOR,
        )
        db.add(gestor)
        db.commit()
        db.refresh(gestor)
        print(f"Gestor inicial criado (id={gestor.id}, email={gestor.email}).")

if __name__ == "__main__":
    main()
