"""Integração — CPF mascarado na área administrativa.

Regras verificadas:
  * listagens e respostas da administração devolvem o CPF como ***.982.247-**;
  * o CPF completo não aparece em nenhuma resposta da área administrativa;
  * o próprio cidadão continua vendo o seu CPF completo no perfil;
  * a busca de cidadãos por CPF é feita na API, com o CPF completo;
  * editar um administrador sem informar o CPF mantém o atual.
"""

import pytest

from app.models import PerfilAdministrativo
from app.utils.cpf import ocultar_cpf
from tests.fabricas import (
    AMANHA,
    autenticar,
    criar_admin,
    criar_agendamento,
    criar_pessoa,
    criar_quadra,
    em,
    gerar_cpf,
    mascarar_cpf,
)

pytestmark = pytest.mark.integracao


@pytest.fixture
def gestor(db):
    return criar_admin(db, perfil=PerfilAdministrativo.GESTOR)


@pytest.fixture
def auth_gestor(client, gestor):
    return autenticar(client, gestor.email)


def test_ocultar_cpf():
    assert ocultar_cpf("52998224725") == "***.982.247-**"
    assert ocultar_cpf("529.982.247-25") == "***.982.247-**"
    # Já mascarado ou inválido: devolve como veio.
    assert ocultar_cpf("***.982.247-**") == "***.982.247-**"
    assert ocultar_cpf("123") == "123"


class TestListagens:
    def test_nenhuma_resposta_da_administracao_traz_o_cpf_completo(
        self, client, db, gestor, auth_gestor
    ):
        pessoa = criar_pessoa(db)
        operador = criar_admin(db, perfil=PerfilAdministrativo.OPERADOR)
        criar_agendamento(db, usuario=pessoa, quadra=criar_quadra(db), inicio=em(AMANHA, 9))

        respostas = {
            rota: client.get(rota, headers=auth_gestor)
            for rota in ("/admin/usuarios-pessoa", "/admin/administradores", "/admin/agendamentos")
        }
        for rota, resposta in respostas.items():
            assert resposta.status_code == 200, rota
            for cpf in (pessoa.cpf, operador.cpf, gestor.cpf):
                assert cpf not in resposta.text, rota
                assert mascarar_cpf(cpf) not in resposta.text, rota

        [cidadao] = respostas["/admin/usuarios-pessoa"].json()
        assert cidadao["cpf"] == ocultar_cpf(pessoa.cpf)
        cpfs_admins = {a["cpf"] for a in respostas["/admin/administradores"].json()}
        assert cpfs_admins == {ocultar_cpf(gestor.cpf), ocultar_cpf(operador.cpf)}
        [agendamento] = respostas["/admin/agendamentos"].json()
        assert agendamento["cpf_usuario"] == ocultar_cpf(pessoa.cpf)

    def test_cadastros_e_reativacao_respondem_com_cpf_mascarado(self, client, db, auth_gestor):
        cpf_pessoa, cpf_admin = gerar_cpf(444000111), gerar_cpf(444000222)
        pessoa = client.post(
            "/admin/usuarios-pessoa",
            json={"nome": "Seu José", "cpf": cpf_pessoa, "email": "jose@teste.com"},
            headers=auth_gestor,
        )
        admin = client.post(
            "/admin/administradores",
            json={"nome": "Paula", "cpf": cpf_admin, "email": "p@rv.gov.br", "perfil": "Operador"},
            headers=auth_gestor,
        )
        assert pessoa.json()["cpf"] == ocultar_cpf(cpf_pessoa)
        assert admin.json()["cpf"] == ocultar_cpf(cpf_admin)

        usuario_id = pessoa.json()["id"]
        client.post(f"/admin/usuarios-pessoa/{usuario_id}/desativar", headers=auth_gestor)
        reativado = client.post(
            f"/admin/usuarios-pessoa/{usuario_id}/reativar", headers=auth_gestor
        )
        assert reativado.json()["cpf"] == ocultar_cpf(cpf_pessoa)

    def test_cidadao_ve_o_proprio_cpf_completo(self, client, db):
        pessoa = criar_pessoa(db)
        perfil = client.get("/usuarios/me", headers=autenticar(client, pessoa.email))
        assert perfil.json()["cpf"] == pessoa.cpf


class TestBuscaPorCpf:
    def test_busca_pelo_cpf_completo_com_ou_sem_mascara(self, client, db, auth_gestor):
        ana = criar_pessoa(db, nome="Ana")
        criar_pessoa(db, nome="Bia")
        for cpf in (ana.cpf, mascarar_cpf(ana.cpf)):
            resposta = client.get(
                "/admin/usuarios-pessoa", params={"cpf": cpf}, headers=auth_gestor
            )
            assert [u["nome"] for u in resposta.json()] == ["Ana"]

    def test_cpf_parcial_ou_inexistente_nao_encontra(self, client, db, auth_gestor):
        ana = criar_pessoa(db)
        for cpf in (ana.cpf[:6], gerar_cpf(999000111)):
            resposta = client.get(
                "/admin/usuarios-pessoa", params={"cpf": cpf}, headers=auth_gestor
            )
            assert resposta.json() == []


class TestEdicaoDeAdministrador:
    def _editar(self, client, auth, admin, **dados):
        corpo = {"nome": admin.nome, "email": admin.email, "perfil": "Operador", **dados}
        return client.put(f"/admin/administradores/{admin.id}", json=corpo, headers=auth)

    def test_sem_cpf_mantem_o_atual(self, client, db, auth_gestor):
        operador = criar_admin(db, perfil=PerfilAdministrativo.OPERADOR)
        cpf_original = operador.cpf
        resposta = self._editar(client, auth_gestor, operador, nome="Nome Novo")
        assert resposta.status_code == 200
        db.refresh(operador)
        assert (operador.nome, operador.cpf) == ("Nome Novo", cpf_original)

    def test_com_cpf_corrige_o_cadastro(self, client, db, auth_gestor):
        operador = criar_admin(db, perfil=PerfilAdministrativo.OPERADOR)
        novo = gerar_cpf(888000111)
        assert self._editar(client, auth_gestor, operador, cpf=novo).status_code == 200
        db.refresh(operador)
        assert operador.cpf == novo

    def test_cpf_mascarado_na_edicao_e_recusado(self, client, db, auth_gestor):
        operador = criar_admin(db, perfil=PerfilAdministrativo.OPERADOR)
        resposta = self._editar(client, auth_gestor, operador, cpf=ocultar_cpf(operador.cpf))
        assert resposta.status_code == 422
