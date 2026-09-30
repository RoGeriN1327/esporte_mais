"""Schemas do Usuário Pessoa (cidadão): auto-cadastro, perfil e troca de e-mail."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import StatusUsuario
from app.schemas.validadores import CPF, Email, Nome, Senha


class UsuarioPessoaCreate(BaseModel):
    nome: Nome = Field(description="Nome completo (máx. 100 caracteres)")
    cpf: CPF = Field(description="CPF (com ou sem máscara)")
    email: Email
    senha: Senha = Field(description="De 8 a 72 caracteres")
    confirmar_senha: str

    @model_validator(mode="after")
    def validar_confirmacao(self) -> "UsuarioPessoaCreate":
        if self.senha != self.confirmar_senha:
            raise ValueError("A confirmação de senha não confere com a senha informada.")
        return self


class UsuarioPessoaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    cpf: str
    email: str
    status: StatusUsuario
    data_cadastro: datetime


class EmailUpdate(BaseModel):
    email: Email
