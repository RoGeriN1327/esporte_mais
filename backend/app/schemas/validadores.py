"""Validações de campos reutilizadas pelos schemas (nome, CPF, e-mail e senha).

Cada função recebe o valor bruto e devolve o valor normalizado, ou lança
ValueError com a mensagem exibida ao usuário (o Pydantic devolve HTTP 422).
Os schemas usam os tipos prontos do final do arquivo, ex.: ``cpf: CPF``.
"""

from typing import Annotated

from pydantic import AfterValidator, EmailStr

from app.utils.cpf import cpf_valido, normalizar_cpf

NOME_TAMANHO_MAXIMO = 100
SENHA_TAMANHO_MINIMO = 8
# O bcrypt processa no máximo 72 bytes; acima disso a biblioteca recusa a senha.
SENHA_TAMANHO_MAXIMO_BYTES = 72


def validar_nome(valor: str) -> str:
    valor = valor.strip()
    if not valor:
        raise ValueError("O nome é obrigatório.")
    if len(valor) > NOME_TAMANHO_MAXIMO:
        raise ValueError("O nome deve ter no máximo 100 caracteres.")
    return valor


def validar_cpf(valor: str) -> str:
    """Aceita CPF com ou sem máscara e devolve só os 11 dígitos."""
    cpf = normalizar_cpf(valor)
    if not cpf_valido(cpf):
        raise ValueError("CPF inválido. Informe 11 dígitos numéricos válidos.")
    return cpf


def normalizar_email(valor: str) -> str:
    return valor.lower()


def validar_tamanho_senha(valor: str) -> str:
    if len(valor) < SENHA_TAMANHO_MINIMO:
        raise ValueError("A senha deve ter no mínimo 8 caracteres.")
    if len(valor.encode("utf-8")) > SENHA_TAMANHO_MAXIMO_BYTES:
        raise ValueError(
            "A senha deve ter no máximo 72 caracteres "
            "(letras acentuadas e símbolos especiais contam em dobro)."
        )
    return valor


Nome = Annotated[str, AfterValidator(validar_nome)]
CPF = Annotated[str, AfterValidator(validar_cpf)]
Email = Annotated[EmailStr, AfterValidator(normalizar_email)]
Senha = Annotated[str, AfterValidator(validar_tamanho_senha)]
