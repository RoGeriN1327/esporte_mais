"""Integração — Usuário Pessoa: auto-cadastro, perfil, edição de e-mail e desativação.

Regras verificadas:
  * cadastro público com CPF e e-mail únicos em TODO o sistema (pessoas e administradores);
  * rate limit de 5 cadastros por hora por IP;
  * senha armazenada apenas como hash; conta criada como Ativa;
  * o cidadão só altera o próprio e-mail (nome e CPF são imutáveis por ele);
  * ao desativar a própria conta: sessões encerradas, agendamentos confirmados
    cancelados, histórico preservado e e-mails de confirmação enviados.
"""

import pytest
from sqlalchemy import select

from app.core import security
from app.core.rate_limit import limiter
from app.models import StatusAgendamento, StatusUsuario, UsuarioPessoa
from tests.fabricas import (
    AMANHA,
    ONTEM,
    autenticar,
    criar_admin,
    criar_agendamento,
    criar_pessoa,
    criar_quadra,
    em,
    eventos,
    gerar_cpf,
    login_completo,
    mascarar_cpf,
)

pytestmark = pytest.mark.integracao


def _cadastro(**alteracoes) -> dict:
    dados = {
        "nome": "Carlos Pereira",
        "cpf": "529.982.247-25",
        "email": "carlos@teste.com",
        "senha": "Senha@123",
        "confirmar_senha": "Senha@123",
    }
    dados.update(alteracoes)
    return dados


def _login(client, email, senha="Senha@123"):
    return client.post("/auth/login", json={"email": email, "senha": senha})


class TestAutoCadastro:
    def test_cadastro_publico_cria_conta_ativa_com_senha_em_hash(self, client, db):
        # Sem autenticação, com CPF mascarado e e-mail com maiúsculas.
        resposta = client.post("/usuarios", json=_cadastro(email="Carlos@Teste.com"))

        assert resposta.status_code == 201
        corpo = resposta.json()
        assert corpo["nome"] == "Carlos Pereira"
        assert corpo["cpf"] == "52998224725"
        assert corpo["email"] == "carlos@teste.com"
        assert corpo["status"] == "Ativo"
        assert "senha" not in corpo

        usuario = db.get(UsuarioPessoa, corpo["id"])
        assert usuario.senha != "Senha@123"
        assert security.verificar_senha("Senha@123", usuario.senha)
        assert _login(client, "carlos@teste.com").status_code == 200

    def test_cpf_e_email_sao_unicos_em_todo_o_sistema(self, client, db):
        criar_pessoa(db, cpf=gerar_cpf(1), email="pessoa@teste.com")
        criar_admin(db, cpf=gerar_cpf(2), email="admin@rv.gov.br")
        criar_pessoa(db, cpf=gerar_cpf(3), status=StatusUsuario.DESATIVADO)
        conflitos = {
            "CPF de outra pessoa (com máscara)": ({"cpf": mascarar_cpf(gerar_cpf(1))}, "CPF"),
            "CPF de administrador": ({"cpf": gerar_cpf(2)}, "CPF"),
            "CPF de conta desativada": ({"cpf": gerar_cpf(3)}, "CPF"),
            "e-mail de outra pessoa (outra caixa)": ({"email": "PESSOA@teste.com"}, "E-mail"),
            "e-mail de administrador": ({"email": "admin@rv.gov.br"}, "E-mail"),
        }
        for caso, (dados, campo) in conflitos.items():
            resposta = client.post("/usuarios", json=_cadastro(**dados))
            assert resposta.status_code == 409, caso
            assert resposta.json() == {"detail": f"{campo} já cadastrado."}, caso

    def test_dados_invalidos_retornam_422_e_nada_e_gravado(self, client, db):
        invalidos = [
            {"cpf": "123.456.789-00"},
            {"email": "invalido"},
            {"nome": "  "},
            {"senha": "1234567", "confirmar_senha": "1234567"},
            {"confirmar_senha": "Diferente@1"},
            # Acima do limite do bcrypt: antes da correção, gerava erro interno (500).
            {"senha": "S" * 80, "confirmar_senha": "S" * 80},
        ]
        for dados in invalidos:
            assert client.post("/usuarios", json=_cadastro(**dados)).status_code == 422, dados
        assert db.scalars(select(UsuarioPessoa)).all() == []

    def test_mais_de_5_cadastros_por_hora_do_mesmo_ip_retorna_429(self, client, db):
        limiter.enabled = True
        limiter.reset()
        respostas = [
            client.post(
                "/usuarios",
                json=_cadastro(cpf=gerar_cpf(100 + i), email=f"pessoa{i}@teste.com"),
            ).status_code
            for i in range(6)
        ]
        assert respostas[:5] == [201] * 5
        assert respostas[5] == 429


def test_meu_perfil_exibe_somente_os_dados_do_usuario_autenticado(client, db):
    pessoa = criar_pessoa(db, nome="Beatriz Lima")
    criar_pessoa(db)  # outro usuário não deve aparecer
    resposta = client.get("/usuarios/me", headers=autenticar(client, pessoa.email))

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert (corpo["id"], corpo["nome"], corpo["cpf"], corpo["status"]) == (
        pessoa.id,
        "Beatriz Lima",
        pessoa.cpf,
        "Ativo",
    )
    assert "senha" not in corpo


class TestEdicaoDeEmail:
    def _editar(self, client, pessoa, dados):
        return client.patch("/usuarios/me", json=dados, headers=autenticar(client, pessoa.email))

    def test_altera_somente_o_email_e_o_login_passa_a_usar_o_novo(self, client, db):
        pessoa = criar_pessoa(db, nome="Original", email="antigo@teste.com")
        cpf_original = pessoa.cpf
        # Nome e CPF enviados junto são ignorados: o cidadão só altera o e-mail.
        dados = {"email": "Novo@Teste.com", "nome": "Hacker", "cpf": gerar_cpf(123456789)}
        resposta = self._editar(client, pessoa, dados)

        assert resposta.status_code == 200
        assert resposta.json()["email"] == "novo@teste.com"
        db.refresh(pessoa)
        assert (pessoa.email, pessoa.nome, pessoa.cpf) == (
            "novo@teste.com",
            "Original",
            cpf_original,
        )
        assert _login(client, "novo@teste.com").status_code == 200
        assert _login(client, "antigo@teste.com").status_code == 401

    def test_novo_email_precisa_ser_valido_e_nao_pertencer_a_outra_conta(self, client, db):
        pessoa = criar_pessoa(db)
        outra = criar_pessoa(db)
        admin = criar_admin(db)
        assert self._editar(client, pessoa, {"email": outra.email}).status_code == 409
        assert self._editar(client, pessoa, {"email": admin.email}).status_code == 409
        assert self._editar(client, pessoa, {"email": "sem-arroba"}).status_code == 422
        # Manter o próprio e-mail não é conflito.
        assert self._editar(client, pessoa, {"email": pessoa.email}).status_code == 200


class TestDesativacaoDaPropriaConta:
    def test_conta_desativada_encerra_todas_as_sessoes_e_bloqueia_o_login(self, client, db):
        pessoa = criar_pessoa(db)
        outra_sessao = login_completo(client, pessoa.email)
        sessao = login_completo(client, pessoa.email)
        cabecalho = {"Authorization": f"Bearer {sessao['access_token']}"}

        resposta = client.post("/usuarios/me/desativar", headers=cabecalho)
        assert resposta.status_code == 200
        assert resposta.json() == {"mensagem": "Conta desativada com sucesso."}
        db.refresh(pessoa)
        assert pessoa.status is StatusUsuario.DESATIVADO

        assert client.get("/usuarios/me", headers=cabecalho).status_code == 401
        for refresh in (sessao["refresh_token"], outra_sessao["refresh_token"]):
            assert client.post("/auth/refresh", json={"refresh_token": refresh}).status_code == 401
        assert _login(client, pessoa.email).status_code == 403

    def test_cancela_o_agendamento_confirmado_libera_o_horario_e_preserva_historico(
        self, client, db, caixa_de_email
    ):
        pessoa = criar_pessoa(db)
        quadra = criar_quadra(db)
        futuro = criar_agendamento(db, usuario=pessoa, quadra=quadra, inicio=em(AMANHA, 9))
        passado = criar_agendamento(
            db,
            usuario=pessoa,
            quadra=quadra,
            inicio=em(ONTEM, 9),
            status=StatusAgendamento.CONCLUIDO,
        )
        client.post("/usuarios/me/desativar", headers=autenticar(client, pessoa.email))

        db.refresh(futuro)
        db.refresh(passado)
        assert futuro.status is StatusAgendamento.CANCELADO
        assert passado.status is StatusAgendamento.CONCLUIDO  # histórico intacto
        assert len(eventos(caixa_de_email, "cancelamento_agendamento", para=pessoa.email)) == 1
        assert len(eventos(caixa_de_email, "confirmacao_desativacao", para=pessoa.email)) == 1

        horarios = client.get(
            f"/quadras/{quadra.id}/horarios-disponiveis",
            params={"data": AMANHA.isoformat()},
            headers=autenticar(client, criar_pessoa(db).email),
        ).json()["horarios"]
        assert "09:00:00" in horarios
