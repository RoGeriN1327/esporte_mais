"""Integração — configurações do sistema (exclusivas do Gestor).

Regras verificadas:
  * valores padrão: 2h de antecedência para cancelamento e lembrete 24h antes;
  * atualização parcial (só os campos informados mudam);
  * limites: cancelamento de 0 a 168h, lembrete de 1 a 168h.

O bloqueio de Operador e cidadão é verificado em test_matriz_de_permissoes.py.
"""

import pytest

from tests.fabricas import autenticar, criar_admin

pytestmark = pytest.mark.integracao

PADRAO = {"cancelamento_antecedencia_minima_horas": 2, "lembrete_antecedencia_horas": 24}


@pytest.fixture
def auth_gestor(client, db):
    return autenticar(client, criar_admin(db).email)


def _configuracoes(client, cabecalho) -> dict:
    return client.get("/admin/configuracoes", headers=cabecalho).json()


def test_valores_padrao_e_atualizacao_parcial_persistida(client, auth_gestor):
    assert _configuracoes(client, auth_gestor) == PADRAO

    client.put(
        "/admin/configuracoes",
        json={"cancelamento_antecedencia_minima_horas": 12, "lembrete_antecedencia_horas": 6},
        headers=auth_gestor,
    )
    assert _configuracoes(client, auth_gestor) == {
        "cancelamento_antecedencia_minima_horas": 12,
        "lembrete_antecedencia_horas": 6,
    }

    # Só o campo informado muda; o outro é preservado.
    resposta = client.put(
        "/admin/configuracoes",
        json={"cancelamento_antecedencia_minima_horas": 5},
        headers=auth_gestor,
    )
    assert resposta.json() == {
        "cancelamento_antecedencia_minima_horas": 5,
        "lembrete_antecedencia_horas": 6,
    }


def test_valores_fora_dos_limites_sao_recusados_sem_alterar_nada(client, auth_gestor):
    invalidos = [
        {"cancelamento_antecedencia_minima_horas": -1},
        {"cancelamento_antecedencia_minima_horas": 169},
        {"lembrete_antecedencia_horas": 0},
        {"lembrete_antecedencia_horas": 169},
        {"cancelamento_antecedencia_minima_horas": "duas"},
    ]
    for dados in invalidos:
        resposta = client.put("/admin/configuracoes", json=dados, headers=auth_gestor)
        assert resposta.status_code == 422, dados
    assert _configuracoes(client, auth_gestor) == PADRAO
