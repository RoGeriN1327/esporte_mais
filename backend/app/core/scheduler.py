"""Jobs periódicos da API (APScheduler), iniciados no lifespan de app.main.

- concluir_agendamentos_vencidos: marca como "Concluído" os agendamentos cujo
  horário já terminou.
- enviar_lembretes_de_agendamento: envia o e-mail de lembrete com a
  antecedência configurada pelo Gestor.

Cada execução abre a própria sessão de banco e nunca propaga exceções: uma
falha é apenas registrada no log e o job tenta de novo no próximo intervalo.
"""

import logging
from collections.abc import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.agendamento_service import AgendamentoService
from app.utils import tempo

logger = logging.getLogger("esporte_mais.scheduler")


def _executar_job(tarefa: Callable[[Session], int], sucesso: str, falha: str) -> None:
    db = SessionLocal()
    try:
        total = tarefa(db)
        if total:
            logger.info(sucesso, total)
    except Exception:
        logger.exception(falha)
    finally:
        db.close()


def concluir_agendamentos_vencidos() -> None:
    _executar_job(
        lambda db: AgendamentoService(db).concluir_vencidos(),
        sucesso="Agendamentos concluídos pelo job: %s",
        falha="Falha no job de conclusão de agendamentos",
    )


def enviar_lembretes_de_agendamento() -> None:
    _executar_job(
        lambda db: AgendamentoService(db).enviar_lembretes(),
        sucesso="Lembretes de agendamento enviados pelo job: %s",
        falha="Falha no job de lembretes de agendamento",
    )


def criar_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone=settings.TIMEZONE)
    for job in (concluir_agendamentos_vencidos, enviar_lembretes_de_agendamento):
        scheduler.add_job(
            job,
            "interval",
            minutes=settings.CONCLUIR_AGENDAMENTOS_INTERVALO_MINUTOS,
            next_run_time=tempo.agora_local(),  # roda uma vez logo na subida da API
            id=job.__name__,
        )
    return scheduler
