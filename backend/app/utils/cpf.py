import re


def normalizar_cpf(valor: str) -> str:
    return re.sub(r"\D", "", valor or "")


def ocultar_cpf(valor: str) -> str:
    """Máscara para exibição na área administrativa: ***.982.247-** (só os 6 dígitos do meio).

    Valor que não tem 11 dígitos (ex.: já mascarado) volta sem alteração.
    """
    cpf = normalizar_cpf(valor)
    if len(cpf) != 11:
        return valor
    return f"***.{cpf[3:6]}.{cpf[6:9]}-**"


def cpf_valido(cpf: str) -> bool:
    if len(cpf) != 11 or not cpf.isdigit():
        return False

    if cpf == cpf[0] * 11:
        return False
    for posicao in (9, 10):
        soma = sum(int(cpf[j]) * ((posicao + 1) - j) for j in range(posicao))
        digito = (soma * 10) % 11
        if digito == 10:
            digito = 0
        if digito != int(cpf[posicao]):
            return False
    return True
