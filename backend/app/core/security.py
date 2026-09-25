import hashlib
import secrets
import string
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import settings
from app.models.enums import PerfilAdministrativo, TipoUsuario

def gerar_hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verificar_senha(senha: str, senha_hash: str) -> bool:
    try:
        return bcrypt.checkpw(senha.encode("utf-8"), senha_hash.encode("utf-8"))
    except ValueError:

        return False

def criar_access_token(
    usuario_id: int,
    tipo: TipoUsuario,
    perfil: PerfilAdministrativo | None = None,
) -> tuple[str, str, datetime]:
    agora = datetime.now(timezone.utc)
    expira_em = agora + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
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

def gerar_token_opaco() -> str:
    return secrets.token_urlsafe(48)

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

HASH_FICTICIO = bcrypt.hashpw(secrets.token_bytes(24), bcrypt.gensalt()).decode("utf-8")

def gerar_senha_temporaria(tamanho: int = 12) -> str:
    alfabeto = string.ascii_letters + string.digits
    while True:
        senha = "".join(secrets.choice(alfabeto) for _ in range(tamanho))
        if (
            any(c.islower() for c in senha)
            and any(c.isupper() for c in senha)
            and any(c.isdigit() for c in senha)
        ):
            return senha
