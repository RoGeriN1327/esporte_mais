"""Integração — agendamentos do cidadão (realizar, consultar, cancelar, renovar).

Regras verificadas:
  * cada cidadão pode ter no máximo UM agendamento confirmado por vez;
  * o horário precisa pertencer à grade da quadra, estar livre e no futuro;
  * cada agendamento dura 1 hora;
  * cancelamento respeita a antecedência mínima configurada (padrão 2 horas);
  * só agendamentos concluídos podem ser renovados; o original passa a "Renovado";
  * cada operação envia o e-mail correspondente;
  * a unicidade é garantida pelo banco mesmo com requisições simultâneas.
"""

from datetime import time, timedelta

import pytest
from sqlalchemy import func, select

from app.models import Agendamento, Configuracao, StatusAgendamento
from app.services.agendamento_service import (
    MSG_HORARIO_OCUPADO,
    MSG_JA_POSSUI_ATIVO,
)
from tests.fabricas import (
    AMANHA,
    HOJE,
    ONTEM,
    autenticar,
    criar_agendamento,
    criar_pessoa,
    criar_quadra,
    em,
    eventos,
    executar_em_paralelo,
    instante,
    usuario_atual,
)

pytestmark = pytest.mark.integracao

DEPOIS_DE_AMANHA = AMANHA + timedelta(days=1)


@pytest.fixture
def pessoa(db):
    return criar_pessoa(db, nome="Lucas Martins")


@pytest.fixture
def auth(client, pessoa):
    return autenticar(client, pessoa.email)


@pytest.fixture
def quadra(db):
    return criar_quadra(db)


def _agendar(client, cabecalho, quadra_id, dia=AMANHA, hora="09:00"):
    return client.post(
        "/agendamentos",
        json={"id_quadra": quadra_id, "data": dia.isoformat(), "hora_inicio": hora},
        headers=cabecalho,
    )


def _confirmados(db) -> int:
    return db.scalar(
        select(func.count())
        .select_from(Agendamento)
        .where(Agendamento.status == StatusAgendamento.CONFIRMADO)
    )


def _horarios_livres(client, quadra_id, cabecalho, dia=AMANHA) -> list[str]:
    return client.get(
        f"/quadras/{quadra_id}/horarios-disponiveis",
        params={"data": dia.isoformat()},
        headers=cabecalho,
    ).json()["horarios"]


def test_agendamento_confirmado_de_1_hora_com_email_e_horario_ocupado(
    client, db, pessoa, auth, quadra, caixa_de_email
):
    resposta = _agendar(client, auth, quadra.id)

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert (corpo["status"], corpo["id_quadra"], corpo["nome_quadra"]) == (
        "Confirmado",
        quadra.id,
        quadra.nome,
    )
    assert instante(corpo["data_hora_inicio"]) == em(AMANHA, 9)
    assert instante(corpo["data_hora_fim"]) == em(AMANHA, 10)
    # Feito pelo próprio cidadão: nenhum administrador responsável.
    assert db.scalar(select(Agendamento)).id_admin_responsavel is None

    [email] = eventos(caixa_de_email, "confirmacao_agendamento", para=pessoa.email)
    for trecho in ("Lucas Martins", quadra.nome, "05/03/2030", "09:00 às 10:00"):
        assert trecho in email["corpo"], trecho

    outra = autenticar(client, criar_pessoa(db).email)
    assert "09:00:00" not in _horarios_livres(client, quadra.id, outra)


class TestUmAgendamentoAtivoPorCidadao:
    def test_segundo_agendamento_e_recusado_em_qualquer_quadra_ou_dia(
        self, client, db, auth, quadra
    ):
        outra = criar_quadra(db, nome="Outra", esporte="Vôlei")
        _agendar(client, auth, quadra.id, hora="09:00")
        for quadra_id, dia in ((quadra.id, AMANHA), (outra.id, DEPOIS_DE_AMANHA)):
            resposta = _agendar(client, auth, quadra_id, dia=dia, hora="10:00")
            assert resposta.status_code == 409
            assert resposta.json() == {"detail": MSG_JA_POSSUI_ATIVO}
        assert _confirmados(db) == 1

        # O limite é por cidadão: outra pessoa agenda normalmente.
        outro = autenticar(client, criar_pessoa(db).email)
        assert _agendar(client, outro, quadra.id, hora="10:00").status_code == 201

    def test_agendamentos_nao_confirmados_nao_contam_no_limite(self, client, db, auth, quadra):
        # Após cancelar, o cidadão pode agendar de novo.
        primeiro = _agendar(client, auth, quadra.id, hora="08:00").json()
        client.post(f"/agendamentos/{primeiro['id']}/cancelar", headers=auth)
        assert _agendar(client, auth, quadra.id, hora="08:00").status_code == 201

        # Histórico concluído, cancelado ou renovado não impede um novo agendamento.
        for hora, status in (
            (9, StatusAgendamento.CONCLUIDO),
            (10, StatusAgendamento.CANCELADO),
            (11, StatusAgendamento.RENOVADO),
        ):
            pessoa = criar_pessoa(db)
            criar_agendamento(db, usuario=pessoa, quadra=quadra, inicio=em(ONTEM, 9), status=status)
            cabecalho = autenticar(client, pessoa.email)
            resposta = _agendar(client, cabecalho, quadra.id, hora=f"{hora:02d}:00")
            assert resposta.status_code == 201, status


class TestValidacaoDoHorario:
    def test_horario_ocupado_por_outra_pessoa_retorna_409(self, client, db, auth, quadra):
        criar_agendamento(db, usuario=criar_pessoa(db), quadra=quadra, inicio=em(AMANHA, 9))
        resposta = _agendar(client, auth, quadra.id, hora="09:00")
        assert resposta.status_code == 409
        assert resposta.json() == {"detail": MSG_HORARIO_OCUPADO}

    def test_horario_fora_da_grade_da_quadra_retorna_400(self, client, db, auth, quadra):
        so_segunda = criar_quadra(db, nome="Só segunda", faixas=[(0, time(8), time(12))])
        tentativas = [(quadra.id, h) for h in ("07:00", "12:00", "13:00", "09:30", "09:00:01")]
        tentativas.append((so_segunda.id, "09:00"))  # terça: dia sem funcionamento
        for quadra_id, hora in tentativas:
            resposta = _agendar(client, auth, quadra_id, hora=hora)
            assert resposta.status_code == 400, hora
            assert resposta.json() == {
                "detail": "Horário indisponível para esta quadra na data selecionada."
            }
        assert _confirmados(db) == 0

    def test_data_ou_horario_que_ja_passou_e_recusado_sem_culpar_outro_usuario(
        self, client, db, pessoa, quadra, relogio
    ):
        auth = autenticar(client, pessoa.email)
        resposta = _agendar(client, auth, quadra.id, dia=ONTEM)
        assert resposta.status_code == 400
        assert resposta.json() == {"detail": "A data deve ser a partir de hoje."}

        # Às 10:30, o horário das 09:00 de hoje já passou. O sistema deve recusar
        # sem afirmar que o horário "acabou de ser ocupado" (ninguém o ocupou).
        relogio.move_to(em(HOJE, 10, 30))
        auth = autenticar(client, pessoa.email)  # login após o avanço do relógio
        resposta = _agendar(client, auth, quadra.id, dia=HOJE, hora="09:00")
        assert resposta.status_code == 400
        assert "ocupado" not in resposta.json()["detail"]
        assert _confirmados(db) == 0

        # Um horário de hoje que ainda não começou é aceito.
        assert _agendar(client, auth, quadra.id, dia=HOJE, hora="11:00").status_code == 201

    def test_quadra_desativada_ou_inexistente_retorna_404(self, client, db, auth):
        from app.models import StatusQuadra

        desativada = criar_quadra(db, status=StatusQuadra.DESATIVADA)
        for quadra_id in (desativada.id, 9999):
            assert _agendar(client, auth, quadra_id).status_code == 404, quadra_id


class TestConcorrencia:
    def test_duas_pessoas_reservando_o_mesmo_horario_ao_mesmo_tempo(self, db, monkeypatch, quadra):
        ana, bruno = criar_pessoa(db), criar_pessoa(db)
        resultados = executar_em_paralelo(
            monkeypatch,
            [
                lambda s: s.criar(usuario_atual(ana), quadra.id, AMANHA, time(9)),
                lambda s: s.criar(usuario_atual(bruno), quadra.id, AMANHA, time(9)),
            ],
        )
        assert resultados == sorted(["ok", MSG_HORARIO_OCUPADO])
        assert _confirmados(db) == 1

    def test_mesma_pessoa_reservando_duas_quadras_ao_mesmo_tempo(self, db, monkeypatch, quadra):
        pessoa = criar_pessoa(db)
        outra = criar_quadra(db, nome="Outra")
        resultados = executar_em_paralelo(
            monkeypatch,
            [
                lambda s: s.criar(usuario_atual(pessoa), quadra.id, AMANHA, time(9)),
                lambda s: s.criar(usuario_atual(pessoa), outra.id, AMANHA, time(9)),
            ],
        )
        assert resultados == sorted(["ok", MSG_JA_POSSUI_ATIVO])
        assert _confirmados(db) == 1


class TestMeusAgendamentos:
    def test_lista_somente_os_do_proprio_cidadao_do_mais_recente_ao_mais_antigo(
        self, client, db, pessoa, auth, quadra
    ):
        concluido = StatusAgendamento.CONCLUIDO
        antigo = criar_agendamento(
            db,
            usuario=pessoa,
            quadra=quadra,
            inicio=em(ONTEM - timedelta(days=7), 9),
            status=concluido,
        )
        recente = criar_agendamento(
            db, usuario=pessoa, quadra=quadra, inicio=em(ONTEM, 9), status=concluido
        )
        futuro = criar_agendamento(db, usuario=pessoa, quadra=quadra, inicio=em(AMANHA, 9))
        criar_agendamento(db, usuario=criar_pessoa(db), quadra=quadra, inicio=em(AMANHA, 10))

        ids = [a["id"] for a in client.get("/agendamentos/me", headers=auth).json()]
        assert ids == [futuro.id, recente.id, antigo.id]

    def test_filtros_por_status_data_esporte_e_nome_da_quadra(self, client, db, pessoa, auth):
        futsal = criar_quadra(db, nome="Ginásio Norte", esporte="Futsal")
        volei = criar_quadra(
            db, nome="Arena Sul", esporte="Vôlei", faixas=[(1, time(22), time(23, 59))]
        )
        a1 = criar_agendamento(
            db,
            usuario=pessoa,
            quadra=futsal,
            inicio=em(ONTEM, 9),
            status=StatusAgendamento.CONCLUIDO,
        )
        # 22:30 de 05/03 em Brasília já é 06/03 em UTC; deve contar como dia 05/03.
        a2 = criar_agendamento(db, usuario=pessoa, quadra=volei, inicio=em(AMANHA, 22, 30))

        def ids(**params):
            resposta = client.get("/agendamentos/me", params=params, headers=auth)
            return [a["id"] for a in resposta.json()]

        assert ids(status="Concluído") == [a1.id]
        assert ids(status="Confirmado") == [a2.id]
        assert ids(data=AMANHA.isoformat()) == [a2.id]
        assert ids(esporte="Futsal") == [a1.id]
        assert ids(nome_quadra="arena") == [a2.id]
        resposta = client.get("/agendamentos/me", params={"status": "Pendente"}, headers=auth)
        assert resposta.status_code == 422

    def test_proximo_agendamento_e_o_confirmado_ainda_nao_encerrado(
        self, client, db, pessoa, auth, quadra, relogio
    ):
        criar_agendamento(
            db,
            usuario=pessoa,
            quadra=quadra,
            inicio=em(ONTEM, 9),
            status=StatusAgendamento.CONCLUIDO,
        )
        resposta = client.get("/agendamentos/me/proximo", headers=auth)
        assert (resposta.status_code, resposta.json()) == (200, None)

        agendamento = criar_agendamento(db, usuario=pessoa, quadra=quadra, inicio=em(HOJE, 9))
        assert client.get("/agendamentos/me/proximo", headers=auth).json()["id"] == agendamento.id
        # Em andamento (09:30), ainda é o próximo.
        relogio.move_to(em(HOJE, 9, 30))
        auth = autenticar(client, pessoa.email)
        assert client.get("/agendamentos/me/proximo", headers=auth).json()["id"] == agendamento.id


def _cancelar(client, cabecalho, agendamento_id):
    return client.post(f"/agendamentos/{agendamento_id}/cancelar", headers=cabecalho)


class TestCancelamentoPeloCidadao:
    def test_cancelamento_libera_o_horario_e_envia_email(
        self, client, db, pessoa, auth, quadra, caixa_de_email
    ):
        agendamento = criar_agendamento(db, usuario=pessoa, quadra=quadra, inicio=em(AMANHA, 9))
        resposta = _cancelar(client, auth, agendamento.id)

        assert (resposta.status_code, resposta.json()["status"]) == (200, "Cancelado")
        db.refresh(agendamento)
        assert agendamento.status is StatusAgendamento.CANCELADO
        assert len(eventos(caixa_de_email, "cancelamento_agendamento", para=pessoa.email)) == 1
        outra = autenticar(client, criar_pessoa(db).email)
        assert _agendar(client, outra, quadra.id, hora="09:00").status_code == 201

    def test_prazo_padrao_permite_cancelar_ate_exatamente_2_horas_antes(
        self, client, db, quadra, relogio
    ):
        no_limite, apos_limite = criar_pessoa(db), criar_pessoa(db)
        a1 = criar_agendamento(db, usuario=no_limite, quadra=quadra, inicio=em(AMANHA, 10))
        a2 = criar_agendamento(db, usuario=apos_limite, quadra=quadra, inicio=em(AMANHA, 11))

        relogio.move_to(em(AMANHA, 8))  # exatamente 2h antes das 10:00
        assert _cancelar(client, autenticar(client, no_limite.email), a1.id).status_code == 200

        relogio.move_to(em(AMANHA, 9) + timedelta(seconds=1))  # 1s após o limite das 11:00
        resposta = _cancelar(client, autenticar(client, apos_limite.email), a2.id)
        assert resposta.status_code == 400
        assert resposta.json() == {"detail": "O prazo de cancelamento foi encerrado."}
        db.refresh(a2)
        assert a2.status is StatusAgendamento.CONFIRMADO

    def test_prazo_configurado_pelo_gestor_e_respeitado(self, client, db, quadra, relogio):
        def configurar(horas):
            configuracao = db.get(Configuracao, "cancelamento_antecedencia_minima_horas")
            if configuracao is None:
                db.add(Configuracao(chave="cancelamento_antecedencia_minima_horas", valor=horas))
            else:
                configuracao.valor = horas
            db.commit()

        pessoa_24h, pessoa_zero = criar_pessoa(db), criar_pessoa(db)
        a1 = criar_agendamento(db, usuario=pessoa_24h, quadra=quadra, inicio=em(AMANHA, 10))
        a2 = criar_agendamento(db, usuario=pessoa_zero, quadra=quadra, inicio=em(AMANHA, 11))

        configurar("24")
        relogio.move_to(em(HOJE, 10) + timedelta(seconds=1))  # 23h59min59s antes
        assert _cancelar(client, autenticar(client, pessoa_24h.email), a1.id).status_code == 400

        configurar("0")  # sem antecedência: pode cancelar até o início
        relogio.move_to(em(AMANHA, 10, 59))
        assert _cancelar(client, autenticar(client, pessoa_zero.email), a2.id).status_code == 200

    def test_agendamento_de_outra_pessoa_ou_inexistente_retorna_404(self, client, db, auth, quadra):
        alheio = criar_agendamento(
            db, usuario=criar_pessoa(db), quadra=quadra, inicio=em(AMANHA, 9)
        )
        # 404 (e não 403): não revela a existência do agendamento alheio.
        for agendamento_id in (alheio.id, 9999):
            assert _cancelar(client, auth, agendamento_id).status_code == 404
        db.refresh(alheio)
        assert alheio.status is StatusAgendamento.CONFIRMADO

    def test_somente_agendamento_confirmado_pode_ser_cancelado(
        self, client, db, pessoa, auth, quadra
    ):
        for status in (
            StatusAgendamento.CANCELADO,
            StatusAgendamento.CONCLUIDO,
            StatusAgendamento.RENOVADO,
        ):
            agendamento = criar_agendamento(
                db, usuario=pessoa, quadra=quadra, inicio=em(AMANHA, 9), status=status
            )
            resposta = _cancelar(client, auth, agendamento.id)
            assert resposta.status_code == 400, status
            assert resposta.json() == {
                "detail": "Apenas agendamentos confirmados podem ser cancelados."
            }


class TestRenovacao:
    def _renovar(self, client, cabecalho, agendamento_id, dia=AMANHA, hora="10:00", **extra):
        return client.post(
            f"/agendamentos/{agendamento_id}/renovar",
            json={"data": dia.isoformat(), "hora_inicio": hora, **extra},
            headers=cabecalho,
        )

    def _concluido(self, db, pessoa, quadra):
        return criar_agendamento(
            db,
            usuario=pessoa,
            quadra=quadra,
            inicio=em(ONTEM, 9),
            status=StatusAgendamento.CONCLUIDO,
        )

    def test_renovacao_cria_novo_agendamento_na_mesma_quadra_e_marca_o_original(
        self, client, db, pessoa, auth, quadra, caixa_de_email
    ):
        original = self._concluido(db, pessoa, quadra)
        outra = criar_quadra(db, nome="Outra")
        # Mesmo que outra quadra seja enviada, a renovação é sempre na quadra original.
        resposta = self._renovar(client, auth, original.id, id_quadra=outra.id)

        assert resposta.status_code == 201
        novo = resposta.json()
        assert novo["id"] != original.id
        assert (novo["id_quadra"], novo["status"]) == (quadra.id, "Confirmado")
        assert instante(novo["data_hora_inicio"]) == em(AMANHA, 10)
        db.refresh(original)
        assert original.status is StatusAgendamento.RENOVADO
        assert len(eventos(caixa_de_email, "confirmacao_renovacao", para=pessoa.email)) == 1

    def test_somente_agendamento_concluido_pode_ser_renovado(
        self, client, db, pessoa, auth, quadra
    ):
        for status in (
            StatusAgendamento.CONFIRMADO,
            StatusAgendamento.CANCELADO,
            StatusAgendamento.RENOVADO,
        ):
            agendamento = criar_agendamento(
                db, usuario=pessoa, quadra=quadra, inicio=em(AMANHA, 9), status=status
            )
            resposta = self._renovar(client, auth, agendamento.id, dia=DEPOIS_DE_AMANHA)
            assert resposta.status_code == 400, status
            assert resposta.json() == {
                "detail": "Apenas agendamentos concluídos podem ser renovados."
            }

    def test_renovacao_recusada_mantem_o_original_concluido(self, client, db, pessoa, auth, quadra):
        original = self._concluido(db, pessoa, quadra)
        criar_agendamento(db, usuario=criar_pessoa(db), quadra=quadra, inicio=em(AMANHA, 10))
        tentativas = [
            ({"hora": "10:00"}, 409),  # horário ocupado
            ({"hora": "15:00"}, 400),  # fora da grade
            ({"dia": ONTEM}, 400),  # data passada
        ]
        for parametros, status_esperado in tentativas:
            resposta = self._renovar(client, auth, original.id, **parametros)
            assert resposta.status_code == status_esperado, parametros

        # Com outro agendamento ativo, o limite de um por cidadão também vale.
        criar_agendamento(db, usuario=pessoa, quadra=quadra, inicio=em(DEPOIS_DE_AMANHA, 9))
        assert self._renovar(client, auth, original.id, hora="11:00").status_code == 409

        db.refresh(original)
        assert original.status is StatusAgendamento.CONCLUIDO

    def test_quadra_desativada_ou_agendamento_alheio_retorna_404(
        self, client, db, pessoa, auth, quadra
    ):
        from app.models import StatusQuadra

        alheio = self._concluido(db, criar_pessoa(db), quadra)
        assert self._renovar(client, auth, alheio.id).status_code == 404

        original = self._concluido(db, pessoa, quadra)
        quadra.status = StatusQuadra.DESATIVADA
        db.commit()
        assert self._renovar(client, auth, original.id).status_code == 404


class TestRestricoesDoBanco:
    """O banco é a última linha de defesa: os índices únicos parciais precisam existir."""

    def test_banco_recusa_dois_confirmados_na_mesma_quadra_e_horario_ou_do_mesmo_cidadao(
        self, db, pessoa, quadra
    ):
        from sqlalchemy.exc import IntegrityError

        criar_agendamento(db, usuario=pessoa, quadra=quadra, inicio=em(AMANHA, 9))
        casos = [
            ("uq_agendamento_quadra_horario_confirmado", criar_pessoa(db), em(AMANHA, 9)),
            ("uq_agendamento_usuario_confirmado", pessoa, em(AMANHA, 10)),
        ]
        for indice, usuario, inicio in casos:
            with pytest.raises(IntegrityError, match=indice):
                criar_agendamento(db, usuario=usuario, quadra=quadra, inicio=inicio)
            db.rollback()

    def test_banco_permite_historico_de_cancelados_no_mesmo_horario(self, db, quadra):
        for _ in range(3):
            criar_agendamento(
                db,
                usuario=criar_pessoa(db),
                quadra=quadra,
                inicio=em(AMANHA, 9),
                status=StatusAgendamento.CANCELADO,
            )
        criar_agendamento(db, usuario=criar_pessoa(db), quadra=quadra, inicio=em(AMANHA, 9))
        assert _confirmados(db) == 1
