"""Cria o primeiro Gestor a partir das variáveis GESTOR_INICIAL_*.

Executado automaticamente pelo docker-entrypoint.sh a cada subida do container.
- Se as variáveis não estiverem definidas, não faz nada (caso normal em produção
  depois do primeiro deploy).
- Se o e-mail já existir, não faz nada (nunca altera a senha de um Gestor existente).
- A senha nunca é impressa no log.

Uso manual (a partir de backend/): python -m scripts.seed_gestor
"""

import sys

from sqlalchemy import select

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import gerar_hash_senha
from app.models import PerfilAdministrativo, UsuarioAdministrativo
from app.schemas.validadores import normalizar_email, validar_cpf, validar_tamanho_senha


def main() -> None:
    nome = settings.GESTOR_INICIAL_NOME
    cpf = settings.GESTOR_INICIAL_CPF
    email = settings.GESTOR_INICIAL_EMAIL
    senha = settings.GESTOR_INICIAL_SENHA

    if not all((nome, cpf, email, senha)):
        print("GESTOR_INICIAL_* não definidas; nenhum Gestor inicial a criar.")
        return

    email = normalizar_email(email)  # o login compara e-mails em minúsculas

    with SessionLocal() as db:
        existente = db.scalar(
            select(UsuarioAdministrativo).where(UsuarioAdministrativo.email == email)
        )
        if existente is not None:
            print(f"Gestor inicial já existe (id={existente.id}); nada a fazer.")
            return

        try:
            cpf = validar_cpf(cpf)
            validar_tamanho_senha(senha)
        except ValueError as erro:
            # Não impede a API de subir; só avisa no log do container.
            print(f"Gestor inicial NÃO criado: {erro}", file=sys.stderr)
            return

        gestor = UsuarioAdministrativo(
            nome=nome.strip(),
            cpf=cpf,
            email=email,
            senha=gerar_hash_senha(senha),
            perfil=PerfilAdministrativo.GESTOR,
        )
        db.add(gestor)
        db.commit()
        print(f"Gestor inicial criado (id={gestor.id}, email={gestor.email}).")


if __name__ == "__main__":
    main()
