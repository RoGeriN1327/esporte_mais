from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session, joinedload

from app.models import Agendamento, StatusAgendamento

class AgendamentoRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def criar(
        self,
        *,
        id_usuario: int,
        id_quadra: int,
        data_hora_inicio: datetime,
        data_hora_fim: datetime,
        id_admin_responsavel: int | None = None,
    ) -> Agendamento:
        agendamento = Agendamento(
            id_usuario=id_usuario,
            id_quadra=id_quadra,
            id_admin_responsavel=id_admin_responsavel,
            data_hora_inicio=data_hora_inicio,
            data_hora_fim=data_hora_fim,
            status=StatusAgendamento.CONFIRMADO,
        )
        self.db.add(agendamento)
        self.db.flush()
        self.db.refresh(agendamento)
        return agendamento

    def obter_por_id(self, agendamento_id: int) -> Agendamento | None:
        return self.db.scalar(
            select(Agendamento)
            .options(joinedload(Agendamento.quadra))
            .where(Agendamento.id == agendamento_id)
        )

    def listar_do_usuario(
        self,
        usuario_id: int,
        *,
        inicio_dia: datetime | None = None,
        fim_dia: datetime | None = None,
        nome_quadra: str | None = None,
        esporte: str | None = None,
        status: StatusAgendamento | None = None,
    ) -> list[Agendamento]:
        from app.models import Quadra

        consulta = (
            select(Agendamento)
            .join(Agendamento.quadra)
            .options(joinedload(Agendamento.quadra))
            .where(Agendamento.id_usuario == usuario_id)
        )
        if inicio_dia is not None and fim_dia is not None:
            consulta = consulta.where(
                Agendamento.data_hora_inicio >= inicio_dia,
                Agendamento.data_hora_inicio < fim_dia,
            )
        if nome_quadra:
            consulta = consulta.where(Quadra.nome.ilike(f"%{nome_quadra}%"))
        if esporte:
            consulta = consulta.where(Quadra.esporte == esporte)
        if status is not None:
            consulta = consulta.where(Agendamento.status == status)
        return list(self.db.scalars(consulta.order_by(Agendamento.data_hora_inicio.desc())))

    def proximo_confirmado(self, usuario_id: int, apos: datetime) -> Agendamento | None:
        return self.db.scalar(
            select(Agendamento)
            .options(joinedload(Agendamento.quadra))
            .where(
                Agendamento.id_usuario == usuario_id,
                Agendamento.status == StatusAgendamento.CONFIRMADO,
                Agendamento.data_hora_fim > apos,
            )
            .order_by(Agendamento.data_hora_inicio)
            .limit(1)
        )

    def existe_confirmado_do_usuario(self, usuario_id: int) -> bool:
        return (
            self.db.scalar(
                select(Agendamento.id).where(
                    Agendamento.id_usuario == usuario_id,
                    Agendamento.status == StatusAgendamento.CONFIRMADO,
                )
            )
            is not None
        )

    def listar_confirmados_do_usuario(self, usuario_id: int) -> list[Agendamento]:
        return list(
            self.db.scalars(
                select(Agendamento)
                .options(joinedload(Agendamento.quadra))
                .where(
                    Agendamento.id_usuario == usuario_id,
                    Agendamento.status == StatusAgendamento.CONFIRMADO,
                )
            )
        )

    def inicios_confirmados_da_quadra(
        self, quadra_id: int, inicio_dia: datetime, fim_dia: datetime
    ) -> list[datetime]:
        return list(
            self.db.scalars(
                select(Agendamento.data_hora_inicio).where(
                    Agendamento.id_quadra == quadra_id,
                    Agendamento.status == StatusAgendamento.CONFIRMADO,
                    Agendamento.data_hora_inicio >= inicio_dia,
                    Agendamento.data_hora_inicio < fim_dia,
                )
            )
        )

    def listar_consolidado(
        self,
        *,
        inicio_dia: datetime | None = None,
        fim_dia: datetime | None = None,
        nome_quadra: str | None = None,
        esporte: str | None = None,
        status: StatusAgendamento | None = None,
        cpf_usuario: str | None = None,
        nome_usuario: str | None = None,
    ) -> list[Agendamento]:
        from app.models import Quadra, UsuarioPessoa

        consulta = (
            select(Agendamento)
            .join(Agendamento.quadra)
            .join(Agendamento.usuario)
            .options(joinedload(Agendamento.quadra), joinedload(Agendamento.usuario))
        )
        if inicio_dia is not None and fim_dia is not None:
            consulta = consulta.where(
                Agendamento.data_hora_inicio >= inicio_dia,
                Agendamento.data_hora_inicio < fim_dia,
            )
        if nome_quadra:
            consulta = consulta.where(Quadra.nome.ilike(f"%{nome_quadra}%"))
        if esporte:
            consulta = consulta.where(Quadra.esporte == esporte)
        if status is not None:
            consulta = consulta.where(Agendamento.status == status)
        if cpf_usuario:
            consulta = consulta.where(UsuarioPessoa.cpf == cpf_usuario)
        if nome_usuario:
            consulta = consulta.where(UsuarioPessoa.nome.ilike(f"%{nome_usuario}%"))
        return list(self.db.scalars(consulta.order_by(Agendamento.data_hora_inicio.desc())))

    def atualizar(self, agendamento: Agendamento, **campos) -> Agendamento:
        for campo, valor in campos.items():
            setattr(agendamento, campo, valor)
        self.db.flush()
        return agendamento

    def listar_para_lembrete(self, agora: datetime, limite: datetime) -> list[Agendamento]:
        return list(
            self.db.scalars(
                select(Agendamento)
                .options(joinedload(Agendamento.quadra), joinedload(Agendamento.usuario))
                .where(
                    Agendamento.status == StatusAgendamento.CONFIRMADO,
                    Agendamento.lembrete_enviado_em.is_(None),
                    Agendamento.data_hora_inicio > agora,
                    Agendamento.data_hora_inicio <= limite,
                )
            )
        )

    def concluir_vencidos(self, agora: datetime) -> int:
        resultado = self.db.execute(
            update(Agendamento)
            .where(
                Agendamento.status == StatusAgendamento.CONFIRMADO,
                Agendamento.data_hora_fim <= agora,
            )
            .values(status=StatusAgendamento.CONCLUIDO)
        )
        return resultado.rowcount
