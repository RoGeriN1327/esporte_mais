"""Unitários — documentação da API (Swagger, ReDoc e /openapi.json) controlada por DOCS_ENABLED."""

import importlib

import pytest
from fastapi.testclient import TestClient

import app.main
from app.core.config import settings

pytestmark = pytest.mark.unitario

ROTAS_DE_DOCUMENTACAO = ["/docs", "/redoc", "/openapi.json"]


@pytest.fixture
def app_com_docs(monkeypatch):
    """Recria a aplicação com o valor de DOCS_ENABLED pedido (lido na criação do FastAPI)."""

    def criar(habilitado: bool):
        monkeypatch.setattr(settings, "DOCS_ENABLED", habilitado)
        return importlib.reload(app.main).app

    yield criar
    monkeypatch.undo()
    importlib.reload(app.main)


def test_documentacao_publicada_por_padrao(app_com_docs):
    cliente = TestClient(app_com_docs(True))
    for rota in ROTAS_DE_DOCUMENTACAO:
        assert cliente.get(rota).status_code == 200, rota


def test_documentacao_desligada_responde_404_e_a_api_continua_no_ar(app_com_docs):
    cliente = TestClient(app_com_docs(False))
    for rota in ROTAS_DE_DOCUMENTACAO:
        assert cliente.get(rota).status_code == 404, rota
    assert cliente.get("/health").status_code == 200
