import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings
from app.core.database import SessionLocal
from app.utils import tempo

logger = logging.getLogger("esporte_mais.scheduler")

def concluir_agendamentos_vencidos() -> None:
    from app.services.agendamento_service import AgendamentoService

    db = SessionLocal()
    try:
        total = AgendamentoService(db).concluir_vencidos()
        if total:
            logger.info("Agendamentos concluídos pelo job: %s", total)
    except Exception:
        logger.exception("Falha no job de conclusão de agendamentos")
    finally:
        db.close()

def enviar_lembretes_de_agendamento() -> None:

    from app.services.agendamento_service import AgendamentoService

    db = SessionLocal()
    try:
        total = AgendamentoService(db).enviar_lembretes()
        if total:
            logger.info("Lembretes de agendamento enviados pelo job: %s", total)
    except Exception:
        logger.exception("Falha no job de lembretes de agendamento")
    finally:
        db.close()

def criar_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone=settings.TIMEZONE)
    scheduler.add_job(
        concluir_agendamentos_vencidos,
        "interval",
        minutes=settings.CONCLUIR_AGENDAMENTOS_INTERVALO_MINUTOS,
        next_run_time=tempo.agora_local(),
        id="concluir_agendamentos_vencidos",
    )
    scheduler.add_job(
        enviar_lembretes_de_agendamento,
        "interval",
        minutes=settings.CONCLUIR_AGENDAMENTOS_INTERVALO_MINUTOS,
        next_run_time=tempo.agora_local(),
        id="enviar_lembretes_de_agendamento",
    )
    return scheduler
