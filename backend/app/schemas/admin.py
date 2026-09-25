from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.enums import PerfilAdministrativo, StatusUsuario
from app.utils.cpf import cpf_valido, normalizar_cpf

class _DadosAdministrativosBase(BaseModel):
    nome: str = Field(description="Nome completo (máx. 100 caracteres)")
    cpf: str = Field(description="CPF (com ou sem máscara)")
    email: EmailStr

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

class AdministradorCreate(_DadosAdministrativosBase):

    perfil: PerfilAdministrativo = Field(description='"Gestor" ou "Operador"')

class AdministradorUpdate(_DadosAdministrativosBase):

    perfil: PerfilAdministrativo

class AdministradorOut(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    cpf: str
    email: str
    perfil: PerfilAdministrativo
    status: StatusUsuario
    data_cadastro: datetime

class UsuarioPessoaAdminCreate(_DadosAdministrativosBase):
    pass
