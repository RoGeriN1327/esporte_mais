from dataclasses import dataclass
from datetime import datetime, timezone

import jwt as pyjwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core import security
from app.core.database import get_db
from app.exceptions import AcessoNegado, ContaDesativada, NaoAutenticado
from app.models import PerfilAdministrativo, StatusUsuario, TipoUsuario
from app.repositories import (
    TokenRepository,
    UsuarioAdministrativoRepository,
    UsuarioPessoaRepository,
)

bearer_scheme = HTTPBearer(auto_error=False, description="Access token JWT (Authorization: Bearer)")

@dataclass
class UsuarioAtual:

    id: int
    nome: str
    email: str
    tipo: TipoUsuario
    perfil: PerfilAdministrativo | None
    jti: str
    expira_em: datetime

def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> UsuarioAtual:
    if credentials is None:
        raise NaoAutenticado("Não autenticado. Informe o token de acesso.")
    try:
        claims = security.decodificar_access_token(credentials.credentials)
    except pyjwt.ExpiredSignatureError:
        raise NaoAutenticado("Sessão expirada. Faça login novamente.")
    except pyjwt.PyJWTError:
        raise NaoAutenticado("Token de acesso inválido.")

    jti = claims.get("jti")
    if not jti or TokenRepository(db).jti_esta_revogado(jti):

        raise NaoAutenticado("Sessão encerrada. Faça login novamente.")

    tipo = TipoUsuario(claims["tipo"])
    usuario_id = int(claims["sub"])
    if tipo is TipoUsuario.PESSOA:
        usuario = UsuarioPessoaRepository(db).obter_por_id(usuario_id)
        perfil = None
    else:
        usuario = UsuarioAdministrativoRepository(db).obter_por_id(usuario_id)

        perfil = PerfilAdministrativo(claims["perfil"]) if claims.get("perfil") else None

    if usuario is None or usuario.status is not StatusUsuario.ATIVO:

        raise ContaDesativada("Conta desativada.")

    return UsuarioAtual(
        id=usuario.id,
        nome=usuario.nome,
        email=usuario.email,
        tipo=tipo,
        perfil=perfil,
        jti=jti,
        expira_em=datetime.fromtimestamp(claims["exp"], tz=timezone.utc),
    )

def require_pessoa(usuario: UsuarioAtual = Depends(get_current_user)) -> UsuarioAtual:
    if usuario.tipo is not TipoUsuario.PESSOA:
        raise AcessoNegado("Acesso restrito a usuários pessoa.")
    return usuario

def require_admin(usuario: UsuarioAtual = Depends(get_current_user)) -> UsuarioAtual:
    if usuario.tipo is not TipoUsuario.ADMINISTRATIVO:
        raise AcessoNegado("Acesso restrito a administradores.")
    return usuario

def require_gestor(usuario: UsuarioAtual = Depends(require_admin)) -> UsuarioAtual:
    if usuario.perfil is not PerfilAdministrativo.GESTOR:
        raise AcessoNegado("Acesso restrito ao perfil Gestor.")
    return usuario
