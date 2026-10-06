from datetime import UTC, datetime

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models import FalhaLogin, IpBloqueado


class SegurancaRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def registrar_falha_login(self, ip: str, email: str) -> None:
        self.db.add(FalhaLogin(ip=ip, email=email, criado_em=datetime.now(UTC)))
        self.db.flush()

    def contar_contas_com_falha(self, ip: str, desde: datetime) -> int:
        """Quantos e-mails diferentes tiveram login recusado a partir deste IP."""
        return self.db.scalar(
            select(func.count(func.distinct(FalhaLogin.email))).where(
                FalhaLogin.ip == ip, FalhaLogin.criado_em >= desde
            )
        )

    def ip_esta_bloqueado(self, ip: str) -> bool:
        return self.db.get(IpBloqueado, ip) is not None

    def bloquear_ip(self, ip: str, motivo: str) -> None:
        if not self.ip_esta_bloqueado(ip):
            self.db.add(IpBloqueado(ip=ip, motivo=motivo, bloqueado_em=datetime.now(UTC)))
            self.db.flush()

    def listar_ips_bloqueados(self) -> list[IpBloqueado]:
        return list(self.db.scalars(select(IpBloqueado).order_by(IpBloqueado.bloqueado_em.desc())))

    def desbloquear_ip(self, ip: str) -> bool:
        """Remove o bloqueio e o histórico de falhas do IP (senão ele seria rebloqueado
        na primeira falha seguinte). Retorna False se o IP não estava bloqueado."""
        if not self.ip_esta_bloqueado(ip):
            return False
        self.db.execute(delete(IpBloqueado).where(IpBloqueado.ip == ip))
        self.db.execute(delete(FalhaLogin).where(FalhaLogin.ip == ip))
        self.db.flush()
        return True
