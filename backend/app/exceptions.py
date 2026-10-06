"""Exceções de negócio lançadas pelos services.

Cada classe define o status HTTP da resposta; a conversão para JSON é feita
em app.main.tratar_erro_de_dominio. A mensagem é exibida ao usuário final.
"""


class ErroDeDominio(Exception):
    status_code: int = 400

    def __init__(self, mensagem: str) -> None:
        self.mensagem = mensagem
        super().__init__(mensagem)


class NaoAutenticado(ErroDeDominio):
    status_code = 401


class CredenciaisInvalidas(ErroDeDominio):
    status_code = 401


class ContaBloqueada(ErroDeDominio):
    status_code = 423


class ContaDesativada(ErroDeDominio):
    status_code = 403


class AcessoNegado(ErroDeDominio):
    status_code = 403


class IpBloqueado(ErroDeDominio):
    status_code = 403


class RecursoNaoEncontrado(ErroDeDominio):
    status_code = 404


class ConflitoDeDados(ErroDeDominio):
    status_code = 409


class RegraDeNegocioViolada(ErroDeDominio):
    status_code = 400
