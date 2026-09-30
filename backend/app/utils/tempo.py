from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from app.core.config import settings


def fuso() -> ZoneInfo:
    return ZoneInfo(settings.TIMEZONE)


def agora_local() -> datetime:
    return datetime.now(fuso())


def hoje_local() -> date:
    return agora_local().date()


def combinar(dia: date, hora: time) -> datetime:
    return datetime.combine(dia, hora, tzinfo=fuso())
