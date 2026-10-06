"""Infraestrutura comum dos testes automatizados do backend Esporte+.

As variáveis de ambiente são fixadas ANTES de importar a aplicação, pois
``app.core.config.settings`` é lido no momento do import. Assim os testes rodam
sempre com as mesmas regras (5 tentativas, bloqueio de 15 min, token de 30 min...)
e contra um banco PostgreSQL exclusivo de testes — nunca o banco de desenvolvimento.
"""

import os
from pathlib import Path

_URL_BASE = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg://esporte:esporte@localhost:5432/esporte_mais"
)
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL") or (
    _URL_BASE.rsplit("/", 1)[0] + "/esporte_mais_test"
)

os.environ.update(
    {
        "DATABASE_URL": TEST_DATABASE_URL,
        "JWT_SECRET": "segredo-exclusivo-dos-testes-com-mais-de-32-bytes",
        "JWT_ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
        "SESSAO_EXPIRE_MINUTES": "120",
        "RESET_TOKEN_EXPIRE_MINUTES": "60",
        "LOGIN_MAX_TENTATIVAS": "3",
        "LOGIN_BLOQUEIO_MINUTOS": "60",
        "IP_MAX_CONTAS_COM_FALHA": "5",
        "IP_JANELA_FALHAS_HORAS": "24",
        "MAIL_MODE": "console",
        "GESTOR_INICIAL_NOME": "Gestor Inicial",
        "GESTOR_INICIAL_CPF": "00000000000",
        "GESTOR_INICIAL_EMAIL": "gestor@esportemais.local",
        "GESTOR_INICIAL_SENHA": "Admin@2026",
        "FRONTEND_URL": "http://localhost:5173",
        "TIMEZONE": "America/Sao_Paulo",
        "SCHEDULER_ENABLED": "false",
    }
)

import bcrypt  # noqa: E402
import pytest  # noqa: E402
import time_machine  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.core.rate_limit import limiter  # noqa: E402
from app.main import app  # noqa: E402
from app.services.email_service import EmailService  # noqa: E402
from tests.fabricas import AGORA  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parents[1]


def _criar_banco_de_testes_se_necessario() -> None:
    url = make_url(TEST_DATABASE_URL)
    admin_engine = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        existe = conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :nome"), {"nome": url.database}
        )
        if not existe:
            conn.execute(text(f'CREATE DATABASE "{url.database}"'))
    admin_engine.dispose()


def _aplicar_migrations_do_zero() -> None:
    """Recria o schema e aplica TODAS as migrations do Alembic.

    Usar as migrations (e não ``create_all``) garante que os testes validem o banco
    exatamente como ele é criado em produção — inclusive os índices únicos parciais
    que impedem agendamentos duplicados.
    """
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    # Config sem arquivo .ini: evita que o logging.fileConfig do Alembic desative
    # os loggers da aplicação durante os testes.
    config = Config()
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    command.upgrade(config, "head")


@pytest.fixture(scope="session", autouse=True)
def banco_de_testes():
    _criar_banco_de_testes_se_necessario()
    _aplicar_migrations_do_zero()
    yield
    engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def bcrypt_rapido():
    """Reduz o custo do bcrypt (12 -> 4 rounds) apenas nos testes.

    O algoritmo e a verificação continuam os mesmos; só o fator de trabalho
    diminui, para a suíte não levar minutos gerando hashes.
    """
    original = bcrypt.gensalt
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(bcrypt, "gensalt", lambda rounds=4, prefix=b"2b": original(rounds, prefix))
        yield


@pytest.fixture(autouse=True)
def limpar_banco():
    yield
    tabelas = ", ".join(f'"{t.name}"' for t in Base.metadata.sorted_tables)
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {tabelas} RESTART IDENTITY CASCADE"))


@pytest.fixture(autouse=True)
def relogio():
    """Congela o relógio em segunda-feira, 04/03/2030, 08:00 (horário de Brasília).

    Regras de prazo (bloqueio de login, expiração de tokens, antecedência de
    cancelamento, lembretes, conclusão automática) dependem do "agora"; com o
    relógio fixo os testes são determinísticos. Use ``relogio.move_to(...)`` ou
    ``relogio.shift(...)`` para simular a passagem do tempo.
    """
    with time_machine.travel(AGORA, tick=False) as viajante:
        yield viajante


@pytest.fixture(autouse=True)
def sem_rate_limit():
    """Desliga o rate limit (testado isoladamente em test_auth_login.py)."""
    limiter.enabled = False
    yield
    limiter.enabled = False
    limiter.reset()


@pytest.fixture(autouse=True)
def caixa_de_email(monkeypatch):
    """Captura todos os e-mails enviados, mantendo o comportamento original."""
    enviados: list[dict] = []
    original = EmailService.enviar

    def enviar_e_capturar(self, destinatario, assunto, corpo, evento="geral", html=None):
        enviados.append(
            {
                "para": destinatario,
                "assunto": assunto,
                "corpo": corpo,
                "evento": evento,
                "html": html,
            }
        )
        return original(self, destinatario, assunto, corpo, evento, html)

    monkeypatch.setattr(EmailService, "enviar", enviar_e_capturar)
    return enviados


@pytest.fixture
def db():
    sessao = SessionLocal()
    yield sessao
    sessao.close()


@pytest.fixture
def client():
    # raise_server_exceptions=False: um erro interno vira HTTP 500 na asserção,
    # exatamente como o usuário final o perceberia.
    with TestClient(app, raise_server_exceptions=False) as cliente:
        yield cliente
