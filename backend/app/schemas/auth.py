from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.utils.cpf import cpf_valido, normalizar_cpf

class LoginRequest(BaseModel):

    email: str = Field(description="E-mail cadastrado")
    senha: str = Field(description="Senha do usuário")

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, valor: str) -> str:
        return valor.lower()

class UsuarioBasicoOut(BaseModel):

    id: int
    nome: str
    email: str
    tipo: str = Field(description='"Pessoa" ou "Administrativo"')
    perfil: str | None = Field(default=None, description='"Gestor"/"Operador" quando administrativo')

class TokenResponse(BaseModel):
    access_token: str = Field(description="JWT de acesso (30 min)")
    refresh_token: str = Field(description="Token opaco de renovação (7 dias)")
    token_type: str = "bearer"
    usuario: UsuarioBasicoOut

class RefreshRequest(BaseModel):
    refresh_token: str = Field(description="Refresh token recebido no login")

class LogoutRequest(BaseModel):
    refresh_token: str = Field(description="Refresh token da sessão a encerrar")

class RecuperarSenhaRequest(BaseModel):

    email: EmailStr
    cpf: str = Field(description="CPF do titular da conta (com ou sem máscara)")

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, valor: str) -> str:
        return valor.lower()

    @field_validator("cpf")
    @classmethod
    def validar_cpf(cls, valor: str) -> str:
        cpf = normalizar_cpf(valor)
        if not cpf_valido(cpf):
            raise ValueError("CPF inválido. Informe 11 dígitos numéricos válidos.")
        return cpf

class RedefinirSenhaRequest(BaseModel):

    token: str = Field(description="Token recebido no link enviado por e-mail")
    nova_senha: str
    confirmar_senha: str

    @field_validator("nova_senha")
    @classmethod
    def validar_tamanho_senha(cls, valor: str) -> str:
        if len(valor) < 8:
            raise ValueError("A senha deve ter no mínimo 8 caracteres.")
        return valor

    @model_validator(mode="after")
    def validar_confirmacao(self) -> "RedefinirSenhaRequest":
        if self.nova_senha != self.confirmar_senha:
            raise ValueError("A confirmação de senha não confere com a senha informada.")
        return self

class MensagemResponse(BaseModel):
    mensagem: str
