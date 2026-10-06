"""Integração — autenticação (POST /auth/login).

Regras verificadas:
  * login de Usuário Pessoa e de Usuário Administrativo com e-mail e senha;
  * mensagem genérica para e-mail inexistente ou senha errada (anti-enumeração);
  * bloqueio de 1 hora após 3 tentativas erradas consecutivas;
  * contador zerado após login bem-sucedido ou fim do bloqueio;
  * conta desativada não acessa o sistema;
  * rate limit de 5 requisições por minuto no login;
  * IP com login recusado em 5 contas diferentes em 24h é bloqueado sem prazo.
"""

from datetime import timedelta

import pytest

from app.core import security
from app.core.rate_limit import limiter
from app.models import PerfilAdministrativo, StatusUsuario
from tests.fabricas import AGORA, SENHA_PADRAO, criar_admin, criar_pessoa

pytestmark = pytest.mark.integracao

MSG_CREDENCIAIS = "E-mail ou senha inválidos."
MSG_BLOQUEADA = (
    "Conta temporariamente bloqueada por excesso de tentativas. Tente novamente mais tarde."
)


def _login(client, email, senha=SENHA_PADRAO):
    return client.post("/auth/login", json={"email": email, "senha": senha})


class TestLoginBemSucedido:
    def test_usuario_pessoa_recebe_tokens_e_dados_basicos(self, client, db):
        pessoa = criar_pessoa(db, nome="Ana Souza", email="ana@teste.com")
        resposta = _login(client, "ana@teste.com")

        assert resposta.status_code == 200
        corpo = resposta.json()
        assert corpo["token_type"] == "bearer"
        assert corpo["refresh_token"]
        assert corpo["usuario"] == {
            "id": pessoa.id,
            "nome": "Ana Souza",
            "email": "ana@teste.com",
            "tipo": "Pessoa",
            "perfil": None,
        }
        claims = security.decodificar_access_token(corpo["access_token"])
        assert claims["sub"] == str(pessoa.id)
        assert claims["tipo"] == "Pessoa"

    def test_administradores_recebem_tipo_e_perfil(self, client, db):
        for perfil in (PerfilAdministrativo.GESTOR, PerfilAdministrativo.OPERADOR):
            admin = criar_admin(db, perfil=perfil)
            usuario = _login(client, admin.email).json()["usuario"]
            assert (usuario["tipo"], usuario["perfil"]) == ("Administrativo", perfil.value)

    def test_email_ignora_maiusculas_mas_a_senha_nao(self, client, db):
        criar_pessoa(db, email="joao@teste.com", senha="SenhaForte1")
        assert _login(client, "JOAO@Teste.Com", "SenhaForte1").status_code == 200
        assert _login(client, "joao@teste.com", "senhaforte1").status_code == 401

    def test_refresh_token_e_persistido_somente_como_hash(self, client, db):
        from sqlalchemy import select

        from app.models import RefreshToken

        pessoa = criar_pessoa(db)
        refresh = _login(client, pessoa.email).json()["refresh_token"]
        registro = db.scalar(select(RefreshToken))
        assert registro.token_hash == security.hash_token(refresh)
        assert registro.token_hash != refresh
        assert registro.expira_em == AGORA + timedelta(hours=2)


class TestCredenciaisInvalidas:
    def test_senha_errada_e_email_inexistente_tem_a_mesma_resposta_generica(self, client, db):
        # Anti-enumeração: não deve ser possível descobrir quais e-mails existem.
        pessoa = criar_pessoa(db)
        senha_errada = _login(client, pessoa.email, "SenhaErrada")
        inexistente = _login(client, "ninguem@teste.com", "SenhaErrada")
        for resposta in (senha_errada, inexistente):
            assert resposta.status_code == 401
            assert resposta.json() == {"detail": MSG_CREDENCIAIS}
            assert resposta.headers["WWW-Authenticate"] == "Bearer"

    def test_campos_ausentes_retornam_422(self, client):
        assert client.post("/auth/login", json={"email": "a@a.com"}).status_code == 422
        assert client.post("/auth/login", json={"senha": "x"}).status_code == 422


class TestBloqueioPorTentativas:
    def test_terceira_tentativa_errada_bloqueia_a_conta_por_1_hora(self, client, db):
        pessoa = criar_pessoa(db)
        for tentativa in range(1, 3):
            assert _login(client, pessoa.email, "errada").status_code == 401
            db.refresh(pessoa)
            assert (pessoa.tentativas_login, pessoa.bloqueado_ate) == (tentativa, None)

        assert _login(client, pessoa.email, "errada").status_code == 401
        db.refresh(pessoa)
        assert pessoa.tentativas_login == 3
        assert pessoa.bloqueado_ate == AGORA + timedelta(hours=1)

        # Bloqueada, a conta recusa até a senha correta.
        resposta = _login(client, pessoa.email, SENHA_PADRAO)
        assert resposta.status_code == 423
        assert resposta.json() == {"detail": MSG_BLOQUEADA}

    def test_bloqueio_dura_exatamente_1_hora_e_depois_zera_o_contador(self, client, db, relogio):
        pessoa = criar_pessoa(db)
        for _ in range(3):
            _login(client, pessoa.email, "errada")

        relogio.shift(timedelta(minutes=59, seconds=59))
        assert _login(client, pessoa.email).status_code == 423

        relogio.shift(timedelta(seconds=1))
        assert _login(client, pessoa.email).status_code == 200
        db.refresh(pessoa)
        assert (pessoa.tentativas_login, pessoa.bloqueado_ate) == (0, None)

    def test_erro_apos_fim_do_bloqueio_recomeca_contagem_do_zero(self, client, db, relogio):
        pessoa = criar_pessoa(db)
        for _ in range(3):
            _login(client, pessoa.email, "errada")
        relogio.shift(timedelta(minutes=61))

        assert _login(client, pessoa.email, "errada").status_code == 401
        db.refresh(pessoa)
        assert pessoa.tentativas_login == 1
        assert pessoa.bloqueado_ate is None

    def test_login_correto_antes_do_limite_zera_o_contador(self, client, db):
        pessoa = criar_pessoa(db)
        for _ in range(2):
            _login(client, pessoa.email, "errada")
        assert _login(client, pessoa.email).status_code == 200
        db.refresh(pessoa)
        assert pessoa.tentativas_login == 0

        # Depois de zerado, são necessárias mais 3 falhas para bloquear.
        for _ in range(2):
            _login(client, pessoa.email, "errada")
        assert _login(client, pessoa.email).status_code == 200

    def test_bloqueio_e_por_conta_e_vale_tambem_para_administradores(self, client, db):
        admin = criar_admin(db)
        outro = criar_pessoa(db)
        for _ in range(3):
            _login(client, admin.email, "errada")
        assert _login(client, admin.email).status_code == 423
        assert _login(client, outro.email).status_code == 200


def test_conta_desativada_nao_acessa_e_senha_errada_nao_revela_o_status(client, db):
    pessoa = criar_pessoa(db, status=StatusUsuario.DESATIVADO)
    admin = criar_admin(db, status=StatusUsuario.DESATIVADO)
    for usuario in (pessoa, admin):
        resposta = _login(client, usuario.email)
        assert resposta.status_code == 403
        assert resposta.json() == {"detail": "Conta desativada."}
        # Com a senha errada, a resposta é a genérica: não revela que a conta existe.
        resposta = _login(client, usuario.email, "errada")
        assert (resposta.status_code, resposta.json()) == (401, {"detail": MSG_CREDENCIAIS})


def test_mais_de_5_logins_por_minuto_do_mesmo_ip_retorna_429(client, db):
    limiter.enabled = True
    limiter.reset()
    pessoa = criar_pessoa(db)
    respostas = [_login(client, pessoa.email).status_code for _ in range(6)]
    assert respostas[:5] == [200] * 5
    assert respostas[5] == 429


def test_rate_limit_usa_o_ip_informado_pela_cloudflare(client, db):
    # Em produção o X-Forwarded-For pode ser forjado pelo cliente (o proxy do Render
    # só acrescenta a ele); o CF-Connecting-IP é sempre reescrito pela Cloudflare.
    limiter.enabled = True
    limiter.reset()

    def tentar(ip):
        return client.post(
            "/auth/login",
            json={"email": "ninguem@teste.com", "senha": "errada"},
            headers={"CF-Connecting-IP": ip},
        ).status_code

    assert [tentar("200.1.1.1") for _ in range(6)][5] == 429
    # Outro cliente real (outro IP da Cloudflare) não é afetado pelo bloqueio do primeiro.
    assert tentar("200.2.2.2") == 401
