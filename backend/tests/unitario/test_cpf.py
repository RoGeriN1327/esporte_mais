"""Unitários — validação de CPF (app/utils/cpf.py).

Regra: CPF é o identificador único do cidadão e do administrador; deve ter
11 dígitos, não pode ser sequência repetida e os dois dígitos verificadores
devem conferir pelo algoritmo módulo 11 da Receita Federal.
"""

import pytest

from app.utils.cpf import cpf_valido, normalizar_cpf

pytestmark = pytest.mark.unitario


def test_normalizacao_remove_mascara_e_caracteres_nao_numericos():
    casos = {
        "529.982.247-25": "52998224725",
        " 529 982 247/25 ": "52998224725",
        "52998224725": "52998224725",
        "": "",
        None: "",
    }
    for entrada, esperado in casos.items():
        assert normalizar_cpf(entrada) == esperado, f"entrada: {entrada!r}"


def test_aceita_cpfs_validos():
    for cpf in ("52998224725", "11144477735", "39053344705"):
        assert cpf_valido(cpf) is True, cpf


def test_rejeita_digitos_verificadores_errados():
    casos = {
        "52998224735": "1º dígito verificador errado",
        "52998224726": "2º dígito verificador errado",
        "52998224752": "dígitos verificadores trocados de posição",
    }
    for cpf, motivo in casos.items():
        assert cpf_valido(cpf) is False, motivo


def test_rejeita_sequencias_repetidas():
    # 111.111.111-11 etc. passam no cálculo do módulo 11, mas não são CPFs válidos.
    for digito in "0123456789":
        assert cpf_valido(digito * 11) is False, digito * 11


def test_resto_10_no_calculo_do_digito_vira_zero():
    # 100.000.001-08: o cálculo do 1º dígito dá 10, que deve ser tratado como 0.
    assert cpf_valido("10000000108") is True
    assert cpf_valido("10000000118") is False
    # 100.000.028-10: o mesmo para o 2º dígito.
    assert cpf_valido("10000002810") is True
    assert cpf_valido("10000002811") is False


def test_rejeita_tamanho_diferente_de_11_ou_caracteres_nao_numericos():
    # A função recebe o CPF já normalizado; máscara ou letras devem ser recusadas.
    for cpf in ("5299822472", "529982247250", "", "1", "529.982.247-25", "5299822472a"):
        assert cpf_valido(cpf) is False, repr(cpf)
