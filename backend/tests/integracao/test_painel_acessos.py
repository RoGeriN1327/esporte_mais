"""Integração — painel secreto de consulta dos acessos.

Regras verificadas:
  * a página só abre no caminho secreto; fora dele, ou com o painel desligado, é 404;
  * os dados só saem com a chave certa; chave errada também é 404, sem pistas;
  * chaves erradas demais bloqueiam o IP (que também perde o login);
  * a página não vai para cache nem para buscadores e não aparece na documentação;
  * resumo, logins por usuário e filtros (período, evento, só logados).
"""

from datetime import UTC, datetime

import pytest

from app.core.config import settings
from app.main import app
from app.models import Acesso
from tests.fabricas import criar_pessoa

pytestmark = pytest.mark.integracao

CAMINHO = "caminho-secreto-de-teste-123"
CHAVE = "chave-secreta-de-teste-456"
IP = "200.1.1.1"


@pytest.fixture(autouse=True)
def painel_ligado(monkeypatch):
    monkeypatch.setattr(settings, "PAINEL_ACESSOS_CAMINHO", CAMINHO)
    monkeypatch.setattr(settings, "PAINEL_ACESSOS_CHAVE", CHAVE)


def _consultar(client, chave=CHAVE, caminho=CAMINHO, ip=IP, **filtros):
    return client.post(
        f"/interno/{caminho}/dados",
        json={"chave": chave, **filtros},
        headers={"CF-Connecting-IP": ip},
    )


def _acesso(db, quando, evento="pagina", **campos):
    padrao = {
        "ip": "1.2.3.4",
        "navegador": "Chrome 120",
        "sistema": "Android 13",
        "tipo_dispositivo": "Celular",
        "user_agent": "Mozilla/5.0",
        "caminho": "/" if evento == "pagina" else None,
    }
    db.add(Acesso(criado_em=quando, evento=evento, **{**padrao, **campos}))
    db.commit()


class TestPagina:
    def test_abre_no_caminho_secreto_sem_cache_e_com_csp(self, client):
        resposta = client.get(f"/interno/{CAMINHO}")
        assert resposta.status_code == 200
        assert "Acesso restrito" in resposta.text
        assert resposta.headers["cache-control"] == "no-store"
        assert "noindex" in resposta.headers["x-robots-tag"]
        csp = resposta.headers["content-security-policy"]
        nonce = csp.split("'nonce-")[1].split("'")[0]
        assert f'nonce="{nonce}"' in resposta.text and "{{NONCE}}" not in resposta.text
        assert "default-src 'none'" in csp

    def test_nonce_muda_a_cada_abertura(self, client):
        a = client.get(f"/interno/{CAMINHO}").headers["content-security-policy"]
        b = client.get(f"/interno/{CAMINHO}").headers["content-security-policy"]
        assert a != b

    @pytest.mark.parametrize("caminho", ["errado", CAMINHO[:-1], CAMINHO + "x", CAMINHO.upper()])
    def test_caminho_errado_e_404_igual_a_rota_inexistente(self, client, caminho):
        resposta = client.get(f"/interno/{caminho}")
        inexistente = client.get("/rota-que-nao-existe")
        assert resposta.status_code == inexistente.status_code == 404
        assert resposta.json() == inexistente.json()

    @pytest.mark.parametrize(
        ("caminho", "chave"), [("", ""), (CAMINHO, ""), ("", CHAVE), ("curto", CHAVE)]
    )
    def test_painel_desligado_sem_configuracao_ou_curta(self, client, monkeypatch, caminho, chave):
        monkeypatch.setattr(settings, "PAINEL_ACESSOS_CAMINHO", caminho)
        monkeypatch.setattr(settings, "PAINEL_ACESSOS_CHAVE", chave)
        assert client.get(f"/interno/{caminho or 'x'}").status_code == 404
        assert _consultar(client, caminho=caminho or "x").status_code == 404

    def test_fora_da_documentacao(self):
        assert not any(p.startswith("/interno") for p in app.openapi()["paths"])


class TestChave:
    def test_chave_certa_devolve_os_dados_sem_cache(self, client, db):
        _acesso(db, datetime(2030, 3, 4, 12, tzinfo=UTC))
        resposta = _consultar(client)
        assert resposta.status_code == 200
        assert resposta.headers["cache-control"] == "no-store"
        assert resposta.json()["resumo"]["total"] == 1

    def test_chave_errada_e_404(self, client, db):
        _acesso(db, datetime(2030, 3, 4, 12, tzinfo=UTC))
        resposta = _consultar(client, chave="errada")
        assert resposta.status_code == 404
        assert resposta.json() == {"detail": "Not Found"}

    def test_chave_certa_em_caminho_errado_e_404(self, client):
        assert _consultar(client, caminho="errado").status_code == 404

    def test_chaves_erradas_demais_bloqueiam_o_ip(self, client):
        assert [_consultar(client, chave=f"e{i}").status_code for i in range(5)] == [404] * 5
        # Bloqueado: nem a chave certa, nem a página, nem o login.
        assert _consultar(client).status_code == 404
        assert (
            client.get(f"/interno/{CAMINHO}", headers={"CF-Connecting-IP": IP}).status_code == 404
        )
        login = client.post(
            "/auth/login",
            json={"email": "x@teste.com", "senha": "x"},
            headers={"CF-Connecting-IP": IP},
        )
        assert login.status_code == 403
        # Outro IP segue normal.
        assert _consultar(client, ip="200.2.2.2").status_code == 200

    def test_quatro_erros_ainda_nao_bloqueiam(self, client):
        for i in range(4):
            _consultar(client, chave=f"e{i}")
        assert _consultar(client).status_code == 200


class TestConsulta:
    def test_resumo_usuarios_e_lista_mais_recente_primeiro(self, client, db):
        pessoa = criar_pessoa(db)
        logado = {"usuario_id": pessoa.id, "email": pessoa.email, "tipo_usuario": "Pessoa"}
        _acesso(db, datetime(2030, 3, 1, 12, tzinfo=UTC), id_visitante="v1")
        _acesso(db, datetime(2030, 3, 2, 12, tzinfo=UTC), "login", **logado)
        _acesso(db, datetime(2030, 3, 2, 12, 1, tzinfo=UTC), id_visitante="v1", **logado)
        _acesso(
            db,
            datetime(2030, 3, 3, 12, tzinfo=UTC),
            "login_recusado",
            ip="9.9.9.9",
            email="x@y.com",
        )

        dados = _consultar(client).json()
        assert dados["resumo"] == {
            "total": 4,
            "telas": 2,
            "logins": 1,
            "logins_recusados": 1,
            "aparelhos": 1,
            "ips": 2,
        }
        [usuario] = dados["usuarios"]
        assert (usuario["email"], usuario["logins"], usuario["telas"]) == (pessoa.email, 1, 1)
        assert [a["evento"] for a in dados["acessos"]] == [
            "login_recusado",
            "pagina",
            "login",
            "pagina",
        ]
        assert dados["acessos"][0]["email"] == "x@y.com"

    def test_filtros(self, client, db):
        # 02:30 UTC do dia 5 ainda é dia 4 em Brasília.
        _acesso(db, datetime(2030, 3, 4, 12, tzinfo=UTC))
        _acesso(db, datetime(2030, 3, 5, 2, 30, tzinfo=UTC), "login", usuario_id=1, email="a@b.c")
        _acesso(db, datetime(2030, 3, 6, 12, tzinfo=UTC))

        def total(**filtros):
            return _consultar(client, **filtros).json()["resumo"]["total"]

        assert total() == 3
        assert total(desde="2030-03-04", ate="2030-03-04") == 2
        assert total(desde="2030-03-05") == 1
        assert total(evento="login") == 1
        assert total(so_logados=True) == 1
        assert _consultar(client, evento="outro").status_code == 422
