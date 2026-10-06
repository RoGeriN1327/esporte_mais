"""Schemas de autenticação: login, tokens, logout e recuperação de senha."""

from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field, model_validator

from app.schemas.validadores import CPF, Email, Senha, normalizar_email


class LoginRequest(BaseModel):
    # Sem validar formato: um e-mail malformado simplesmente não encontra usuário.
    email: Annotated[str, AfterValidator(normalizar_email)] = Field(description="E-mail cadastrado")
    senha: str = Field(description="Senha do usuário")


class UsuarioBasicoOut(BaseModel):
    id: int
    nome: str
    email: str
    tipo: str = Field(description='"Pessoa" ou "Administrativo"')
    perfil: str | None = Field(
        default=None, description='"Gestor"/"Operador" quando administrativo'
    )


class TokenResponse(BaseModel):
    access_token: str = Field(description="JWT de acesso (30 min, nunca além do fim da sessão)")
    refresh_token: str = Field(description="Token opaco de renovação (vale até o fim da sessão)")
    sessao_expira_em: datetime = Field(
        description="Fim da sessão (2 horas após o login); renovar os tokens não o estende"
    )
    # "bearer" é o tipo de token do padrão OAuth2 (RFC 6750), não uma senha.
    token_type: str = "bearer"  # noqa: S105
    usuario: UsuarioBasicoOut


class RefreshRequest(BaseModel):
    refresh_token: str = Field(description="Refresh token recebido no login")


class LogoutRequest(BaseModel):
    refresh_token: str = Field(description="Refresh token da sessão a encerrar")


class RecuperarSenhaRequest(BaseModel):
    email: Email
    cpf: CPF = Field(description="CPF do titular da conta (com ou sem máscara)")


class ValidarTokenRedefinicaoRequest(BaseModel):
    token: str = Field(description="Token recebido no link enviado por e-mail")


class RedefinirSenhaRequest(BaseModel):
    token: str = Field(description="Token recebido no link enviado por e-mail")
    nova_senha: Senha
    confirmar_senha: str

    @model_validator(mode="after")
    def validar_confirmacao(self) -> "RedefinirSenhaRequest":
        if self.nova_senha != self.confirmar_senha:
            raise ValueError("A confirmação de senha não confere com a senha informada.")
        return self


class MensagemResponse(BaseModel):
    mensagem: str
