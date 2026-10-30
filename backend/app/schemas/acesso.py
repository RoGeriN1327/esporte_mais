"""Schemas do registro de acessos e do painel secreto de consulta."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AcessoRequest(BaseModel):
    caminho: str = Field(max_length=255, description="Tela aberta (ex.: /sobre, /agendamentos)")
    id_visitante: str | None = Field(
        default=None,
        max_length=64,
        description="Id aleatório guardado no navegador, para agrupar visitas do mesmo aparelho",
    )
    referencia: str | None = Field(
        default=None, max_length=255, description="Página de origem (document.referrer)"
    )


class ConsultaPainelRequest(BaseModel):
    chave: str = Field(max_length=200)
    desde: date | None = None
    ate: date | None = None
    evento: Literal["pagina", "login", "login_recusado"] | None = None
    so_logados: bool = False


class AcessoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    criado_em: datetime
    evento: str
    caminho: str | None
    ip: str
    pais: str | None
    navegador: str
    sistema: str
    tipo_dispositivo: str
    dispositivo: str | None
    user_agent: str
    id_visitante: str | None
    referencia: str | None
    tipo_usuario: str | None
    email: str | None


class ResumoAcessosOut(BaseModel):
    total: int
    telas: int
    logins: int
    logins_recusados: int
    aparelhos: int
    ips: int


class UsuarioAcessosOut(BaseModel):
    email: str | None
    tipo: str | None
    logins: int
    telas: int
    ultimo_acesso: datetime


class ConsultaPainelOut(BaseModel):
    resumo: ResumoAcessosOut
    usuarios: list[UsuarioAcessosOut]
    acessos: list[AcessoOut]
    limite: int
