"""Schema do registro de acesso enviado pelo front a cada tela aberta."""

from pydantic import BaseModel, Field


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
