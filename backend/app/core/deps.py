"""Dependencies do FastAPI para autenticação e controle de acesso.

Use os aliases nos parâmetros das rotas para exigir o tipo de usuário:
    UsuarioLogado  qualquer usuário autenticado
    PessoaLogada   somente Usuário Pessoa (cidadão)
    AdminLogado    Gestor ou Operador
    GestorLogado   somente Gestor
    IpLiberado     rotas públicas de autenticação: recusa IPs bloqueados
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated

import jwt as pyjwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core import security
from app.core.database import get_db
from app.core.rate_limit import ip_do_cliente
from app.exceptions import AcessoNegado, ContaDesativada, IpBloqueado, NaoAutenticado
from app.models import PerfilAdministrativo, StatusUsuario, TipoUsuario
from app.repositories import (
    SegurancaRepository,
    TokenRepository,
    UsuarioAdministrativoRepository,
    UsuarioPessoaRepository,
)

bearer_scheme = HTTPBearer(auto_error=False, description="Access token JWT (Authorization: Bearer)")

SessaoDb = Annotated[Session, Depends(get_db)]

MSG_IP_BLOQUEADO = (
    "Acesso bloqueado por excesso de tentativas de login. "
    "Procure a Secretaria Municipal de Esportes."
)


def get_ip_liberado(request: Request, db: SessaoDb) -> str:
    """IP do cliente nas rotas públicas de autenticação; recusa IPs bloqueados."""
    ip = ip_do_cliente(request)
    if SegurancaRepository(db).ip_esta_bloqueado(ip):
        raise IpBloqueado(MSG_IP_BLOQUEADO)
    return ip


# Use nas rotas públicas de autenticação (login, cadastro, recuperação de senha).
IpLiberado = Annotated[str, Depends(get_ip_liberado)]


@dataclass
class UsuarioAtual:
    """Usuário da requisição, montado a partir do access token + banco."""

    id: int
    nome: str
    email: str
    tipo: TipoUsuario
    perfil: PerfilAdministrativo | None
    jti: str
    expira_em: datetime


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: SessaoDb,
) -> UsuarioAtual:
    if credentials is None:
        raise NaoAutenticado("Não autenticado. Informe o token de acesso.")
    try:
        claims = security.decodificar_access_token(credentials.credentials)
    except pyjwt.ExpiredSignatureError:
        raise NaoAutenticado("Sessão expirada. Faça login novamente.") from None
    except pyjwt.PyJWTError:
        raise NaoAutenticado("Token de acesso inválido.") from None

    jti = claims.get("jti")
    if not jti or TokenRepository(db).jti_esta_revogado(jti):
        raise NaoAutenticado("Sessão encerrada. Faça login novamente.")

    tipo = TipoUsuario(claims["tipo"])
    usuario_id = int(claims["sub"])
    if tipo is TipoUsuario.PESSOA:
        usuario = UsuarioPessoaRepository(db).obter_por_id(usuario_id)
    else:
        usuario = UsuarioAdministrativoRepository(db).obter_por_id(usuario_id)

    if usuario is None or usuario.status is not StatusUsuario.ATIVO:
        raise ContaDesativada("Conta desativada.")

    # O perfil vem do banco, não do token: uma alteração de perfil (ex.: Gestor
    # rebaixado a Operador) passa a valer na próxima requisição, sem esperar o
    # token expirar.
    perfil = usuario.perfil if tipo is TipoUsuario.ADMINISTRATIVO else None

    return UsuarioAtual(
        id=usuario.id,
        nome=usuario.nome,
        email=usuario.email,
        tipo=tipo,
        perfil=perfil,
        jti=jti,
        expira_em=datetime.fromtimestamp(claims["exp"], tz=UTC),
    )


UsuarioLogado = Annotated[UsuarioAtual, Depends(get_current_user)]


def require_pessoa(usuario: UsuarioLogado) -> UsuarioAtual:
    if usuario.tipo is not TipoUsuario.PESSOA:
        raise AcessoNegado("Acesso restrito a usuários pessoa.")
    return usuario


def require_admin(usuario: UsuarioLogado) -> UsuarioAtual:
    if usuario.tipo is not TipoUsuario.ADMINISTRATIVO:
        raise AcessoNegado("Acesso restrito a administradores.")
    return usuario


def require_gestor(
    usuario: Annotated[UsuarioAtual, Depends(require_admin)],
) -> UsuarioAtual:
    if usuario.perfil is not PerfilAdministrativo.GESTOR:
        raise AcessoNegado("Acesso restrito ao perfil Gestor.")
    return usuario


PessoaLogada = Annotated[UsuarioAtual, Depends(require_pessoa)]
AdminLogado = Annotated[UsuarioAtual, Depends(require_admin)]
GestorLogado = Annotated[UsuarioAtual, Depends(require_gestor)]
