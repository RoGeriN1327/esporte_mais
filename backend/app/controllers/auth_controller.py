from fastapi import APIRouter, Request

from app.core.deps import SessaoDb, UsuarioLogado
from app.core.rate_limit import limiter
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    MensagemResponse,
    RecuperarSenhaRequest,
    RedefinirSenhaRequest,
    RefreshRequest,
    TokenResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Autenticar usuário (login)",
    description="Autentica Usuário Pessoa ou Administrativo com e-mail e senha. "
    "Retorna access token JWT (30 min) e refresh token (7 dias).",
)
@limiter.limit("10/minute")
def login(request: Request, dados: LoginRequest, db: SessaoDb) -> TokenResponse:
    return TokenResponse(**AuthService(db).login(dados.email, dados.senha))


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Renovar tokens de acesso",
    description="Troca um refresh token válido por um novo par de tokens (rotação).",
)
@limiter.limit("30/minute")
def refresh(request: Request, dados: RefreshRequest, db: SessaoDb) -> TokenResponse:
    return TokenResponse(**AuthService(db).renovar_tokens(dados.refresh_token))


@router.post(
    "/logout",
    response_model=MensagemResponse,
    summary="Encerrar sessão (logout)",
    description="Revoga o refresh token informado e invalida o access token atual.",
)
def logout(dados: LogoutRequest, usuario: UsuarioLogado, db: SessaoDb) -> MensagemResponse:
    AuthService(db).logout(usuario, dados.refresh_token)
    return MensagemResponse(mensagem="Sessão encerrada com sucesso.")


@router.post(
    "/recuperar-senha",
    response_model=MensagemResponse,
    summary="Solicitar recuperação de senha",
    description="Envia link temporário (1 hora) de redefinição de senha quando e-mail "
    "e CPF pertencem ao mesmo usuário. A resposta é sempre genérica (anti-enumeração).",
)
@limiter.limit("5/minute")
def recuperar_senha(
    request: Request, dados: RecuperarSenhaRequest, db: SessaoDb
) -> MensagemResponse:
    return MensagemResponse(mensagem=AuthService(db).recuperar_senha(dados.email, dados.cpf))


@router.post(
    "/redefinir-senha",
    response_model=MensagemResponse,
    summary="Redefinir senha via link temporário",
    description="Define nova senha (de 8 a 72 caracteres, diferente da atual) a partir do "
    "token recebido "
    "por e-mail. O link é de uso único e expira em 1 hora.",
)
@limiter.limit("5/minute")
def redefinir_senha(
    request: Request, dados: RedefinirSenhaRequest, db: SessaoDb
) -> MensagemResponse:
    AuthService(db).redefinir_senha(dados.token, dados.nova_senha)
    return MensagemResponse(mensagem="Senha redefinida com sucesso. Faça login com a nova senha.")
