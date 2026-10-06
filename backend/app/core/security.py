"""Senhas (bcrypt), access tokens (JWT) e tokens opacos (refresh e redefinição).

- Access token: JWT curto (ACCESS_TOKEN_EXPIRE_MINUTES), validado em app.core.deps.
- Refresh token e link de redefinição de senha: valores aleatórios entregues ao
  usuário; no banco fica só o hash SHA-256 (hash_token).
"""

import hashlib
import secrets
import string
import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.core.config import settings
from app.models.enums import PerfilAdministrativo, TipoUsuario

# --- Senhas -----------------------------------------------------------------


def gerar_hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verificar_senha(senha: str, senha_hash: str) -> bool:
    try:
        return bcrypt.checkpw(senha.encode("utf-8"), senha_hash.encode("utf-8"))
    except ValueError:
        return False


# Usado no login de e-mail inexistente: verificar a senha contra este hash faz a
# resposta demorar o mesmo que a de um e-mail cadastrado, impedindo descobrir
# quais e-mails existem pelo tempo de resposta.
HASH_FICTICIO = bcrypt.hashpw(secrets.token_bytes(24), bcrypt.gensalt()).decode("utf-8")


def gerar_senha_temporaria(tamanho: int = 12) -> str:
    """Senha aleatória com ao menos uma minúscula, uma maiúscula e um dígito."""
    alfabeto = string.ascii_letters + string.digits
    while True:
        senha = "".join(secrets.choice(alfabeto) for _ in range(tamanho))
        if (
            any(c.islower() for c in senha)
            and any(c.isupper() for c in senha)
            and any(c.isdigit() for c in senha)
        ):
            return senha


# --- Access token (JWT) -----------------------------------------------------


def criar_access_token(
    usuario_id: int,
    tipo: TipoUsuario,
    perfil: PerfilAdministrativo | None = None,
    sessao_expira_em: datetime | None = None,
) -> tuple[str, str, datetime]:
    """Retorna (token, jti, expira_em). O jti permite revogar o token no logout.

    Com sessao_expira_em, o token nunca vale além do fim da sessão.
    """
    agora = datetime.now(UTC)
    expira_em = agora + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    if sessao_expira_em is not None:
        expira_em = min(expira_em, sessao_expira_em)
    jti = str(uuid.uuid4())
    claims = {
        "sub": str(usuario_id),
        "tipo": tipo.value,
        "perfil": perfil.value if perfil is not None else None,
        "jti": jti,
        "iat": agora,
        "exp": expira_em,
    }
    token = jwt.encode(claims, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, jti, expira_em


def decodificar_access_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])


# --- Tokens opacos (refresh e redefinição de senha) -------------------------


def gerar_token_opaco() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
