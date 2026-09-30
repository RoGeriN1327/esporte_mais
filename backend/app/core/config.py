"""Configurações da aplicação, lidas de variáveis de ambiente.

Em Docker as variáveis vêm do docker-compose.yml; rodando fora dele, do arquivo
backend/.env (modelo em backend/.env.example). Campos sem valor padrão
(DATABASE_URL e JWT_SECRET) são obrigatórios: a API não inicia se faltarem.
"""

from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str

    # HS256 exige chave de no mínimo 256 bits (RFC 7518, seção 3.2); uma chave
    # curta facilita a força bruta e a falsificação de tokens.
    JWT_SECRET: str = Field(min_length=32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    RESET_TOKEN_EXPIRE_MINUTES: int = 60

    # Bloqueio temporário da conta após N senhas erradas seguidas
    LOGIN_MAX_TENTATIVAS: int = 5
    LOGIN_BLOQUEIO_MINUTOS: int = 15

    # "console" apenas imprime o e-mail no log; "smtp" envia de verdade
    MAIL_MODE: Literal["console", "smtp"] = "console"
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "no-reply@esportemais.local"
    SMTP_TLS: bool = False

    # Primeiro Gestor, criado por scripts/seed_gestor.py na subida do container.
    # Opcionais: em produção, defina-os só no primeiro deploy e apague-os depois
    # do primeiro login (ver README). Sem eles o seed apenas não faz nada.
    GESTOR_INICIAL_NOME: str | None = None
    GESTOR_INICIAL_CPF: str | None = None
    GESTOR_INICIAL_EMAIL: str | None = None
    GESTOR_INICIAL_SENHA: str | None = None

    # Origem liberada no CORS e base dos links enviados por e-mail
    FRONTEND_URL: str = "http://localhost:5173"
    DOCS_ENABLED: bool = True

    @field_validator("DATABASE_URL")
    @classmethod
    def usar_driver_psycopg(cls, valor: str) -> str:
        # Provedores (Render, Supabase, Railway...) entregam a URL como
        # "postgres://" ou "postgresql://"; o SQLAlchemy precisa do driver explícito.
        for prefixo in ("postgres://", "postgresql://"):
            if valor.startswith(prefixo):
                return "postgresql+psycopg://" + valor.removeprefix(prefixo)
        return valor

    @field_validator("FRONTEND_URL")
    @classmethod
    def sem_barra_final(cls, valor: str) -> str:
        # O navegador envia a origem sem "/" no final; com a barra o CORS recusa
        # todas as requisições e os links dos e-mails saem com "//".
        return valor.rstrip("/")

    TIMEZONE: str = "America/Sao_Paulo"
    # Jobs periódicos (app.core.scheduler); o intervalo vale para os dois jobs
    SCHEDULER_ENABLED: bool = True
    CONCLUIR_AGENDAMENTOS_INTERVALO_MINUTOS: int = 5


settings = Settings()
