"""Integração — administração de usuários (Gestor e Operador).

Regras verificadas:
  * somente o Gestor gerencia administradores (listar, cadastrar, editar, desativar);
  * Gestor e Operador gerenciam cidadãos (listar, cadastrar, desativar, reativar);
  * contas criadas pela administração recebem senha temporária por e-mail;
  * CPF e e-mail únicos em todo o sistema;
  * o Gestor não pode desativar a própria conta;
  * desativação encerra sessões; mudança de perfil vale imediatamente.
"""

import re

import pytest
from sqlalchemy import select

from app.models import (
    PerfilAdministrativo,
    StatusAgendamento,
    StatusUsuario,
    UsuarioAdministrativo,
    UsuarioPessoa,
)
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
)

pytestmark = pytest.mark.integracao

GESTOR = PerfilAdministrativo.GESTOR
OPERADOR = PerfilAdministrativo.OPERADOR


@pytest.fixture
def gestor(db):
    return criar_admin(db, perfil=GESTOR)


@pytest.fixture
def auth_gestor(client, gestor):
    return autenticar(client, gestor.email)


@pytest.fixture
def auth_operador(client, db):
    return autenticar(client, criar_admin(db, perfil=OPERADOR).email)


def _novo_admin(**alteracoes) -> dict:
    dados = {
        "nome": "Paula Operadora",
        "cpf": gerar_cpf(555000111),
        "email": "paula@rioverde.go.gov.br",
        "perfil": "Operador",
    }
    dados.update(alteracoes)
    return dados


def _senha_do_email(caixa, evento, email) -> str:
    [mensagem] = eventos(caixa, evento, para=email)
    return re.search(r"\n\s{4}(\S+)\n", mensagem["corpo"]).group(1)


def _login(client, email, senha="Senha@123"):
    return client.post("/auth/login", json={"email": email, "senha": senha})


class TestAdministradores:
    def test_gestor_lista_ativos_e_desativados(self, client, db, gestor, auth_gestor):
        criar_admin(db, perfil=OPERADOR, status=StatusUsuario.DESATIVADO)
        resposta = client.get("/admin/administradores", headers=auth_gestor)
        assert resposta.status_code == 200
        assert {a["status"] for a in resposta.json()} == {"Ativo", "Desativado"}
        assert all("senha" not in a for a in resposta.json())

    def test_gestor_cadastra_gestor_ou_operador_que_recebe_senha_temporaria(
        self, client, auth_gestor, caixa_de_email
    ):
        for n, perfil in enumerate(("Operador", "Gestor")):
            email = f"novo{n}@rioverde.go.gov.br"
            dados = _novo_admin(perfil=perfil, email=email, cpf=gerar_cpf(555000111 + n))
            resposta = client.post("/admin/administradores", json=dados, headers=auth_gestor)

            assert resposta.status_code == 201
            assert (resposta.json()["perfil"], resposta.json()["status"]) == (perfil, "Ativo")
            senha = _senha_do_email(caixa_de_email, "boas_vindas_administrador", email)
            assert len(senha) == 12
            login = _login(client, email, senha)
            assert (login.status_code, login.json()["usuario"]["perfil"]) == (200, perfil)

    def test_cadastro_exige_cpf_e_email_unicos_e_perfil_valido(
        self, client, db, gestor, auth_gestor
    ):
        pessoa = criar_pessoa(db)
        conflitos = [
            _novo_admin(cpf=pessoa.cpf),
            _novo_admin(email=pessoa.email),
            _novo_admin(email=gestor.email),
        ]
        for dados in conflitos:
            resposta = client.post("/admin/administradores", json=dados, headers=auth_gestor)
            assert resposta.status_code == 409, dados
        resposta = client.post(
            "/admin/administradores", json=_novo_admin(perfil="Root"), headers=auth_gestor
        )
        assert resposta.status_code == 422

    def test_operador_nao_cadastra_nem_desativa_administradores(
        self, client, db, gestor, auth_operador
    ):
        resposta = client.post("/admin/administradores", json=_novo_admin(), headers=auth_operador)
        assert resposta.status_code == 403
        assert resposta.json() == {"detail": "Acesso restrito ao perfil Gestor."}
        novo = select(UsuarioAdministrativo).where(
            UsuarioAdministrativo.email == "paula@rioverde.go.gov.br"
        )
        assert db.scalar(novo) is None

        url = f"/admin/administradores/{gestor.id}/desativar"
        assert client.post(url, headers=auth_operador).status_code == 403
        db.refresh(gestor)
        assert gestor.status is StatusUsuario.ATIVO

    def test_gestor_edita_dados_e_perfil(self, client, db, auth_gestor):
        operador = criar_admin(db, perfil=OPERADOR)
        novo_cpf = gerar_cpf(777000111)
        dados = _novo_admin(nome="Nome Novo", cpf=novo_cpf, email="novo@rv.gov.br", perfil="Gestor")
        url = f"/admin/administradores/{operador.id}"
        assert client.put(url, json=dados, headers=auth_gestor).status_code == 200
        db.refresh(operador)
        assert (operador.nome, operador.cpf, operador.email, operador.perfil) == (
            "Nome Novo",
            novo_cpf,
            "novo@rv.gov.br",
            GESTOR,
        )
        # Manter o próprio CPF e e-mail não é conflito.
        dados = _novo_admin(cpf=novo_cpf, email="novo@rv.gov.br")
        assert client.put(url, json=dados, headers=auth_gestor).status_code == 200

    def test_edicao_recusa_email_de_outro_usuario_e_administrador_inexistente(
        self, client, db, gestor, auth_gestor
    ):
        operador = criar_admin(db, perfil=OPERADOR)
        resposta = client.put(
            f"/admin/administradores/{operador.id}",
            json=_novo_admin(email=gestor.email),
            headers=auth_gestor,
        )
        assert resposta.status_code == 409
        resposta = client.put(
            "/admin/administradores/9999", json=_novo_admin(), headers=auth_gestor
        )
        assert resposta.status_code == 404

    def test_rebaixar_gestor_a_operador_retira_o_acesso_imediatamente(
        self, client, db, auth_gestor
    ):
        # Um Gestor rebaixado a Operador não pode continuar usando funções de Gestor
        # com o token emitido antes da alteração.
        outro_gestor = criar_admin(db, perfil=GESTOR)
        auth_outro = autenticar(client, outro_gestor.email)
        assert client.get("/admin/administradores", headers=auth_outro).status_code == 200

        client.put(
            f"/admin/administradores/{outro_gestor.id}",
            json=_novo_admin(cpf=outro_gestor.cpf, email=outro_gestor.email, perfil="Operador"),
            headers=auth_gestor,
        )
        assert client.get("/admin/administradores", headers=auth_outro).status_code == 403

    def test_gestor_desativa_operador_e_encerra_suas_sessoes(self, client, db, auth_gestor):
        operador = criar_admin(db, perfil=OPERADOR)
        sessao = login_completo(client, operador.email)

        url = f"/admin/administradores/{operador.id}/desativar"
        assert client.post(url, headers=auth_gestor).status_code == 200
        db.refresh(operador)
        assert operador.status is StatusUsuario.DESATIVADO
        cabecalho = {"Authorization": f"Bearer {sessao['access_token']}"}
        assert client.get("/admin/usuarios-pessoa", headers=cabecalho).status_code == 403
        # O refresh token foi revogado na desativação: a sessão não pode ser renovada.
        refresh = {"refresh_token": sessao["refresh_token"]}
        assert client.post("/auth/refresh", json=refresh).status_code == 401

    def test_gestor_nao_desativa_a_si_mesmo_nem_administrador_inexistente(
        self, client, db, gestor, auth_gestor
    ):
        resposta = client.post(f"/admin/administradores/{gestor.id}/desativar", headers=auth_gestor)
        assert resposta.status_code == 400
        assert resposta.json() == {"detail": "Auto desativação administrativa não é permitida."}
        db.refresh(gestor)
        assert gestor.status is StatusUsuario.ATIVO

        resposta = client.post("/admin/administradores/9999/desativar", headers=auth_gestor)
        assert resposta.status_code == 404


def _nova_pessoa(**alteracoes) -> dict:
    dados = {"nome": "Seu José", "cpf": gerar_cpf(333222111), "email": "jose@teste.com"}
    dados.update(alteracoes)
    return dados


class TestGestaoDeCidadaos:
    def test_gestor_e_operador_listam_cidadaos_ativos_e_desativados(self, client, db):
        criar_pessoa(db)
        criar_pessoa(db, status=StatusUsuario.DESATIVADO)
        for perfil in (GESTOR, OPERADOR):
            cabecalho = autenticar(client, criar_admin(db, perfil=perfil).email)
            resposta = client.get("/admin/usuarios-pessoa", headers=cabecalho)
            assert resposta.status_code == 200, perfil
            assert len(resposta.json()) == 2, perfil

    def test_operador_cadastra_cidadao_que_recebe_senha_por_email(
        self, client, auth_operador, caixa_de_email
    ):
        resposta = client.post("/admin/usuarios-pessoa", json=_nova_pessoa(), headers=auth_operador)
        assert resposta.status_code == 201
        assert resposta.json()["status"] == "Ativo"

        senha = _senha_do_email(caixa_de_email, "boas_vindas_pessoa", "jose@teste.com")
        assert _login(client, "jose@teste.com", senha).status_code == 200

    def test_cadastro_de_cidadao_recusa_cpf_em_uso_ou_invalido_sem_gravar(
        self, client, db, gestor, auth_operador
    ):
        em_uso = client.post(
            "/admin/usuarios-pessoa", json=_nova_pessoa(cpf=gestor.cpf), headers=auth_operador
        )
        invalido = client.post(
            "/admin/usuarios-pessoa", json=_nova_pessoa(cpf="11111111111"), headers=auth_operador
        )
        assert (em_uso.status_code, invalido.status_code) == (409, 422)
        assert db.scalars(select(UsuarioPessoa)).all() == []

    def test_desativar_cidadao_cancela_agendamento_ativo_e_encerra_sessao(
        self, client, db, auth_operador, caixa_de_email
    ):
        pessoa = criar_pessoa(db)
        quadra = criar_quadra(db)
        ativo = criar_agendamento(db, usuario=pessoa, quadra=quadra, inicio=em(AMANHA, 10))
        concluido = criar_agendamento(
            db,
            usuario=pessoa,
            quadra=quadra,
            inicio=em(ONTEM, 10),
            status=StatusAgendamento.CONCLUIDO,
        )
        sessao = login_completo(client, pessoa.email)

        url = f"/admin/usuarios-pessoa/{pessoa.id}/desativar"
        assert client.post(url, headers=auth_operador).status_code == 200
        for registro in (pessoa, ativo, concluido):
            db.refresh(registro)
        assert pessoa.status is StatusUsuario.DESATIVADO
        assert ativo.status is StatusAgendamento.CANCELADO
        assert concluido.status is StatusAgendamento.CONCLUIDO
        refresh = {"refresh_token": sessao["refresh_token"]}
        assert client.post("/auth/refresh", json=refresh).status_code == 401
        assert len(eventos(caixa_de_email, "confirmacao_desativacao", para=pessoa.email)) == 1
        assert len(eventos(caixa_de_email, "cancelamento_agendamento", para=pessoa.email)) == 1

    def test_reativar_cidadao_restaura_login_com_a_senha_anterior(self, client, db, auth_operador):
        pessoa = criar_pessoa(db, status=StatusUsuario.DESATIVADO)
        pessoa.tentativas_login = 5
        db.commit()

        url = f"/admin/usuarios-pessoa/{pessoa.id}/reativar"
        resposta = client.post(url, headers=auth_operador)
        assert (resposta.status_code, resposta.json()["status"]) == (200, "Ativo")
        db.refresh(pessoa)
        assert pessoa.tentativas_login == 0
        assert _login(client, pessoa.email).status_code == 200

    def test_acoes_sobre_cidadao_inexistente_retornam_404(self, client, auth_operador):
        for acao in ("desativar", "reativar"):
            url = f"/admin/usuarios-pessoa/9999/{acao}"
            assert client.post(url, headers=auth_operador).status_code == 404, acao
