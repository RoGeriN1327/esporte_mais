"""Integração — registro de acessos (telas abertas e logins).

Regras verificadas:
  * cada tela aberta grava IP, país, navegador, sistema, dispositivo e o visitante;
  * com login, o acesso fica ligado ao usuário; token inválido não recusa o registro;
  * login com sucesso e login recusado (com o e-mail digitado) são gravados, nunca a senha;
  * robôs, monitores e ferramentas automáticas não são gravados, nem a rota /health;
  * uma falha ao gravar nunca atrapalha a tela nem o login.
"""

import pytest
from sqlalchemy import select

from app.models import Acesso
from app.services import acesso_service
from tests.fabricas import SENHA_PADRAO, autenticar, criar_pessoa

pytestmark = pytest.mark.integracao

CELULAR = (
    "Mozilla/5.0 (Linux; Android 13; SM-A536E) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
)
COMPUTADOR = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
IPHONE = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1"
)
ROBOS = [
    "Mozilla/5.0+(compatible; UptimeRobot/2.0; http://www.uptimerobot.com/)",
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "curl/8.5.0",
    "python-requests/2.31.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 HeadlessChrome/120.0.0.0 Safari/537.36",
    "WhatsApp/2.23.20.0",
    "",
]


def _cabecalhos(user_agent=COMPUTADOR, ip="200.10.20.30", **extras):
    return {"User-Agent": user_agent, "CF-Connecting-IP": ip, **extras}


def _acessos(db) -> list[Acesso]:
    db.expire_all()
    return list(db.scalars(select(Acesso).order_by(Acesso.id)))


def _abrir_tela(client, caminho="/sobre", headers=None, **corpo):
    return client.post(
        "/acessos", json={"caminho": caminho, **corpo}, headers=headers or _cabecalhos()
    )


class TestTelaAberta:
    def test_grava_ip_pais_navegador_e_dispositivo_do_celular(self, client, db):
        resposta = _abrir_tela(
            client,
            "/quadras",
            headers=_cabecalhos(CELULAR, "177.1.2.3", **{"CF-IPCountry": "BR"}),
            id_visitante="abc-123",
            referencia="https://www.google.com/",
        )
        assert resposta.status_code == 204

        [acesso] = _acessos(db)
        assert acesso.evento == "pagina"
        assert acesso.caminho == "/quadras"
        assert acesso.ip == "177.1.2.3"
        assert acesso.pais == "BR"
        assert acesso.navegador.startswith("Chrome Mobile 120")
        assert acesso.sistema == "Android 13"
        assert acesso.tipo_dispositivo == "Celular"
        assert acesso.dispositivo == "Samsung SM-A536E"
        assert acesso.user_agent == CELULAR
        assert acesso.id_visitante == "abc-123"
        assert acesso.referencia == "https://www.google.com/"
        assert acesso.usuario_id is None and acesso.email is None
        assert acesso.criado_em is not None

    def test_computador_e_iphone(self, client, db):
        _abrir_tela(client, headers=_cabecalhos(COMPUTADOR))
        _abrir_tela(client, headers=_cabecalhos(IPHONE))

        computador, iphone = _acessos(db)
        assert (computador.tipo_dispositivo, computador.sistema) == ("Computador", "Windows 10")
        assert computador.navegador.startswith("Chrome 120")
        assert computador.dispositivo is None
        assert (iphone.tipo_dispositivo, iphone.dispositivo) == ("Celular", "Apple iPhone")
        assert iphone.sistema.startswith("iOS 17")

    def test_com_login_liga_o_acesso_ao_usuario(self, client, db):
        pessoa = criar_pessoa(db)
        headers = {**autenticar(client, pessoa.email), **_cabecalhos()}
        _abrir_tela(client, "/agendamentos", headers=headers)

        acesso = _acessos(db)[-1]
        assert (acesso.tipo_usuario, acesso.usuario_id, acesso.email) == (
            "Pessoa",
            pessoa.id,
            pessoa.email,
        )

    def test_token_invalido_registra_como_anonimo(self, client, db):
        headers = {"Authorization": "Bearer lixo", **_cabecalhos()}
        assert _abrir_tela(client, headers=headers).status_code == 204
        [acesso] = _acessos(db)
        assert acesso.usuario_id is None

    def test_sem_cloudflare_usa_o_ip_da_conexao(self, client, db):
        client.post("/acessos", json={"caminho": "/"}, headers={"User-Agent": COMPUTADOR})
        [acesso] = _acessos(db)
        assert acesso.ip and acesso.pais is None

    @pytest.mark.parametrize("user_agent", ROBOS)
    def test_robos_e_ferramentas_nao_sao_gravados(self, client, db, user_agent):
        assert _abrir_tela(client, headers=_cabecalhos(user_agent)).status_code == 204
        assert _acessos(db) == []

    def test_health_nao_e_gravado(self, client, db):
        assert client.get("/health", headers=_cabecalhos()).status_code == 200
        assert client.head("/health", headers=_cabecalhos()).status_code == 200
        assert _acessos(db) == []

    @pytest.mark.parametrize(
        "corpo",
        [{}, {"caminho": "x" * 256}, {"caminho": "/", "id_visitante": "x" * 65}],
    )
    def test_dados_invalidos_sao_recusados(self, client, db, corpo):
        assert client.post("/acessos", json=corpo, headers=_cabecalhos()).status_code == 422
        assert _acessos(db) == []

    def test_falha_ao_gravar_nao_atrapalha(self, client, db, monkeypatch):
        def quebrar():
            raise RuntimeError("banco fora do ar")

        monkeypatch.setattr(acesso_service, "SessionLocal", quebrar)
        assert _abrir_tela(client).status_code == 204


class TestLogin:
    def test_login_com_sucesso_e_gravado_com_o_usuario(self, client, db):
        pessoa = criar_pessoa(db)
        resposta = client.post(
            "/auth/login",
            json={"email": pessoa.email, "senha": SENHA_PADRAO},
            headers=_cabecalhos(CELULAR),
        )
        assert resposta.status_code == 200

        [acesso] = _acessos(db)
        assert acesso.evento == "login"
        assert (acesso.tipo_usuario, acesso.usuario_id, acesso.email) == (
            "Pessoa",
            pessoa.id,
            pessoa.email,
        )
        assert acesso.tipo_dispositivo == "Celular"

    def test_login_recusado_grava_o_email_digitado_e_nunca_a_senha(self, client, db):
        resposta = client.post(
            "/auth/login",
            json={"email": "Fulano@Teste.com", "senha": "senha-secreta"},
            headers=_cabecalhos(),
        )
        assert resposta.status_code == 401

        [acesso] = _acessos(db)
        assert acesso.evento == "login_recusado"
        assert acesso.email == "fulano@teste.com"
        assert acesso.usuario_id is None
        valores = [str(getattr(acesso, c.key)) for c in Acesso.__table__.columns]
        assert not any("senha-secreta" in v for v in valores)

    def test_falha_ao_gravar_nao_atrapalha_o_login(self, client, db, monkeypatch):
        def quebrar():
            raise RuntimeError("banco fora do ar")

        monkeypatch.setattr(acesso_service, "SessionLocal", quebrar)
        pessoa = criar_pessoa(db)
        ok = client.post(
            "/auth/login",
            json={"email": pessoa.email, "senha": SENHA_PADRAO},
            headers=_cabecalhos(),
        )
        errado = client.post(
            "/auth/login", json={"email": pessoa.email, "senha": "errada"}, headers=_cabecalhos()
        )
        assert (ok.status_code, errado.status_code) == (200, 401)
