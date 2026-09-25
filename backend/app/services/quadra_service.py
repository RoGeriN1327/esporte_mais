from datetime import date, time, timedelta

from sqlalchemy.orm import Session

from app.exceptions import RecursoNaoEncontrado, RegraDeNegocioViolada
from app.models import Quadra, StatusQuadra
from app.repositories import AgendamentoRepository, QuadraRepository
from app.schemas.quadra import QuadraAdminCreate, QuadraAdminUpdate
from app.utils import tempo

DURACAO_SLOT = timedelta(hours=1)

MSG_QUADRA_NAO_ENCONTRADA = "Quadra não encontrada."
MSG_DATA_PASSADA = "A data deve ser a partir de hoje."

class QuadraService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.quadras = QuadraRepository(db)
        self.agendamentos = AgendamentoRepository(db)

    def listar_disponiveis(
        self,
        *,
        esporte: str | None = None,
        nome: str | None = None,
        bairro: str | None = None,
    ) -> list[Quadra]:
        return self.quadras.listar_ativas(esporte=esporte, nome=nome, bairro=bairro)

    def opcoes_de_filtro(self) -> dict[str, list[str]]:
        return {
            "esportes": self.quadras.esportes_distintos(),
            "bairros": self.quadras.bairros_distintos(),
        }

    def obter_quadra_ativa(self, quadra_id: int) -> Quadra:
        quadra = self.quadras.obter_por_id(quadra_id)
        if quadra is None or quadra.status is not StatusQuadra.ATIVA:

            raise RecursoNaoEncontrado(MSG_QUADRA_NAO_ENCONTRADA)
        return quadra

    def slots_da_grade(self, quadra_id: int, dia: date) -> list[time]:
        slots: list[time] = []
        for faixa in self.quadras.faixas_do_dia(quadra_id, dia.weekday()):
            inicio = tempo.combinar(dia, faixa.hora_inicio)
            limite = tempo.combinar(dia, faixa.hora_fim)
            while inicio + DURACAO_SLOT <= limite:
                slots.append(inicio.time())
                inicio += DURACAO_SLOT
        return sorted(set(slots))

    def horarios_disponiveis(self, quadra_id: int, dia: date) -> list[time]:
        self.obter_quadra_ativa(quadra_id)
        if dia < tempo.hoje_local():
            raise RegraDeNegocioViolada(MSG_DATA_PASSADA)

        inicio_dia = tempo.combinar(dia, time.min)
        fim_dia = inicio_dia + timedelta(days=1)
        ocupados = {
            ocupado.astimezone(tempo.fuso()).time()
            for ocupado in self.agendamentos.inicios_confirmados_da_quadra(
                quadra_id, inicio_dia, fim_dia
            )
        }
        agora = tempo.agora_local()
        return [
            slot
            for slot in self.slots_da_grade(quadra_id, dia)
            if slot not in ocupados and tempo.combinar(dia, slot) > agora
        ]

    def _obter_para_gestao(self, quadra_id: int) -> Quadra:
        quadra = self.quadras.obter_por_id(quadra_id)
        if quadra is None:
            raise RecursoNaoEncontrado(MSG_QUADRA_NAO_ENCONTRADA)
        return quadra

    def listar_para_gestao(
        self,
        *,
        esporte: str | None = None,
        nome: str | None = None,
        bairro: str | None = None,
    ) -> list[Quadra]:
        return self.quadras.listar_todas(esporte=esporte, nome=nome, bairro=bairro)

    def cadastrar(self, dados: QuadraAdminCreate) -> list[Quadra]:
        faixas = [(f.dia_semana, f.hora_inicio, f.hora_fim) for f in dados.faixas]
        criadas = [
            self.quadras.criar(
                nome=dados.nome,
                descricao=dados.descricao,
                endereco=dados.endereco,
                bairro=dados.bairro,
                esporte=esporte,
                faixas=faixas,
            )
            for esporte in dados.esportes
        ]
        self.db.commit()
        return criadas

    def editar(self, quadra_id: int, dados: QuadraAdminUpdate) -> Quadra:
        quadra = self._obter_para_gestao(quadra_id)
        self.quadras.atualizar(
            quadra,
            nome=dados.nome,
            descricao=dados.descricao,
            endereco=dados.endereco,
            bairro=dados.bairro,
            esporte=dados.esporte,
        )
        self.quadras.substituir_faixas(
            quadra, [(f.dia_semana, f.hora_inicio, f.hora_fim) for f in dados.faixas]
        )
        self.db.commit()
        return quadra

    def desativar(self, quadra_id: int) -> Quadra:
        quadra = self._obter_para_gestao(quadra_id)
        self.quadras.atualizar(quadra, status=StatusQuadra.DESATIVADA)
        self.db.commit()
        return quadra
