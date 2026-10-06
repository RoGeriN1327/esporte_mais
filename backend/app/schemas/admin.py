"""Schemas da gestão de usuários pela administração (administradores e cidadãos)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import PerfilAdministrativo, StatusUsuario
from app.schemas.validadores import CPF, Email, Nome


class _DadosCadastraisBase(BaseModel):
    nome: Nome = Field(description="Nome completo (máx. 100 caracteres)")
    cpf: CPF = Field(description="CPF (com ou sem máscara)")
    email: Email


class AdministradorCreate(_DadosCadastraisBase):
    perfil: PerfilAdministrativo = Field(description='"Gestor" ou "Operador"')


class AdministradorUpdate(_DadosCadastraisBase):
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


class UsuarioPessoaAdminCreate(_DadosCadastraisBase):
    """Cadastro de cidadão feito pela administração (senha gerada e enviada por e-mail)."""


class IpBloqueadoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ip: str
    motivo: str
    bloqueado_em: datetime
