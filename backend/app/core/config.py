from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    RESET_TOKEN_EXPIRE_MINUTES: int = 60

    LOGIN_MAX_TENTATIVAS: int = 5
    LOGIN_BLOQUEIO_MINUTOS: int = 15

    MAIL_MODE: Literal["console", "smtp"] = "console"
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "no-reply@esportemais.local"
    SMTP_TLS: bool = False

    GESTOR_INICIAL_NOME: str
    GESTOR_INICIAL_CPF: str
    GESTOR_INICIAL_EMAIL: str
    GESTOR_INICIAL_SENHA: str

    FRONTEND_URL: str = "http://localhost:5173"

    TIMEZONE: str = "America/Sao_Paulo"
    SCHEDULER_ENABLED: bool = True
    CONCLUIR_AGENDAMENTOS_INTERVALO_MINUTOS: int = 5

settings = Settings()
