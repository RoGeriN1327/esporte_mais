"""Unitários — geração de horários e configurações, com repositórios falsos.

O QuadraService transforma a grade de funcionamento (faixas por dia da semana)
em horários de 1 hora e remove os ocupados/passados. Aqui o banco é substituído
por dublês (fakes), isolando apenas a regra de cálculo.
"""

from datetime import date, datetime, time, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.exceptions import RecursoNaoEncontrado, RegraDeNegocioViolada
from app.models import StatusQuadra
from app.services.configuracao_service import ConfiguracaoService
from app.services.quadra_service import QuadraService
from tests.fabricas import AMANHA, FUSO, HOJE, ONTEM

pytestmark = pytest.mark.unitario


class QuadraRepositoryFalso:
    def __init__(
        self, faixas_por_dia: dict[int, list[tuple[time, time]]], status=StatusQuadra.ATIVA
    ):
        self.faixas_por_dia = faixas_por_dia
        self.status = status

    def faixas_do_dia(self, quadra_id: int, dia_semana: int):
        return [
            SimpleNamespace(hora_inicio=i, hora_fim=f)
            for i, f in self.faixas_por_dia.get(dia_semana, [])
        ]

    def obter_por_id(self, quadra_id: int):
        return SimpleNamespace(id=quadra_id, status=self.status) if quadra_id == 1 else None


class AgendamentoRepositoryFalso:
    def __init__(self, ocupados: list[datetime] | None = None):
        self.ocupados = ocupados or []

    def inicios_confirmados_da_quadra(self, quadra_id, inicio_dia, fim_dia):
        return [o for o in self.ocupados if inicio_dia <= o < fim_dia]


def _servico(faixas, ocupados=None, status=StatusQuadra.ATIVA) -> QuadraService:
    servico = QuadraService(MagicMock())
    servico.quadras = QuadraRepositoryFalso(faixas, status)
    servico.agendamentos = AgendamentoRepositoryFalso(ocupados)
    return servico


SEGUNDA = HOJE.weekday()  # 04/03/2030 é segunda-feira (0)
TERCA = AMANHA.weekday()


class TestSlotsDaGrade:
    def test_cada_faixa_gera_horarios_de_1_hora_e_descarta_a_sobra(self):
        casos = [
            ((time(8), time(12)), [time(8), time(9), time(10), time(11)]),
            # 08:30-10:00 comporta só 08:30-09:30; os 30 min restantes não viram horário.
            ((time(8, 30), time(10)), [time(8, 30)]),
            # O último horário pode terminar exatamente no fim da faixa.
            ((time(22), time(23, 59)), [time(22)]),
        ]
        for faixa, esperado in casos:
            servico = _servico({TERCA: [faixa]})
            assert servico.slots_da_grade(1, AMANHA) == esperado, faixa

    def test_varias_faixas_no_mesmo_dia_sao_combinadas_ordenadas_e_sem_repeticao(self):
        servico = _servico({TERCA: [(time(18), time(20)), (time(8), time(10))]})
        assert servico.slots_da_grade(1, AMANHA) == [time(8), time(9), time(18), time(19)]
        servico = _servico({TERCA: [(time(8), time(10)), (time(8), time(10))]})
        assert servico.slots_da_grade(1, AMANHA) == [time(8), time(9)]

    def test_usa_a_grade_do_dia_da_semana_da_data_consultada(self):
        servico = _servico({SEGUNDA: [(time(8), time(9))], TERCA: [(time(14), time(15))]})
        assert servico.slots_da_grade(1, HOJE) == [time(8)]
        assert servico.slots_da_grade(1, AMANHA) == [time(14)]
        assert servico.slots_da_grade(1, AMANHA + timedelta(days=1)) == []  # quarta sem faixa


class TestHorariosDisponiveis:
    def test_remove_somente_os_horarios_ocupados_naquela_data(self):
        from datetime import UTC

        ocupados = [
            datetime.combine(AMANHA, time(9), tzinfo=FUSO),
            datetime.combine(date(2030, 3, 12), time(10), tzinfo=FUSO),  # outra terça
            # 14:00 UTC == 11:00 em Brasília: gravado em UTC, comparado no horário local.
            datetime(2030, 3, 5, 14, 0, tzinfo=UTC),
        ]
        servico = _servico({TERCA: [(time(8), time(12))]}, ocupados)
        assert servico.horarios_disponiveis(1, AMANHA) == [time(8), time(10)]

    def test_hoje_exibe_apenas_horarios_que_ainda_nao_comecaram(self, relogio):
        servico = _servico({SEGUNDA: [(time(8), time(12))]})
        relogio.move_to(datetime.combine(HOJE, time(9, 30), tzinfo=FUSO))
        assert servico.horarios_disponiveis(1, HOJE) == [time(10), time(11)]
        # O horário que começa exatamente agora também não é exibido.
        relogio.move_to(datetime.combine(HOJE, time(10), tzinfo=FUSO))
        assert servico.horarios_disponiveis(1, HOJE) == [time(11)]

    def test_data_passada_e_recusada(self):
        servico = _servico({ONTEM.weekday(): [(time(8), time(12))]})
        with pytest.raises(RegraDeNegocioViolada, match="a partir de hoje"):
            servico.horarios_disponiveis(1, ONTEM)

    def test_quadra_desativada_ou_inexistente_nao_tem_horarios(self):
        desativada = _servico({TERCA: [(time(8), time(12))]}, status=StatusQuadra.DESATIVADA)
        with pytest.raises(RecursoNaoEncontrado):
            desativada.horarios_disponiveis(1, AMANHA)
        with pytest.raises(RecursoNaoEncontrado):
            _servico({TERCA: [(time(8), time(12))]}).horarios_disponiveis(999, AMANHA)


class ConfiguracaoRepositoryFalso:
    def __init__(self, valores: dict[str, str]):
        self.valores = valores

    def obter_valor(self, chave):
        return self.valores.get(chave)

    def definir_valor(self, chave, valor):
        self.valores[chave] = valor


class TestConfiguracaoService:
    def _servico(self, valores) -> ConfiguracaoService:
        servico = ConfiguracaoService(MagicMock())
        servico.configuracoes = ConfiguracaoRepositoryFalso(valores)
        return servico

    def test_padroes_de_2h_para_cancelamento_e_24h_para_lembrete(self):
        servico = self._servico({})
        assert servico.obter_antecedencia_cancelamento_horas() == 2
        assert servico.obter_lembrete_antecedencia_horas() == 24

    def test_valor_configurado_prevalece_sobre_o_padrao_inclusive_zero(self):
        servico = self._servico(
            {"cancelamento_antecedencia_minima_horas": "6", "lembrete_antecedencia_horas": "3"}
        )
        assert servico.obter_antecedencia_cancelamento_horas() == 6
        assert servico.obter_lembrete_antecedencia_horas() == 3
        # Zero é um valor válido e não pode ser confundido com "não configurado".
        servico = self._servico({"cancelamento_antecedencia_minima_horas": "0"})
        assert servico.obter_antecedencia_cancelamento_horas() == 0

    def test_atualizacao_parcial_altera_somente_o_campo_informado(self):
        servico = self._servico({"lembrete_antecedencia_horas": "12"})
        resultado = servico.atualizar(cancelamento_antecedencia_minima_horas=5)
        assert resultado == {
            "cancelamento_antecedencia_minima_horas": 5,
            "lembrete_antecedencia_horas": 12,
        }
