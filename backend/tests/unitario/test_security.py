"""Unitários — segurança (app/core/security.py): senhas, JWT e tokens opacos."""

import re
import string
from datetime import timedelta

import jwt
import pytest

from app.core import security
from app.core.config import settings
from app.models import PerfilAdministrativo, TipoUsuario
from tests.fabricas import AGORA

pytestmark = pytest.mark.unitario


class TestHashDeSenha:
    def test_hash_bcrypt_com_salt_sem_texto_claro(self):
        hash_ = security.gerar_hash_senha("MinhaSenha123")
        assert "MinhaSenha123" not in hash_
        assert hash_.startswith("$2b$")  # formato bcrypt
        # Mesma senha, hashes diferentes: cada hash tem seu próprio salt.
        assert security.gerar_hash_senha("MinhaSenha123") != hash_

    def test_senha_correta_e_aceita_inclusive_com_acentos(self):
        for senha in ("MinhaSenha123", "Çãõ@#çé!123"):
            hash_ = security.gerar_hash_senha(senha)
            assert security.verificar_senha(senha, hash_) is True, senha

    def test_senha_diferente_ou_invalida_e_recusada_sem_erro(self):
        hash_ = security.gerar_hash_senha("MinhaSenha123")
        # Maiúsculas/minúsculas, um caractere a menos/a mais, vazia e acima de 72 bytes
        # (limite do bcrypt: no login deve apenas falhar, nunca derrubar a API).
        for tentativa in ("minhasenha123", "MinhaSenha12", "MinhaSenha1234", "", "S" * 100):
            assert security.verificar_senha(tentativa, hash_) is False, tentativa
        assert security.verificar_senha("qualquer", "isto-nao-e-um-hash-bcrypt") is False


class TestAccessTokenJwt:
    def test_claims_identificam_usuario_tipo_e_perfil(self):
        token, jti, _ = security.criar_access_token(42, TipoUsuario.PESSOA)
        claims = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        assert (claims["sub"], claims["tipo"], claims["perfil"], claims["jti"]) == (
            "42",
            "Pessoa",
            None,
            jti,
        )

        token, _, _ = security.criar_access_token(
            7, TipoUsuario.ADMINISTRATIVO, PerfilAdministrativo.OPERADOR
        )
        claims = security.decodificar_access_token(token)
        assert (claims["tipo"], claims["perfil"]) == ("Administrativo", "Operador")

    def test_expira_exatamente_30_minutos_apos_emissao(self, relogio):
        token, _, expira_em = security.criar_access_token(1, TipoUsuario.PESSOA)
        assert expira_em == AGORA + timedelta(minutes=30)

        relogio.shift(timedelta(minutes=29, seconds=59))
        assert security.decodificar_access_token(token)["sub"] == "1"

        relogio.shift(timedelta(seconds=2))
        with pytest.raises(jwt.ExpiredSignatureError):
            security.decodificar_access_token(token)

    def test_cada_token_tem_jti_unico(self):
        jtis = {security.criar_access_token(1, TipoUsuario.PESSOA)[1] for _ in range(50)}
        assert len(jtis) == 50

    def test_tokens_falsificados_sao_rejeitados(self):
        outro_segredo = jwt.encode(
            {"sub": "1", "tipo": "Administrativo", "perfil": "Gestor", "jti": "x"},
            "segredo-do-atacante-tambem-com-mais-de-32-bytes",
            algorithm="HS256",
        )
        # Ataque clássico: token sem assinatura ("alg": "none").
        sem_assinatura = jwt.encode({"sub": "1", "tipo": "Pessoa"}, key=None, algorithm="none")
        cabecalho, corpo, assinatura = security.criar_access_token(1, TipoUsuario.PESSOA)[0].split(
            "."
        )
        adulterado = f"{cabecalho}.{corpo}x.{assinatura}"

        for nome, falso in (
            ("outro segredo", outro_segredo),
            ("alg none", sem_assinatura),
            ("conteúdo adulterado", adulterado),
        ):
            with pytest.raises(jwt.PyJWTError):
                security.decodificar_access_token(falso)
                pytest.fail(f"token aceito: {nome}")

    def test_segredo_precisa_ter_ao_menos_32_caracteres(self):
        # HS256 exige chave de no mínimo 256 bits (RFC 7518, seção 3.2).
        from pydantic import ValidationError

        from app.core.config import Settings

        with pytest.raises(ValidationError, match="JWT_SECRET"):
            Settings(_env_file=None, JWT_SECRET="x" * 31)
        assert Settings(_env_file=None, JWT_SECRET="x" * 32).JWT_SECRET == "x" * 32


class TestTokensOpacos:
    def test_token_opaco_e_aleatorio_e_url_safe(self):
        tokens = {security.gerar_token_opaco() for _ in range(100)}
        assert len(tokens) == 100
        assert all(re.fullmatch(r"[A-Za-z0-9_-]{64}", t) for t in tokens)

    def test_hash_do_token_e_sha256_deterministico(self):
        assert security.hash_token("abc") == (
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        )
        assert security.hash_token("abc") != security.hash_token("abd")


class TestSenhaTemporaria:
    def test_senha_temporaria_tem_letras_maiusculas_minusculas_e_digitos(self):
        # Geração aleatória: repete 200 vezes para exercitar o laço de rejeição.
        for _ in range(200):
            senha = security.gerar_senha_temporaria()
            assert len(senha) == 12
            assert any(c.islower() for c in senha)
            assert any(c.isupper() for c in senha)
            assert any(c.isdigit() for c in senha)
            assert set(senha) <= set(string.ascii_letters + string.digits)
        assert len(security.gerar_senha_temporaria(20)) == 20

    def test_senhas_consecutivas_sao_diferentes(self):
        assert len({security.gerar_senha_temporaria() for _ in range(100)}) == 100
