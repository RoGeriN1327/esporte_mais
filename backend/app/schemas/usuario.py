from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.models.enums import StatusUsuario
from app.utils.cpf import cpf_valido, normalizar_cpf

class UsuarioPessoaCreate(BaseModel):

    nome: str = Field(description="Nome completo (máx. 100 caracteres)")
    cpf: str = Field(description="CPF (com ou sem máscara)")
    email: EmailStr
    senha: str = Field(description="Mínimo de 8 caracteres")
    confirmar_senha: str

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("O nome é obrigatório.")
        if len(valor) > 100:
            raise ValueError("O nome deve ter no máximo 100 caracteres.")
        return valor

    @field_validator("cpf")
    @classmethod
    def validar_cpf(cls, valor: str) -> str:
        cpf = normalizar_cpf(valor)
        if not cpf_valido(cpf):
            raise ValueError("CPF inválido. Informe 11 dígitos numéricos válidos.")
        return cpf

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, valor: str) -> str:

        return valor.lower()

    @field_validator("senha")
    @classmethod
    def validar_tamanho_senha(cls, valor: str) -> str:
        if len(valor) < 8:
            raise ValueError("A senha deve ter no mínimo 8 caracteres.")
        return valor

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

    email: EmailStr

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, valor: str) -> str:
        return valor.lower()
