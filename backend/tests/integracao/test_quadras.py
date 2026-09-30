"""Integração — consulta de quadras e gestão de quadras.

Regras verificadas (consulta):
  * apenas quadras ativas são exibidas ao cidadão, com filtros de esporte, nome e bairro;
  * horários disponíveis = grade da quadra - horários ocupados - horários passados;
  * datas passadas são recusadas; quadra desativada não aceita consulta de horários.

Regras verificadas (gestão, Gestor e Operador):
  * cadastro com múltiplos esportes gera um registro independente por esporte;
  * edição substitui a grade sem afetar agendamentos existentes;
  * desativação impede novos agendamentos, preservando os existentes.
"""

from datetime import time

import pytest

from app.models import PerfilAdministrativo, Quadra, StatusAgendamento, StatusQuadra
from tests.fabricas import (
    AMANHA,
    HOJE,
    ONTEM,
    autenticar,
    criar_admin,
    criar_agendamento,
    criar_pessoa,
    criar_quadra,
    em,
)

pytestmark = pytest.mark.integracao


@pytest.fixture
def auth_pessoa(client, db):
    return autenticar(client, criar_pessoa(db).email)


@pytest.fixture
def auth_admin(client, db):
    return autenticar(client, criar_admin(db).email)


def _horarios(client, quadra_id, dia, cabecalho):
    return client.get(
        f"/quadras/{quadra_id}/horarios-disponiveis",
        params={"data": dia.isoformat()},
        headers=cabecalho,
    )


def _nomes(resposta) -> list[str]:
    return [q["nome"] for q in resposta.json()]


class TestConsultaDeQuadras:
    def test_lista_somente_quadras_ativas_ordenadas_por_nome_e_esporte(
        self, client, db, auth_pessoa
    ):
        criar_quadra(db, nome="Zeta", esporte="Futsal")
        criar_quadra(db, nome="Alfa", esporte="Vôlei")
        criar_quadra(db, nome="Alfa", esporte="Basquete")
        criar_quadra(db, nome="Desativada", status=StatusQuadra.DESATIVADA)
        resposta = client.get("/quadras", headers=auth_pessoa)
        assert resposta.status_code == 200
        assert [(q["nome"], q["esporte"]) for q in resposta.json()] == [
            ("Alfa", "Basquete"),
            ("Alfa", "Vôlei"),
            ("Zeta", "Futsal"),
        ]

    def test_filtros_por_esporte_nome_e_bairro(self, client, db, auth_pessoa):
        criar_quadra(db, nome="Ginásio Municipal", esporte="Futsal", bairro="Centro")
        criar_quadra(db, nome="Arena Centro", esporte="Futebol", bairro="Centro")
        criar_quadra(db, nome="Arena Sul", esporte="Futsal", bairro="Jardim Goiás")

        def filtrar(**params):
            return _nomes(client.get("/quadras", params=params, headers=auth_pessoa))

        assert filtrar(esporte="Futsal") == ["Arena Sul", "Ginásio Municipal"]  # exato
        assert filtrar(nome="muni") == ["Ginásio Municipal"]  # parcial, sem caixa
        assert filtrar(bairro="Jardim Goiás") == ["Arena Sul"]
        assert filtrar(esporte="Futsal", bairro="Centro") == ["Ginásio Municipal"]

    def test_opcoes_de_filtro_consideram_apenas_quadras_ativas(self, client, db, auth_pessoa):
        criar_quadra(db, esporte="Vôlei", bairro="Centro")
        criar_quadra(db, esporte="Futsal", bairro="Centro")
        criar_quadra(db, esporte="Tênis", bairro="Setor Oculto", status=StatusQuadra.DESATIVADA)
        resposta = client.get("/quadras/filtros", headers=auth_pessoa)
        assert resposta.json() == {"esportes": ["Futsal", "Vôlei"], "bairros": ["Centro"]}


class TestHorariosDisponiveis:
    def test_horarios_vem_da_grade_do_dia_da_semana(self, client, db, auth_pessoa):
        quadra = criar_quadra(db)
        resposta = _horarios(client, quadra.id, AMANHA, auth_pessoa)
        assert resposta.status_code == 200
        assert resposta.json() == {
            "id_quadra": quadra.id,
            "data": AMANHA.isoformat(),
            "horarios": ["08:00:00", "09:00:00", "10:00:00", "11:00:00"],
        }
        so_segunda = criar_quadra(db, faixas=[(0, time(8), time(12))])
        assert _horarios(client, so_segunda.id, AMANHA, auth_pessoa).json()["horarios"] == []

    def test_somente_agendamento_confirmado_na_mesma_quadra_ocupa_o_horario(
        self, client, db, auth_pessoa
    ):
        quadra = criar_quadra(db, nome="A")
        outra = criar_quadra(db, nome="B")
        criar_agendamento(db, usuario=criar_pessoa(db), quadra=quadra, inicio=em(AMANHA, 9))
        for status in (
            StatusAgendamento.CANCELADO,
            StatusAgendamento.CONCLUIDO,
            StatusAgendamento.RENOVADO,
        ):
            criar_agendamento(
                db, usuario=criar_pessoa(db), quadra=quadra, inicio=em(AMANHA, 10), status=status
            )
        criar_agendamento(db, usuario=criar_pessoa(db), quadra=outra, inicio=em(AMANHA, 11))

        horarios = _horarios(client, quadra.id, AMANHA, auth_pessoa).json()["horarios"]
        assert horarios == ["08:00:00", "10:00:00", "11:00:00"]

    def test_hoje_exibe_apenas_horarios_futuros(self, client, db, relogio):
        quadra = criar_quadra(db)
        relogio.move_to(em(HOJE, 9, 30))
        auth_pessoa = autenticar(client, criar_pessoa(db).email)
        assert _horarios(client, quadra.id, HOJE, auth_pessoa).json()["horarios"] == [
            "10:00:00",
            "11:00:00",
        ]

    def test_data_passada_ou_em_formato_invalido_e_recusada(self, client, db, auth_pessoa):
        quadra = criar_quadra(db)
        resposta = _horarios(client, quadra.id, ONTEM, auth_pessoa)
        assert resposta.status_code == 400
        assert resposta.json() == {"detail": "A data deve ser a partir de hoje."}
        resposta = client.get(
            f"/quadras/{quadra.id}/horarios-disponiveis",
            params={"data": "05/03/2030"},
            headers=auth_pessoa,
        )
        assert resposta.status_code == 422

    def test_quadra_desativada_ou_inexistente_retorna_404(self, client, db, auth_pessoa):
        quadra = criar_quadra(db, status=StatusQuadra.DESATIVADA)
        for quadra_id in (quadra.id, 9999):
            resposta = _horarios(client, quadra_id, AMANHA, auth_pessoa)
            assert resposta.status_code == 404
            assert resposta.json() == {"detail": "Quadra não encontrada."}


def _quadra_payload(**alteracoes) -> dict:
    dados = {
        "nome": "Poliesportivo Vila Borges",
        "endereco": "Av. Presidente Vargas, 500",
        "bairro": "Vila Borges",
        "descricao": "Quadra coberta com arquibancada",
        "esportes": ["Futsal"],
        "faixas": [
            {"dia_semana": 1, "hora_inicio": "08:00", "hora_fim": "10:00"},
            {"dia_semana": 1, "hora_inicio": "18:00", "hora_fim": "20:00"},
        ],
    }
    dados.update(alteracoes)
    return dados


def _edicao_payload(**alteracoes) -> dict:
    dados = _quadra_payload()
    del dados["esportes"]
    dados["esporte"] = "Futsal"
    dados.update(alteracoes)
    return dados


class TestCadastroDeQuadras:
    def test_operador_cadastra_quadra_que_ja_oferece_horarios(self, client, db, auth_pessoa):
        operador = criar_admin(db, perfil=PerfilAdministrativo.OPERADOR)
        resposta = client.post(
            "/admin/quadras", json=_quadra_payload(), headers=autenticar(client, operador.email)
        )
        assert resposta.status_code == 201
        [quadra] = resposta.json()
        assert (quadra["status"], quadra["esporte"]) == ("Ativa", "Futsal")
        assert quadra["faixas"] == [
            {"dia_semana": 1, "hora_inicio": "08:00:00", "hora_fim": "10:00:00"},
            {"dia_semana": 1, "hora_inicio": "18:00:00", "hora_fim": "20:00:00"},
        ]
        horarios = _horarios(client, quadra["id"], AMANHA, auth_pessoa).json()["horarios"]
        assert horarios == ["08:00:00", "09:00:00", "18:00:00", "19:00:00"]

    def test_varios_esportes_geram_um_registro_independente_por_esporte(
        self, client, db, auth_admin
    ):
        resposta = client.post(
            "/admin/quadras",
            json=_quadra_payload(esportes=["Futsal", "Vôlei", "Basquete"]),
            headers=auth_admin,
        )
        criadas = resposta.json()
        assert sorted(q["esporte"] for q in criadas) == ["Basquete", "Futsal", "Vôlei"]
        assert len({q["id"] for q in criadas}) == 3
        assert all(len(q["faixas"]) == 2 for q in criadas)

    def test_esporte_invalido_ou_faixas_sobrepostas_retornam_422_sem_gravar(
        self, client, db, auth_admin
    ):
        sobrepostas = [
            {"dia_semana": 1, "hora_inicio": "08:00", "hora_fim": "10:00"},
            {"dia_semana": 1, "hora_inicio": "09:30", "hora_fim": "11:30"},
        ]
        for dados in (
            _quadra_payload(esportes=["Futsal", "Xadrez"]),
            _quadra_payload(faixas=sobrepostas),
        ):
            resposta = client.post("/admin/quadras", json=dados, headers=auth_admin)
            assert resposta.status_code == 422, dados
        assert db.query(Quadra).count() == 0


class TestEdicaoDeQuadras:
    def test_edicao_substitui_dados_e_grade_de_horarios(self, client, db, auth_admin, auth_pessoa):
        quadra = criar_quadra(db)  # todos os dias 08-12
        nova_grade = [{"dia_semana": 1, "hora_inicio": "18:00", "hora_fim": "19:00"}]
        resposta = client.put(
            f"/admin/quadras/{quadra.id}",
            json=_edicao_payload(nome="Nome Novo", esporte="Vôlei", faixas=nova_grade),
            headers=auth_admin,
        )
        assert resposta.status_code == 200
        corpo = resposta.json()
        assert (corpo["nome"], corpo["esporte"]) == ("Nome Novo", "Vôlei")
        assert corpo["faixas"] == [
            {"dia_semana": 1, "hora_inicio": "18:00:00", "hora_fim": "19:00:00"}
        ]
        # A grade antiga deixa de gerar horários.
        assert _horarios(client, quadra.id, AMANHA, auth_pessoa).json()["horarios"] == ["18:00:00"]

        resposta = client.put("/admin/quadras/9999", json=_edicao_payload(), headers=auth_admin)
        assert resposta.status_code == 404

    def test_edicao_nao_afeta_agendamentos_existentes(self, client, db, auth_admin):
        quadra = criar_quadra(db)
        agendamento = criar_agendamento(
            db, usuario=criar_pessoa(db), quadra=quadra, inicio=em(AMANHA, 9)
        )
        client.put(
            f"/admin/quadras/{quadra.id}",
            json=_edicao_payload(
                faixas=[{"dia_semana": 1, "hora_inicio": "18:00", "hora_fim": "19:00"}]
            ),
            headers=auth_admin,
        )
        db.refresh(agendamento)
        assert agendamento.status is StatusAgendamento.CONFIRMADO
        assert agendamento.data_hora_inicio == em(AMANHA, 9)


class TestDesativacaoDeQuadras:
    def test_quadra_desativada_sai_da_consulta_e_nao_aceita_novos_agendamentos(
        self, client, db, auth_admin, auth_pessoa
    ):
        quadra = criar_quadra(db)
        resposta = client.post(f"/admin/quadras/{quadra.id}/desativar", headers=auth_admin)
        assert resposta.status_code == 200
        assert resposta.json() == {"mensagem": "Quadra desativada com sucesso."}

        assert client.get("/quadras", headers=auth_pessoa).json() == []
        novo = {"id_quadra": quadra.id, "data": AMANHA.isoformat(), "hora_inicio": "09:00"}
        assert client.post("/agendamentos", json=novo, headers=auth_pessoa).status_code == 404
        # Na listagem administrativa ela continua visível, com a grade.
        [listada] = client.get("/admin/quadras", headers=auth_admin).json()
        assert (listada["status"], len(listada["faixas"])) == ("Desativada", 7)

    def test_desativacao_preserva_agendamentos_existentes(self, client, db, auth_admin):
        quadra = criar_quadra(db)
        agendamento = criar_agendamento(
            db, usuario=criar_pessoa(db), quadra=quadra, inicio=em(AMANHA, 9)
        )
        client.post(f"/admin/quadras/{quadra.id}/desativar", headers=auth_admin)
        db.refresh(agendamento)
        assert agendamento.status is StatusAgendamento.CONFIRMADO
        assert client.post("/admin/quadras/9999/desativar", headers=auth_admin).status_code == 404


def test_listagem_administrativa_filtra_nome_e_bairro_parcialmente(client, db, auth_admin):
    criar_quadra(db, nome="Ginásio Norte", bairro="Setor Norte")
    criar_quadra(db, nome="Quadra Sul", bairro="Setor Sul")
    por_nome = client.get("/admin/quadras", params={"nome": "gin"}, headers=auth_admin)
    por_bairro = client.get("/admin/quadras", params={"bairro": "sul"}, headers=auth_admin)
    assert _nomes(por_nome) == ["Ginásio Norte"]
    assert _nomes(por_bairro) == ["Quadra Sul"]
