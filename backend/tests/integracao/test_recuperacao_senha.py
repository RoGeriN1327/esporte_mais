"""Integração — recuperação e redefinição de senha.

Regras verificadas:
  * o link só é enviado quando e-mail E CPF pertencem ao mesmo usuário ativo;
  * a resposta é sempre a mesma (anti-enumeração de contas);
  * o link vale por 1 hora e é de uso único;
  * redefinir a senha desbloqueia a conta e encerra as sessões abertas.
"""

import re
from datetime import timedelta

import pytest
from sqlalchemy import func, select

from app.models import Notificacao, StatusUsuario, TokenRedefinicaoSenha
from tests.fabricas import (
    AGORA,
    criar_admin,
    criar_pessoa,
    eventos,
    login_completo,
    mascarar_cpf,
)

pytestmark = pytest.mark.integracao

MSG_GENERICA = "Se o e-mail estiver cadastrado, o link será enviado."
NOVA_SENHA = "NovaSenha@2030"


def _solicitar(client, email, cpf):
    return client.post("/auth/recuperar-senha", json={"email": email, "cpf": cpf})


def _token_do_email(caixa, email) -> str:
    [mensagem] = eventos(caixa, "recuperacao_senha", para=email)
    return re.search(r"/redefinir-senha\?token=(\S+)", mensagem["corpo"]).group(1)


def _redefinir(client, token, senha=NOVA_SENHA, confirmar=None):
    return client.post(
        "/auth/redefinir-senha",
        json={"token": token, "nova_senha": senha, "confirmar_senha": confirmar or senha},
    )


def _total_tokens(db) -> int:
    return db.scalar(select(func.count()).select_from(TokenRedefinicaoSenha))


class TestSolicitacao:
    def test_email_e_cpf_corretos_enviam_link_de_1_hora(self, client, db, caixa_de_email):
        pessoa = criar_pessoa(db)
        resposta = _solicitar(client, pessoa.email, pessoa.cpf)

        assert resposta.status_code == 200
        assert resposta.json() == {"mensagem": MSG_GENERICA}
        [mensagem] = eventos(caixa_de_email, "recuperacao_senha", para=pessoa.email)
        assert "http://localhost:5173/redefinir-senha?token=" in mensagem["corpo"]
        assert "válido por 1 hora" in mensagem["corpo"]

        registro = db.scalar(select(TokenRedefinicaoSenha))
        assert registro.usuario_id == pessoa.id
        assert registro.expira_em == AGORA + timedelta(hours=1)
        # O token é guardado apenas como hash.
        assert registro.token_hash != _token_do_email(caixa_de_email, pessoa.email)
        # O envio fica no histórico de notificações.
        notificacao = db.scalar(select(Notificacao))
        assert (notificacao.destinatario, notificacao.evento, notificacao.sucesso) == (
            pessoa.email,
            "recuperacao_senha",
            True,
        )

    def test_aceita_email_em_maiusculas_cpf_com_mascara_e_administradores(
        self, client, db, caixa_de_email
    ):
        pessoa = criar_pessoa(db)
        admin = criar_admin(db)
        _solicitar(client, pessoa.email.upper(), mascarar_cpf(pessoa.cpf))
        _solicitar(client, admin.email, admin.cpf)
        assert len(eventos(caixa_de_email, "recuperacao_senha", para=pessoa.email)) == 1
        assert len(eventos(caixa_de_email, "recuperacao_senha", para=admin.email)) == 1

    def test_dados_que_nao_conferem_nao_enviam_link_e_tem_a_mesma_resposta(
        self, client, db, caixa_de_email
    ):
        # Anti-enumeração: a resposta não revela se o e-mail existe ou se o CPF confere.
        pessoa = criar_pessoa(db)
        outra = criar_pessoa(db)
        desativada = criar_pessoa(db, status=StatusUsuario.DESATIVADO)
        tentativas = {
            "CPF de outra pessoa": (pessoa.email, outra.cpf),
            "e-mail inexistente": ("ninguem@teste.com", pessoa.cpf),
            "conta desativada": (desativada.email, desativada.cpf),
        }
        for caso, (email, cpf) in tentativas.items():
            resposta = _solicitar(client, email, cpf)
            assert (resposta.status_code, resposta.json()) == (200, {"mensagem": MSG_GENERICA}), (
                caso
            )
        assert eventos(caixa_de_email, "recuperacao_senha") == []
        assert _total_tokens(db) == 0

    def test_cpf_invalido_retorna_422(self, client):
        assert _solicitar(client, "a@a.com", "123.456.789-00").status_code == 422


class TestRedefinicao:
    def test_nova_senha_passa_a_valer_e_a_antiga_deixa_de_valer(self, client, db, caixa_de_email):
        pessoa = criar_pessoa(db)
        _solicitar(client, pessoa.email, pessoa.cpf)
        resposta = _redefinir(client, _token_do_email(caixa_de_email, pessoa.email))

        assert resposta.status_code == 200
        assert resposta.json() == {
            "mensagem": "Senha redefinida com sucesso. Faça login com a nova senha."
        }
        login_novo = {"email": pessoa.email, "senha": NOVA_SENHA}
        login_antigo = {"email": pessoa.email, "senha": "Senha@123"}
        assert client.post("/auth/login", json=login_novo).status_code == 200
        assert client.post("/auth/login", json=login_antigo).status_code == 401

    def test_link_e_de_uso_unico_e_token_inventado_e_recusado(self, client, db, caixa_de_email):
        pessoa = criar_pessoa(db)
        _solicitar(client, pessoa.email, pessoa.cpf)
        token = _token_do_email(caixa_de_email, pessoa.email)
        assert _redefinir(client, token).status_code == 200

        for invalido in (token, "token-inventado"):
            resposta = _redefinir(client, invalido, "OutraSenha@1")
            assert resposta.status_code == 400
            assert resposta.json() == {"detail": "Link inválido ou expirado."}

    def test_link_vale_por_exatamente_1_hora(self, client, db, caixa_de_email, relogio):
        dentro_do_prazo = criar_pessoa(db)
        expirado = criar_pessoa(db)
        for pessoa in (dentro_do_prazo, expirado):
            _solicitar(client, pessoa.email, pessoa.cpf)

        relogio.shift(timedelta(minutes=59, seconds=59))
        token = _token_do_email(caixa_de_email, dentro_do_prazo.email)
        assert _redefinir(client, token).status_code == 200

        relogio.shift(timedelta(seconds=1))
        resposta = _redefinir(client, _token_do_email(caixa_de_email, expirado.email))
        assert resposta.status_code == 400
        assert resposta.json() == {"detail": "Link inválido ou expirado."}

    def test_redefinicao_desbloqueia_a_conta_e_encerra_as_sessoes_abertas(
        self, client, db, caixa_de_email
    ):
        pessoa = criar_pessoa(db)
        sessao = login_completo(client, pessoa.email)
        for _ in range(5):
            client.post("/auth/login", json={"email": pessoa.email, "senha": "errada"})
        _solicitar(client, pessoa.email, pessoa.cpf)
        _redefinir(client, _token_do_email(caixa_de_email, pessoa.email))

        db.refresh(pessoa)
        assert (pessoa.tentativas_login, pessoa.bloqueado_ate) == (0, None)
        login = {"email": pessoa.email, "senha": NOVA_SENHA}
        assert client.post("/auth/login", json=login).status_code == 200
        # Se a senha vazou, quem estava logado com ela não pode continuar renovando a sessão.
        resposta = client.post("/auth/refresh", json={"refresh_token": sessao["refresh_token"]})
        assert resposta.status_code == 401

    def test_senha_invalida_e_recusada_e_o_link_continua_valido(self, client, db, caixa_de_email):
        pessoa = criar_pessoa(db)
        _solicitar(client, pessoa.email, pessoa.cpf)
        token = _token_do_email(caixa_de_email, pessoa.email)
        assert _redefinir(client, token, "curta").status_code == 422
        assert _redefinir(client, token, NOVA_SENHA, "Diferente@1").status_code == 422
        assert _redefinir(client, token).status_code == 200
