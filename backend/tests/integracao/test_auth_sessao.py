"""Integração — sessão: access token, refresh token (rotação) e logout.

Regras verificadas:
  * rotas protegidas exigem access token válido (401 caso contrário);
  * access token expira em 30 minutos;
  * refresh token (7 dias) gera novo par e é invalidado após o uso (rotação);
  * logout invalida imediatamente o access token e o refresh token da sessão;
  * usuário desativado perde o acesso mesmo com token ainda válido.
"""

from datetime import timedelta

import jwt
import pytest

from app.models import StatusUsuario
from tests.fabricas import autenticar, criar_pessoa, login_completo

pytestmark = pytest.mark.integracao

ROTA_PROTEGIDA = "/usuarios/me"


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


class TestAccessToken:
    def test_requisicao_sem_token_valido_e_recusada_com_401(self, client, db):
        resposta = client.get(ROTA_PROTEGIDA)
        assert resposta.status_code == 401
        assert resposta.json() == {"detail": "Não autenticado. Informe o token de acesso."}
        assert resposta.headers["WWW-Authenticate"] == "Bearer"

        pessoa = criar_pessoa(db)
        forjado = jwt.encode(
            {"sub": str(pessoa.id), "tipo": "Pessoa", "jti": "x", "exp": 9999999999},
            "segredo-do-atacante-tambem-com-mais-de-32-bytes",
            algorithm="HS256",
        )
        for token in ("abc", "a.b.c", "", forjado):
            resposta = client.get(ROTA_PROTEGIDA, headers=_bearer(token))
            assert resposta.status_code == 401, token

    def test_token_valido_da_acesso_por_exatamente_30_minutos(self, client, db, relogio):
        pessoa = criar_pessoa(db)
        cabecalho = autenticar(client, pessoa.email)
        resposta = client.get(ROTA_PROTEGIDA, headers=cabecalho)
        assert (resposta.status_code, resposta.json()["id"]) == (200, pessoa.id)

        relogio.shift(timedelta(minutes=29, seconds=59))
        assert client.get(ROTA_PROTEGIDA, headers=cabecalho).status_code == 200

        relogio.shift(timedelta(seconds=2))
        resposta = client.get(ROTA_PROTEGIDA, headers=cabecalho)
        assert resposta.status_code == 401
        assert resposta.json() == {"detail": "Sessão expirada. Faça login novamente."}

    def test_usuario_desativado_perde_acesso_com_token_ainda_valido(self, client, db):
        pessoa = criar_pessoa(db)
        cabecalho = autenticar(client, pessoa.email)
        pessoa.status = StatusUsuario.DESATIVADO
        db.commit()

        resposta = client.get(ROTA_PROTEGIDA, headers=cabecalho)
        assert resposta.status_code == 403
        assert resposta.json() == {"detail": "Conta desativada."}


def _renovar(client, refresh):
    return client.post("/auth/refresh", json={"refresh_token": refresh})


class TestRefreshToken:
    def test_refresh_gera_novo_par_e_o_antigo_nao_pode_ser_reutilizado(self, client, db):
        pessoa = criar_pessoa(db)
        sessao = login_completo(client, pessoa.email)

        resposta = _renovar(client, sessao["refresh_token"])
        assert resposta.status_code == 200
        novo = resposta.json()
        assert novo["refresh_token"] != sessao["refresh_token"]
        assert novo["access_token"] != sessao["access_token"]
        assert client.get(ROTA_PROTEGIDA, headers=_bearer(novo["access_token"])).status_code == 200

        # Rotação: após o uso, o refresh token antigo é revogado.
        reuso = _renovar(client, sessao["refresh_token"])
        assert reuso.status_code == 401
        assert reuso.json() == {"detail": "Sessão inválida ou expirada. Faça login novamente."}
        assert _renovar(client, "nao-existe").status_code == 401

    def test_refresh_token_vale_por_exatamente_7_dias(self, client, db, relogio):
        pessoa = criar_pessoa(db)
        primeiro = login_completo(client, pessoa.email)["refresh_token"]
        segundo = login_completo(client, pessoa.email)["refresh_token"]

        relogio.shift(timedelta(days=7) - timedelta(seconds=1))
        assert _renovar(client, primeiro).status_code == 200
        relogio.shift(timedelta(seconds=1))
        assert _renovar(client, segundo).status_code == 401

    def test_refresh_de_usuario_desativado_retorna_403(self, client, db):
        pessoa = criar_pessoa(db)
        refresh = login_completo(client, pessoa.email)["refresh_token"]
        pessoa.status = StatusUsuario.DESATIVADO
        db.commit()
        assert _renovar(client, refresh).status_code == 403


class TestLogout:
    def test_logout_invalida_o_access_token_e_revoga_o_refresh_token(self, client, db):
        pessoa = criar_pessoa(db)
        sessao = login_completo(client, pessoa.email)
        cabecalho = _bearer(sessao["access_token"])

        resposta = client.post(
            "/auth/logout", json={"refresh_token": sessao["refresh_token"]}, headers=cabecalho
        )
        assert resposta.status_code == 200
        assert resposta.json() == {"mensagem": "Sessão encerrada com sucesso."}

        depois = client.get(ROTA_PROTEGIDA, headers=cabecalho)
        assert depois.status_code == 401
        assert depois.json() == {"detail": "Sessão encerrada. Faça login novamente."}
        assert _renovar(client, sessao["refresh_token"]).status_code == 401

    def test_logout_nao_encerra_outras_sessoes_do_mesmo_usuario(self, client, db):
        pessoa = criar_pessoa(db)
        celular = login_completo(client, pessoa.email)
        computador = login_completo(client, pessoa.email)

        client.post(
            "/auth/logout",
            json={"refresh_token": celular["refresh_token"]},
            headers=_bearer(celular["access_token"]),
        )
        resposta = client.get(ROTA_PROTEGIDA, headers=_bearer(computador["access_token"]))
        assert resposta.status_code == 200

    def test_logout_nao_revoga_refresh_token_de_outro_usuario(self, client, db):
        # Um usuário mal-intencionado não pode derrubar a sessão de outro
        # enviando o refresh token alheio no próprio logout.
        atacante = criar_pessoa(db)
        vitima = criar_pessoa(db)
        sessao_atacante = login_completo(client, atacante.email)
        sessao_vitima = login_completo(client, vitima.email)

        client.post(
            "/auth/logout",
            json={"refresh_token": sessao_vitima["refresh_token"]},
            headers=_bearer(sessao_atacante["access_token"]),
        )
        assert _renovar(client, sessao_vitima["refresh_token"]).status_code == 200
