import re

def normalizar_cpf(valor: str) -> str:
    return re.sub(r"\D", "", valor or "")

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
