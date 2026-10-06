"""Integração — bloqueio de IP por força bruta no login.

Regras verificadas:
  * IP com login recusado em 5 contas diferentes em 24 horas é bloqueado sem prazo;
  * errar várias vezes a mesma conta não bloqueia o IP (só a conta);
  * o bloqueio vale para as rotas públicas de autenticação, não para quem já está logado;
  * só o Gestor lista e desbloqueia IPs; desbloquear apaga o histórico de falhas.
"""

from datetime import timedelta

import pytest

from app.models import PerfilAdministrativo
from tests.fabricas import SENHA_PADRAO, autenticar, criar_admin, criar_pessoa, login_completo

pytestmark = pytest.mark.integracao

ATACANTE = "6.6.6.6"
OUTRO_IP = "7.7.7.7"
MSG_IP_BLOQUEADO = (
    "Acesso bloqueado por excesso de tentativas de login. "
    "Procure a Secretaria Municipal de Esportes."
)


def _login(client, email, senha="errada", ip=ATACANTE):
    return client.post(
        "/auth/login", json={"email": email, "senha": senha}, headers={"CF-Connecting-IP": ip}
    )


def _errar_em_contas(client, quantidade, ip=ATACANTE):
    return [_login(client, f"alvo{i}@teste.com", ip=ip).status_code for i in range(quantidade)]


class TestBloqueio:
    def test_quinta_conta_diferente_bloqueia_o_ip_sem_prazo(self, client, db, relogio):
        pessoa = criar_pessoa(db)
        assert _errar_em_contas(client, 4) == [401] * 4
        assert _login(client, pessoa.email, SENHA_PADRAO).status_code == 200

        assert _errar_em_contas(client, 5) == [401] * 5
        # Bloqueado: nem a senha correta entra, e o bloqueio não vence com o tempo.
        for _ in range(2):
            resposta = _login(client, pessoa.email, SENHA_PADRAO)
            assert (resposta.status_code, resposta.json()) == (403, {"detail": MSG_IP_BLOQUEADO})
            relogio.shift(timedelta(days=365))

        # Outro IP não é afetado.
        assert _login(client, pessoa.email, SENHA_PADRAO, ip=OUTRO_IP).status_code == 200

    def test_errar_a_mesma_conta_varias_vezes_bloqueia_so_a_conta(self, client, db):
        pessoa = criar_pessoa(db)
        outra = criar_pessoa(db)
        respostas = [_login(client, pessoa.email).status_code for _ in range(10)]
        assert respostas[:3] == [401] * 3
        assert respostas[3:] == [423] * 7
        assert _login(client, outra.email, SENHA_PADRAO).status_code == 200

    def test_falhas_com_mais_de_24_horas_nao_contam(self, client, db, relogio):
        pessoa = criar_pessoa(db)
        _errar_em_contas(client, 4)
        relogio.shift(timedelta(hours=24, seconds=1))
        _login(client, "nova-conta@teste.com")
        assert _login(client, pessoa.email, SENHA_PADRAO).status_code == 200

    def test_ip_bloqueado_nao_cadastra_nem_recupera_senha_mas_sessao_aberta_continua(
        self, client, db
    ):
        pessoa = criar_pessoa(db)
        sessao = login_completo(client, pessoa.email)
        _errar_em_contas(client, 5)
        cabecalho = {"CF-Connecting-IP": ATACANTE}

        rotas = [
            ("/usuarios", {}),
            ("/auth/recuperar-senha", {"email": pessoa.email, "cpf": pessoa.cpf}),
            ("/auth/redefinir-senha/validar", {"token": "x"}),
            ("/auth/redefinir-senha", {"token": "x"}),
        ]
        for rota, corpo in rotas:
            resposta = client.post(rota, json=corpo, headers=cabecalho)
            assert resposta.status_code == 403, rota

        # Quem já estava logado não é derrubado pelo bloqueio do IP.
        autorizado = {**cabecalho, "Authorization": f"Bearer {sessao['access_token']}"}
        assert client.get("/usuarios/me", headers=autorizado).status_code == 200


class TestDesbloqueioPeloGestor:
    def test_gestor_lista_e_desbloqueia_e_o_historico_e_apagado(self, client, db):
        gestor = criar_admin(db, perfil=PerfilAdministrativo.GESTOR)
        auth = autenticar(client, gestor.email)
        _errar_em_contas(client, 5)

        bloqueados = client.get("/admin/ips-bloqueados", headers=auth).json()
        assert [b["ip"] for b in bloqueados] == [ATACANTE]
        assert bloqueados[0]["motivo"] == "Login recusado em 5 contas diferentes em 24h"

        resposta = client.delete(f"/admin/ips-bloqueados/{ATACANTE}", headers=auth)
        assert resposta.status_code == 200
        assert client.get("/admin/ips-bloqueados", headers=auth).json() == []
        # Sem o histórico antigo, uma nova falha não rebloqueia o IP.
        assert _login(client, "mais-uma@teste.com").status_code == 401
        assert _login(client, "mais-uma@teste.com").status_code == 401

    def test_desbloquear_ip_que_nao_esta_bloqueado_retorna_404(self, client, db):
        gestor = criar_admin(db, perfil=PerfilAdministrativo.GESTOR)
        auth = autenticar(client, gestor.email)
        resposta = client.delete("/admin/ips-bloqueados/1.2.3.4", headers=auth)
        assert (resposta.status_code, resposta.json()) == (
            404,
            {"detail": "IP não está bloqueado."},
        )
