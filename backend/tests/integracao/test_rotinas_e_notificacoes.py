"""Integração — rotinas automáticas (scheduler) e envio de e-mails.

Regras verificadas:
  * agendamentos confirmados cujo horário terminou passam a "Concluído";
  * lembrete enviado uma única vez, dentro da antecedência configurada;
  * todo envio de e-mail fica registrado no histórico de notificações;
  * falha no servidor de e-mail NÃO desfaz a operação de negócio.
"""

from datetime import timedelta
from unittest.mock import MagicMock

import pytest
from sqlalchemy import select

from app.core import scheduler
from app.core.config import settings
from app.models import Agendamento, Configuracao, Notificacao, StatusAgendamento
from app.services.agendamento_service import AgendamentoService
from app.services.email_service import EmailService
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
)

pytestmark = pytest.mark.integracao


@pytest.fixture
def quadra(db):
    return criar_quadra(db)


class TestConclusaoAutomatica:
    def test_somente_confirmados_que_ja_terminaram_viram_concluidos(self, db, quadra, relogio):
        outra = criar_quadra(db, nome="Outra")
        terminou = criar_agendamento(
            db, usuario=criar_pessoa(db), quadra=quadra, inicio=em(HOJE, 9)
        )
        em_andamento = criar_agendamento(
            db, usuario=criar_pessoa(db), quadra=outra, inicio=em(HOJE, 9, 30)
        )
        cancelado = criar_agendamento(
            db,
            usuario=criar_pessoa(db),
            quadra=quadra,
            inicio=em(ONTEM, 9),
            status=StatusAgendamento.CANCELADO,
        )
        relogio.move_to(em(HOJE, 10))  # exatamente no término das 09:00

        assert AgendamentoService(db).concluir_vencidos() == 1
        for agendamento in (terminou, em_andamento, cancelado):
            db.refresh(agendamento)
        assert terminou.status is StatusAgendamento.CONCLUIDO
        assert em_andamento.status is StatusAgendamento.CONFIRMADO
        assert cancelado.status is StatusAgendamento.CANCELADO

    def test_apos_conclusao_o_cidadao_pode_renovar(self, client, db, quadra, relogio):
        pessoa = criar_pessoa(db)
        agendamento = criar_agendamento(db, usuario=pessoa, quadra=quadra, inicio=em(HOJE, 9))
        relogio.move_to(em(HOJE, 10, 5))
        AgendamentoService(db).concluir_vencidos()

        resposta = client.post(
            f"/agendamentos/{agendamento.id}/renovar",
            json={"data": AMANHA.isoformat(), "hora_inicio": "09:00"},
            headers=autenticar(client, pessoa.email),
        )
        assert resposta.status_code == 201


class TestLembretes:
    def test_envia_um_unico_lembrete_para_agendamento_nas_proximas_24h(
        self, db, quadra, caixa_de_email
    ):
        pessoa = criar_pessoa(db)
        agendamento = criar_agendamento(db, usuario=pessoa, quadra=quadra, inicio=em(HOJE, 11))
        servico = AgendamentoService(db)
        assert servico.enviar_lembretes() == 1
        [email] = eventos(caixa_de_email, "lembrete_agendamento", para=pessoa.email)
        assert "11:00 às 12:00" in email["corpo"]
        db.refresh(agendamento)
        assert agendamento.lembrete_enviado_em is not None

        assert servico.enviar_lembretes() == 0  # não reenvia
        assert len(eventos(caixa_de_email, "lembrete_agendamento")) == 1

    def test_so_lembra_confirmados_que_ainda_vao_comecar_dentro_da_janela(
        self, db, quadra, relogio
    ):
        # Agora = 04/03 08:00. Janela: até 05/03 08:00 (inclusive).
        outra = criar_quadra(db, nome="Outra")

        def agendar(quadra_, inicio, status=StatusAgendamento.CONFIRMADO):
            return criar_agendamento(
                db, usuario=criar_pessoa(db), quadra=quadra_, inicio=inicio, status=status
            )

        dentro = agendar(quadra, em(AMANHA, 8))
        fora_da_janela = agendar(outra, em(AMANHA, 9))
        cancelado = agendar(quadra, em(HOJE, 11), StatusAgendamento.CANCELADO)
        concluido = agendar(outra, em(HOJE, 11), StatusAgendamento.CONCLUIDO)
        ja_comecou = agendar(outra, em(HOJE, 8))  # começa exatamente agora
        assert AgendamentoService(db).enviar_lembretes() == 1
        for agendamento in (dentro, fora_da_janela, cancelado, concluido, ja_comecou):
            db.refresh(agendamento)
        assert dentro.lembrete_enviado_em is not None
        assert fora_da_janela.lembrete_enviado_em is None
        assert cancelado.lembrete_enviado_em is None
        assert concluido.lembrete_enviado_em is None
        assert ja_comecou.lembrete_enviado_em is None

    def test_respeita_a_antecedencia_configurada(self, db, quadra):
        db.add(Configuracao(chave="lembrete_antecedencia_horas", valor="2"))
        db.commit()
        proximo = criar_agendamento(
            db, usuario=criar_pessoa(db), quadra=quadra, inicio=em(HOJE, 10)
        )
        distante = criar_agendamento(
            db, usuario=criar_pessoa(db), quadra=quadra, inicio=em(HOJE, 11)
        )
        assert AgendamentoService(db).enviar_lembretes() == 1
        db.refresh(proximo)
        db.refresh(distante)
        assert proximo.lembrete_enviado_em is not None
        assert distante.lembrete_enviado_em is None


class TestScheduler:
    def test_job_de_conclusao_usa_sessao_propria_e_registra_falhas(
        self, db, quadra, relogio, monkeypatch, caplog
    ):
        agendamento = criar_agendamento(
            db, usuario=criar_pessoa(db), quadra=quadra, inicio=em(HOJE, 9)
        )
        relogio.move_to(em(HOJE, 11))
        scheduler.concluir_agendamentos_vencidos()
        db.refresh(agendamento)
        assert agendamento.status is StatusAgendamento.CONCLUIDO

        def falhar(self):
            raise RuntimeError("banco indisponível")

        monkeypatch.setattr(AgendamentoService, "concluir_vencidos", falhar)
        scheduler.concluir_agendamentos_vencidos()  # não deve propagar a exceção
        assert "Falha no job de conclusão de agendamentos" in caplog.text

    def test_job_de_lembretes_usa_sessao_propria_e_registra_falhas(
        self, db, quadra, monkeypatch, caplog, caixa_de_email
    ):
        pessoa = criar_pessoa(db)
        criar_agendamento(db, usuario=pessoa, quadra=quadra, inicio=em(HOJE, 11))
        scheduler.enviar_lembretes_de_agendamento()
        assert len(eventos(caixa_de_email, "lembrete_agendamento", para=pessoa.email)) == 1

        def falhar(self):
            raise RuntimeError("SMTP e banco indisponíveis")

        monkeypatch.setattr(AgendamentoService, "enviar_lembretes", falhar)
        scheduler.enviar_lembretes_de_agendamento()
        assert "Falha no job de lembretes de agendamento" in caplog.text

    def test_api_inicia_e_encerra_o_scheduler_quando_habilitado(self, monkeypatch):
        from fastapi.testclient import TestClient

        import app.main as main

        agendador = MagicMock()
        monkeypatch.setattr(main.settings, "SCHEDULER_ENABLED", True)
        monkeypatch.setattr(main, "criar_scheduler", lambda: agendador)
        with TestClient(main.app):
            agendador.start.assert_called_once()
        agendador.shutdown.assert_called_once_with(wait=False)

    def test_registra_os_dois_jobs_periodicos(self):
        agendador = scheduler.criar_scheduler()
        jobs = {job.id: job for job in agendador.get_jobs()}
        assert set(jobs) == {"concluir_agendamentos_vencidos", "enviar_lembretes_de_agendamento"}
        for job in jobs.values():
            assert job.trigger.interval == timedelta(
                minutes=settings.CONCLUIR_AGENDAMENTOS_INTERVALO_MINUTOS
            )


class TestEnvioDeEmail:
    def test_envio_por_smtp_com_tls_e_autenticacao(self, db, monkeypatch):
        smtp = MagicMock()
        monkeypatch.setattr(settings, "MAIL_MODE", "smtp")
        monkeypatch.setattr("app.services.email_service.smtplib.SMTP", smtp)

        EmailService(db).enviar("ana@teste.com", "Assunto", "Corpo", evento="teste")

        smtp.assert_called_once_with(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
        conexao = smtp.return_value.__enter__.return_value
        mensagem = conexao.send_message.call_args.args[0]
        assert (mensagem["To"], mensagem["Subject"], mensagem["From"]) == (
            "ana@teste.com",
            "Assunto",
            settings.SMTP_FROM,
        )
        conexao.starttls.assert_not_called()
        registro = db.scalar(select(Notificacao))
        assert (registro.evento, registro.sucesso) == ("teste", True)

        monkeypatch.setattr(settings, "SMTP_TLS", True)
        monkeypatch.setattr(settings, "SMTP_USER", "usuario")
        monkeypatch.setattr(settings, "SMTP_PASSWORD", "senha")
        EmailService(db).enviar("ana@teste.com", "A", "C")
        conexao.starttls.assert_called_once()
        conexao.login.assert_called_once_with("usuario", "senha")

    def test_falha_de_smtp_e_registrada_e_nao_desfaz_o_agendamento(
        self, client, db, quadra, monkeypatch
    ):
        monkeypatch.setattr(settings, "MAIL_MODE", "smtp")
        monkeypatch.setattr(
            "app.services.email_service.smtplib.SMTP",
            MagicMock(side_effect=OSError("SMTP fora do ar")),
        )
        pessoa = criar_pessoa(db)
        resposta = client.post(
            "/agendamentos",
            json={"id_quadra": quadra.id, "data": AMANHA.isoformat(), "hora_inicio": "09:00"},
            headers=autenticar(client, pessoa.email),
        )
        assert resposta.status_code == 201
        assert db.scalar(select(Agendamento)).status is StatusAgendamento.CONFIRMADO
        registro = db.scalar(
            select(Notificacao).where(Notificacao.evento == "confirmacao_agendamento")
        )
        assert registro.sucesso is False

    def test_email_sem_sessao_de_banco_registra_em_sessao_propria(self, db):
        EmailService().enviar("x@teste.com", "Assunto", "Corpo", evento="avulso")
        assert db.scalar(select(Notificacao)).evento == "avulso"
