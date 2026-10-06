"""Integração — matriz de controle de acesso de TODAS as rotas da API.

Perfis: anônimo, Usuário Pessoa (cidadão), Operador e Gestor.
Níveis de acesso:
  * AUTENTICADO — qualquer usuário logado;
  * PESSOA      — somente cidadãos;
  * ADMIN       — Gestor e Operador;
  * GESTOR      — somente Gestor.

Para cada rota x perfil verifica-se: quem não tem permissão recebe 401 (sem login)
ou 403 (logado sem permissão); quem tem permissão NÃO recebe 401/403 (pode receber
404/422 porque os testes usam IDs e corpos fictícios — o que importa aqui é o acesso).
"""

import pytest

from app.main import app
from app.models import PerfilAdministrativo
from tests.fabricas import autenticar, criar_admin, criar_pessoa

pytestmark = pytest.mark.integracao

AUTENTICADO, PESSOA, ADMIN, GESTOR = "autenticado", "pessoa", "admin", "gestor"
PERMITIDOS = {
    AUTENTICADO: {"pessoa", "operador", "gestor"},
    PESSOA: {"pessoa"},
    ADMIN: {"operador", "gestor"},
    GESTOR: {"gestor"},
}

ROTAS_PROTEGIDAS = [
    ("POST", "/auth/logout", AUTENTICADO),
    ("GET", "/quadras", AUTENTICADO),
    ("GET", "/quadras/filtros", AUTENTICADO),
    ("GET", "/quadras/9999/horarios-disponiveis", AUTENTICADO),
    ("GET", "/usuarios/me", PESSOA),
    ("PATCH", "/usuarios/me", PESSOA),
    ("POST", "/usuarios/me/desativar", PESSOA),
    ("POST", "/agendamentos", PESSOA),
    ("GET", "/agendamentos/me", PESSOA),
    ("GET", "/agendamentos/me/proximo", PESSOA),
    ("POST", "/agendamentos/9999/cancelar", PESSOA),
    ("POST", "/agendamentos/9999/renovar", PESSOA),
    ("GET", "/admin/usuarios-pessoa", ADMIN),
    ("POST", "/admin/usuarios-pessoa", ADMIN),
    ("POST", "/admin/usuarios-pessoa/9999/desativar", ADMIN),
    ("POST", "/admin/usuarios-pessoa/9999/reativar", ADMIN),
    ("GET", "/admin/quadras", ADMIN),
    ("POST", "/admin/quadras", ADMIN),
    ("PUT", "/admin/quadras/9999", ADMIN),
    ("POST", "/admin/quadras/9999/desativar", ADMIN),
    ("GET", "/admin/agendamentos", ADMIN),
    ("POST", "/admin/agendamentos", ADMIN),
    ("POST", "/admin/agendamentos/9999/remarcar", ADMIN),
    ("POST", "/admin/agendamentos/9999/cancelar", ADMIN),
    ("GET", "/admin/administradores", GESTOR),
    ("POST", "/admin/administradores", GESTOR),
    ("PUT", "/admin/administradores/9999", GESTOR),
    ("POST", "/admin/administradores/9999/desativar", GESTOR),
    ("GET", "/admin/configuracoes", GESTOR),
    ("PUT", "/admin/configuracoes", GESTOR),
]

ROTAS_PUBLICAS = [
    ("GET", "/health"),
    ("POST", "/usuarios"),
    ("POST", "/auth/login"),
    ("POST", "/auth/refresh"),
    ("POST", "/auth/recuperar-senha"),
    ("POST", "/auth/redefinir-senha/validar"),
    ("POST", "/auth/redefinir-senha"),
]


@pytest.fixture
def cabecalhos(client, db):
    # Usuários novos a cada rota: algumas ações (ex.: desativar a própria conta)
    # encerram a sessão e não podem contaminar a verificação das rotas seguintes.
    def novos():
        return {
            "anonimo": {},
            "pessoa": autenticar(client, criar_pessoa(db).email),
            "operador": autenticar(
                client, criar_admin(db, perfil=PerfilAdministrativo.OPERADOR).email
            ),
            "gestor": autenticar(client, criar_admin(db, perfil=PerfilAdministrativo.GESTOR).email),
        }

    return novos


def _verificar_nivel(client, cabecalhos, nivel):
    rotas = [(m, r) for m, r, n in ROTAS_PROTEGIDAS if n == nivel]
    assert rotas
    for metodo, rota in rotas:
        for perfil, cabecalho in cabecalhos().items():
            resposta = client.request(metodo, rota, headers=cabecalho, json={})
            if perfil == "anonimo":
                esperado = "401"
                aceito = resposta.status_code == 401
            elif perfil in PERMITIDOS[nivel]:
                esperado = "permitido (≠ 401/403)"
                aceito = resposta.status_code not in (401, 403)
            else:
                esperado = "403"
                aceito = resposta.status_code == 403
            assert aceito, (
                f"{metodo} {rota} como {perfil}: esperado {esperado}, obtido {resposta.status_code}"
            )


def test_rotas_de_qualquer_usuario_autenticado(client, cabecalhos):
    _verificar_nivel(client, cabecalhos, AUTENTICADO)


def test_rotas_exclusivas_do_cidadao(client, cabecalhos):
    _verificar_nivel(client, cabecalhos, PESSOA)


def test_rotas_de_gestor_e_operador(client, cabecalhos):
    _verificar_nivel(client, cabecalhos, ADMIN)


def test_rotas_exclusivas_do_gestor(client, cabecalhos):
    _verificar_nivel(client, cabecalhos, GESTOR)


def test_todas_as_rotas_da_api_estao_na_matriz():
    """Garante que nenhuma rota nova fique fora da verificação de acesso."""

    def normalizar(caminho: str) -> str:
        return "/".join(
            "{id}" if parte.isdigit() or parte.startswith("{") else parte
            for parte in caminho.split("/")
        )

    # A especificação OpenAPI lista todas as rotas publicadas, inclusive as dos routers.
    na_api = {
        (metodo.upper(), normalizar(caminho))
        for caminho, operacoes in app.openapi()["paths"].items()
        for metodo in operacoes
    }
    na_matriz = {(m, normalizar(r)) for m, r, _ in ROTAS_PROTEGIDAS} | {
        (m, normalizar(r)) for m, r in ROTAS_PUBLICAS
    }
    assert na_api == na_matriz
