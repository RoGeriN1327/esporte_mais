"""Integração — painel administrativo de agendamentos (Gestor e Operador).

Regras verificadas:
  * painel consolidado com todos os agendamentos e filtros (data, quadra, esporte,
    status, nome e CPF do cidadão);
  * agendamento em nome do cidadão (por CPF) com as mesmas regras do fluxo normal,
    registrando o administrador responsável;
  * remarcação apenas de agendamentos confirmados, na mesma quadra, para horário livre;
  * cancelamento administrativo a qualquer momento (sem o prazo imposto ao cidadão);
  * o cidadão é avisado por e-mail de toda ação administrativa.
"""

from datetime import time, timedelta

import pytest

from app.models import PerfilAdministrativo, StatusAgendamento, StatusUsuario
from app.services.agendamento_service import MSG_HORARIO_OCUPADO, AgendamentoService
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
    eventos,
    executar_em_paralelo,
    instante,
    mascarar_cpf,
    usuario_atual,
)

pytestmark = pytest.mark.integracao

DEPOIS_DE_AMANHA = AMANHA + timedelta(days=1)


@pytest.fixture
def operador(db):
    return criar_admin(db, perfil=PerfilAdministrativo.OPERADOR)


@pytest.fixture
def auth_admin(client, operador):
    return autenticar(client, operador.email)


@pytest.fixture
def quadra(db):
    return criar_quadra(db)


class TestPainelConsolidado:
    def test_gestor_e_operador_veem_agendamentos_de_todos_os_cidadaos(
        self, client, db, auth_admin, quadra
    ):
        ana = criar_pessoa(db, nome="Ana")
        bia = criar_pessoa(db, nome="Bia")
        criar_agendamento(db, usuario=ana, quadra=quadra, inicio=em(AMANHA, 9))
        criar_agendamento(db, usuario=bia, quadra=quadra, inicio=em(AMANHA, 10))

        auth_gestor = autenticar(client, criar_admin(db).email)
        for cabecalho in (auth_admin, auth_gestor):
            resposta = client.get("/admin/agendamentos", headers=cabecalho)
            assert resposta.status_code == 200
            assert {(a["nome_usuario"], a["cpf_usuario"]) for a in resposta.json()} == {
                ("Ana", ana.cpf),
                ("Bia", bia.cpf),
            }

    def test_filtros_por_cidadao_quadra_esporte_status_e_data(self, client, db, auth_admin):
        futsal = criar_quadra(db, nome="Ginásio", esporte="Futsal")
        volei = criar_quadra(db, nome="Arena", esporte="Vôlei")
        joao = criar_pessoa(db, nome="João Batista")
        maria = criar_pessoa(db, nome="Maria Clara")
        a1 = criar_agendamento(db, usuario=joao, quadra=futsal, inicio=em(AMANHA, 9))
        a2 = criar_agendamento(
            db, usuario=maria, quadra=volei, inicio=em(ONTEM, 9), status=StatusAgendamento.CONCLUIDO
        )

        def ids(**params):
            resposta = client.get("/admin/agendamentos", params=params, headers=auth_admin)
            return [a["id"] for a in resposta.json()]

        assert ids(cpf_usuario=mascarar_cpf(joao.cpf)) == [a1.id]  # CPF com máscara
        assert ids(nome_usuario="batista") == [a1.id]
        assert ids(status="Concluído") == [a2.id]
        assert ids(data=AMANHA.isoformat()) == [a1.id]
        assert ids(esporte="Vôlei") == [a2.id]
        assert ids(nome_quadra="gin") == [a1.id]


def _agendar_para(client, cabecalho, cpf, quadra_id, dia=AMANHA, hora="09:00"):
    return client.post(
        "/admin/agendamentos",
        json={
            "cpf_usuario": cpf,
            "id_quadra": quadra_id,
            "data": dia.isoformat(),
            "hora_inicio": hora,
        },
        headers=cabecalho,
    )


class TestAgendamentoEmNomeDoCidadao:
    def test_cria_agendamento_visivel_ao_cidadao_e_registra_o_administrador(
        self, client, db, operador, auth_admin, quadra, caixa_de_email
    ):
        pessoa = criar_pessoa(db)
        resposta = _agendar_para(client, auth_admin, mascarar_cpf(pessoa.cpf), quadra.id)

        assert resposta.status_code == 201
        corpo = resposta.json()
        assert (corpo["status"], corpo["cpf_usuario"], corpo["id_admin_responsavel"]) == (
            "Confirmado",
            pessoa.cpf,
            operador.id,
        )
        assert len(eventos(caixa_de_email, "confirmacao_agendamento", para=pessoa.email)) == 1
        meus = client.get("/agendamentos/me", headers=autenticar(client, pessoa.email)).json()
        assert [a["id"] for a in meus] == [corpo["id"]]

    def test_cidadao_precisa_existir_estar_ativo_e_ter_cpf_valido(
        self, client, db, auth_admin, quadra
    ):
        desativado = criar_pessoa(db, status=StatusUsuario.DESATIVADO)
        casos = [
            ("529.982.247-25", 404, "Usuário não encontrado."),
            (desativado.cpf, 400, "Usuário desativado não pode receber novos agendamentos."),
        ]
        for cpf, status_esperado, mensagem in casos:
            resposta = _agendar_para(client, auth_admin, cpf, quadra.id)
            assert (resposta.status_code, resposta.json()) == (
                status_esperado,
                {"detail": mensagem},
            )
        assert _agendar_para(client, auth_admin, "123.456.789-00", quadra.id).status_code == 422

    def test_aplica_as_mesmas_regras_do_agendamento_feito_pelo_cidadao(
        self, client, db, auth_admin, quadra
    ):
        pessoa = criar_pessoa(db)
        criar_agendamento(db, usuario=criar_pessoa(db), quadra=quadra, inicio=em(AMANHA, 9))
        assert (
            _agendar_para(client, auth_admin, pessoa.cpf, quadra.id, hora="09:00").status_code
            == 409
        )
        assert (
            _agendar_para(client, auth_admin, pessoa.cpf, quadra.id, hora="20:00").status_code
            == 400
        )
        # Limite de um agendamento ativo por cidadão.
        criar_agendamento(db, usuario=pessoa, quadra=quadra, inicio=em(AMANHA, 10))
        assert (
            _agendar_para(client, auth_admin, pessoa.cpf, quadra.id, hora="11:00").status_code
            == 409
        )


class TestRemarcacao:
    def _remarcar(self, client, cabecalho, agendamento_id, dia=DEPOIS_DE_AMANHA, hora="11:00"):
        return client.post(
            f"/admin/agendamentos/{agendamento_id}/remarcar",
            json={"data": dia.isoformat(), "hora_inicio": hora},
            headers=cabecalho,
        )

    def test_remarca_mantendo_1_hora_libera_o_horario_antigo_e_avisa_o_cidadao(
        self, client, db, operador, auth_admin, quadra, caixa_de_email
    ):
        pessoa = criar_pessoa(db)
        agendamento = criar_agendamento(db, usuario=pessoa, quadra=quadra, inicio=em(AMANHA, 9))
        resposta = self._remarcar(client, auth_admin, agendamento.id)

        assert resposta.status_code == 200
        corpo = resposta.json()
        assert instante(corpo["data_hora_inicio"]) == em(DEPOIS_DE_AMANHA, 11)
        assert instante(corpo["data_hora_fim"]) == em(DEPOIS_DE_AMANHA, 12)
        assert (corpo["id_admin_responsavel"], corpo["status"]) == (operador.id, "Confirmado")
        [email] = eventos(caixa_de_email, "remarcacao_agendamento", para=pessoa.email)
        assert "06/03/2030" in email["corpo"]
        assert "11:00 às 12:00" in email["corpo"]

        outra = autenticar(client, criar_pessoa(db).email)
        horarios = client.get(
            f"/quadras/{quadra.id}/horarios-disponiveis",
            params={"data": AMANHA.isoformat()},
            headers=outra,
        ).json()["horarios"]
        assert "09:00:00" in horarios

    def test_remarcacao_invalida_e_recusada_e_mantem_o_horario_original(
        self, client, db, auth_admin, quadra
    ):
        agendamento = criar_agendamento(
            db, usuario=criar_pessoa(db), quadra=quadra, inicio=em(AMANHA, 9)
        )
        criar_agendamento(
            db, usuario=criar_pessoa(db), quadra=quadra, inicio=em(DEPOIS_DE_AMANHA, 11)
        )
        tentativas = [
            ({}, 409),  # horário ocupado
            ({"hora": "19:00"}, 400),  # fora da grade
            ({"dia": ONTEM}, 400),  # data passada
        ]
        for parametros, status_esperado in tentativas:
            resposta = self._remarcar(client, auth_admin, agendamento.id, **parametros)
            assert resposta.status_code == status_esperado, parametros
        db.refresh(agendamento)
        assert agendamento.data_hora_inicio == em(AMANHA, 9)
        assert self._remarcar(client, auth_admin, 9999).status_code == 404

    def test_somente_agendamentos_confirmados_podem_ser_remarcados(
        self, client, db, auth_admin, quadra
    ):
        for status in (
            StatusAgendamento.CANCELADO,
            StatusAgendamento.CONCLUIDO,
            StatusAgendamento.RENOVADO,
        ):
            agendamento = criar_agendamento(
                db, usuario=criar_pessoa(db), quadra=quadra, inicio=em(ONTEM, 9), status=status
            )
            resposta = self._remarcar(client, auth_admin, agendamento.id)
            assert resposta.status_code == 400, status
            assert resposta.json() == {
                "detail": "Apenas agendamentos confirmados podem ser remarcados."
            }

    def test_duas_remarcacoes_simultaneas_para_o_mesmo_horario(
        self, db, monkeypatch, operador, quadra
    ):
        # Dois atendentes remarcam agendamentos diferentes para o mesmo horário ao
        # mesmo tempo: apenas um pode ficar com ele.
        a1 = criar_agendamento(db, usuario=criar_pessoa(db), quadra=quadra, inicio=em(AMANHA, 9))
        a2 = criar_agendamento(db, usuario=criar_pessoa(db), quadra=quadra, inicio=em(AMANHA, 10))
        admin = usuario_atual(operador, PerfilAdministrativo.OPERADOR)
        resultados = executar_em_paralelo(
            monkeypatch,
            [
                lambda s: s.remarcar(admin, a1.id, DEPOIS_DE_AMANHA, time(11)),
                lambda s: s.remarcar(admin, a2.id, DEPOIS_DE_AMANHA, time(11)),
            ],
        )
        assert resultados == sorted(["ok", MSG_HORARIO_OCUPADO])
        db.expire_all()
        inicios = sorted(db.get(type(a1), a.id).data_hora_inicio for a in (a1, a2))
        assert em(DEPOIS_DE_AMANHA, 11) in inicios
        assert len(set(inicios)) == 2

    def test_lembrete_e_reenviado_para_o_novo_horario(
        self, client, db, operador, quadra, relogio, caixa_de_email
    ):
        # Cenário: o lembrete do horário original já foi enviado; a Secretaria remarca
        # para outra data. O cidadão precisa ser lembrado do NOVO horário.
        pessoa = criar_pessoa(db)
        agendamento = criar_agendamento(db, usuario=pessoa, quadra=quadra, inicio=em(AMANHA, 9))
        relogio.move_to(em(HOJE, 9, 30))  # amanhã 09h está a 23h30: dentro da janela de 24h
        AgendamentoService(db).enviar_lembretes()  # lembrete do horário original
        assert len(eventos(caixa_de_email, "lembrete_agendamento", para=pessoa.email)) == 1

        nova_data = HOJE + timedelta(days=7)
        auth_admin = autenticar(client, operador.email)  # login após o avanço do relógio
        remarcacao = self._remarcar(client, auth_admin, agendamento.id, dia=nova_data, hora="10:00")
        assert remarcacao.status_code == 200

        relogio.move_to(em(nova_data, 10) - timedelta(hours=23))  # dentro da janela de 24h
        db.expire_all()
        AgendamentoService(db).enviar_lembretes()
        assert len(eventos(caixa_de_email, "lembrete_agendamento", para=pessoa.email)) == 2


class TestCancelamentoAdministrativo:
    def _cancelar(self, client, cabecalho, agendamento_id):
        return client.post(f"/admin/agendamentos/{agendamento_id}/cancelar", headers=cabecalho)

    def test_cancela_mesmo_fora_do_prazo_do_cidadao(
        self, client, db, operador, quadra, relogio, caixa_de_email
    ):
        pessoa = criar_pessoa(db)
        agendamento = criar_agendamento(db, usuario=pessoa, quadra=quadra, inicio=em(HOJE, 9))
        relogio.move_to(em(HOJE, 8, 50))  # 10 minutos antes: cidadão já não poderia cancelar
        auth_admin = autenticar(client, operador.email)

        resposta = self._cancelar(client, auth_admin, agendamento.id)
        assert resposta.status_code == 200
        assert resposta.json()["status"] == "Cancelado"
        assert resposta.json()["id_admin_responsavel"] == operador.id
        assert len(eventos(caixa_de_email, "cancelamento_agendamento", para=pessoa.email)) == 1

    def test_somente_agendamentos_confirmados_existentes_podem_ser_cancelados(
        self, client, db, auth_admin, quadra
    ):
        for status in (
            StatusAgendamento.CANCELADO,
            StatusAgendamento.CONCLUIDO,
            StatusAgendamento.RENOVADO,
        ):
            agendamento = criar_agendamento(
                db, usuario=criar_pessoa(db), quadra=quadra, inicio=em(ONTEM, 9), status=status
            )
            assert self._cancelar(client, auth_admin, agendamento.id).status_code == 400, status
        assert self._cancelar(client, auth_admin, 9999).status_code == 404
