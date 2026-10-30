from datetime import datetime

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.models import Acesso


class AcessoRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def registrar(self, **campos) -> None:
        self.db.add(Acesso(**campos))
        self.db.flush()

    @staticmethod
    def _filtros(
        desde: datetime | None, ate: datetime | None, evento: str | None, so_logados: bool
    ) -> list:
        filtros = []
        if desde is not None:
            filtros.append(Acesso.criado_em >= desde)
        if ate is not None:
            filtros.append(Acesso.criado_em < ate)
        if evento:
            filtros.append(Acesso.evento == evento)
        if so_logados:
            filtros.append(Acesso.usuario_id.is_not(None))
        return filtros

    def listar(self, *, limite: int, **filtros) -> list[Acesso]:
        return list(
            self.db.scalars(
                select(Acesso)
                .where(*self._filtros(**filtros))
                .order_by(Acesso.criado_em.desc(), Acesso.id.desc())
                .limit(limite)
            )
        )

    def resumir(self, **filtros) -> dict:
        def contar_evento(nome: str):
            return func.count().filter(Acesso.evento == nome)

        linha = self.db.execute(
            select(
                func.count(),
                contar_evento("pagina"),
                contar_evento("login"),
                contar_evento("login_recusado"),
                func.count(distinct(Acesso.id_visitante)),
                func.count(distinct(Acesso.ip)),
            ).where(*self._filtros(**filtros))
        ).one()
        return dict(
            zip(
                ("total", "telas", "logins", "logins_recusados", "aparelhos", "ips"),
                linha,
                strict=True,
            )
        )

    def resumir_por_usuario(self, **filtros) -> list[dict]:
        linhas = self.db.execute(
            select(
                Acesso.email,
                Acesso.tipo_usuario,
                func.count().filter(Acesso.evento == "login"),
                func.count().filter(Acesso.evento == "pagina"),
                func.max(Acesso.criado_em),
            )
            .where(Acesso.usuario_id.is_not(None), *self._filtros(**filtros))
            .group_by(Acesso.email, Acesso.tipo_usuario)
            .order_by(func.max(Acesso.criado_em).desc())
        ).all()
        return [
            {"email": e, "tipo": t, "logins": lg, "telas": tl, "ultimo_acesso": u}
            for e, t, lg, tl, u in linhas
        ]
