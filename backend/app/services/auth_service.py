"""Autenticação: login com bloqueio por tentativas, rotação de tokens, logout e
recuperação de senha por link enviado ao e-mail.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core import security
from app.core.config import settings
from app.core.deps import UsuarioAtual
from app.exceptions import (
    ContaBloqueada,
    ContaDesativada,
    CredenciaisInvalidas,
    RegraDeNegocioViolada,
)
from app.models import StatusUsuario, TipoUsuario, UsuarioAdministrativo, UsuarioPessoa
from app.repositories import (
    TokenRepository,
    UsuarioAdministrativoRepository,
    UsuarioPessoaRepository,
)
from app.services.email_service import EmailService

MSG_CREDENCIAIS_INVALIDAS = "E-mail ou senha inválidos."
MSG_CONTA_BLOQUEADA = (
    "Conta temporariamente bloqueada por excesso de tentativas. Tente novamente mais tarde."
)
MSG_CONTA_DESATIVADA = "Conta desativada."
MSG_SESSAO_INVALIDA = "Sessão inválida ou expirada. Faça login novamente."
MSG_LINK_INVALIDO = "Link inválido ou expirado."
MSG_SENHA_IGUAL_ATUAL = "A nova senha deve ser diferente da senha atual."
MSG_RECUPERACAO_GENERICA = "Se o e-mail estiver cadastrado, o link será enviado."


class AuthService:
    def __init__(self, db: Session, email_service: EmailService | None = None) -> None:
        self.db = db
        self.pessoas = UsuarioPessoaRepository(db)
        self.admins = UsuarioAdministrativoRepository(db)
        self.tokens = TokenRepository(db)
        self.emails = email_service or EmailService(db)

    def _localizar_por_email(
        self, email: str
    ) -> tuple[UsuarioPessoa | UsuarioAdministrativo | None, TipoUsuario | None]:
        pessoa = self.pessoas.obter_por_email(email)
        if pessoa is not None:
            return pessoa, TipoUsuario.PESSOA
        admin = self.admins.obter_por_email(email)
        if admin is not None:
            return admin, TipoUsuario.ADMINISTRATIVO
        return None, None

    def _repositorio_de(
        self, tipo: TipoUsuario
    ) -> UsuarioPessoaRepository | UsuarioAdministrativoRepository:
        return self.pessoas if tipo is TipoUsuario.PESSOA else self.admins

    def _emitir_tokens(
        self, usuario: UsuarioPessoa | UsuarioAdministrativo, tipo: TipoUsuario
    ) -> dict:
        perfil = usuario.perfil if tipo is TipoUsuario.ADMINISTRATIVO else None
        access_token, _jti, _exp = security.criar_access_token(usuario.id, tipo, perfil)
        refresh_token = security.gerar_token_opaco()
        self.tokens.criar_refresh(
            token_hash=security.hash_token(refresh_token),
            tipo_usuario=tipo,
            usuario_id=usuario.id,
            expira_em=datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "usuario": {
                "id": usuario.id,
                "nome": usuario.nome,
                "email": usuario.email,
                "tipo": tipo.value,
                "perfil": perfil.value if perfil is not None else None,
            },
        }

    def login(self, email: str, senha: str) -> dict:
        usuario, tipo = self._localizar_por_email(email)
        if usuario is None:
            # Gasta o mesmo tempo de um login real (ver security.HASH_FICTICIO).
            security.verificar_senha(senha, security.HASH_FICTICIO)
            raise CredenciaisInvalidas(MSG_CREDENCIAIS_INVALIDAS)

        agora = datetime.now(UTC)
        repositorio = self._repositorio_de(tipo)

        if usuario.bloqueado_ate is not None:
            if usuario.bloqueado_ate > agora:
                raise ContaBloqueada(MSG_CONTA_BLOQUEADA)
            # Bloqueio vencido: o usuário recomeça com todas as tentativas.
            repositorio.atualizar(usuario, tentativas_login=0, bloqueado_ate=None)

        if not security.verificar_senha(senha, usuario.senha):
            tentativas = usuario.tentativas_login + 1
            campos: dict = {"tentativas_login": tentativas}
            if tentativas >= settings.LOGIN_MAX_TENTATIVAS:
                campos["bloqueado_ate"] = agora + timedelta(minutes=settings.LOGIN_BLOQUEIO_MINUTOS)
            repositorio.atualizar(usuario, **campos)
            self.db.commit()
            raise CredenciaisInvalidas(MSG_CREDENCIAIS_INVALIDAS)

        # O status é checado só depois da senha, para não revelar a quem não sabe
        # a senha que a conta existe e está desativada.
        if usuario.status is not StatusUsuario.ATIVO:
            raise ContaDesativada(MSG_CONTA_DESATIVADA)

        if usuario.tentativas_login:
            repositorio.atualizar(usuario, tentativas_login=0)

        resultado = self._emitir_tokens(usuario, tipo)
        self.db.commit()
        return resultado

    def renovar_tokens(self, refresh_token: str) -> dict:
        """Rotação: o refresh token usado é revogado e um novo par é emitido."""
        registro = self.tokens.obter_refresh_por_hash(security.hash_token(refresh_token))
        agora = datetime.now(UTC)
        if registro is None or registro.revogado_em is not None or registro.expira_em <= agora:
            raise CredenciaisInvalidas(MSG_SESSAO_INVALIDA)

        usuario = self._repositorio_de(registro.tipo_usuario).obter_por_id(registro.usuario_id)
        if usuario is None or usuario.status is not StatusUsuario.ATIVO:
            raise ContaDesativada(MSG_CONTA_DESATIVADA)

        self.tokens.revogar_refresh(registro)
        resultado = self._emitir_tokens(usuario, registro.tipo_usuario)
        self.db.commit()
        return resultado

    def logout(self, usuario_atual: UsuarioAtual, refresh_token: str) -> None:
        registro = self.tokens.obter_refresh_por_hash(security.hash_token(refresh_token))
        if (
            registro is not None
            and registro.revogado_em is None
            and registro.tipo_usuario is usuario_atual.tipo
            and registro.usuario_id == usuario_atual.id
        ):
            self.tokens.revogar_refresh(registro)
        self.tokens.adicionar_jti_na_denylist(usuario_atual.jti, usuario_atual.expira_em)
        self.db.commit()

    def recuperar_senha(self, email: str, cpf: str) -> str:
        """Sempre devolve a mesma mensagem, exista ou não a conta (anti-enumeração)."""
        usuario, tipo = self._localizar_por_email(email)
        if usuario is not None and usuario.cpf == cpf and usuario.status is StatusUsuario.ATIVO:
            token = security.gerar_token_opaco()
            self.tokens.criar_token_redefinicao(
                token_hash=security.hash_token(token),
                tipo_usuario=tipo,
                usuario_id=usuario.id,
                expira_em=datetime.now(UTC)
                + timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES),
            )
            self.db.commit()
            link = f"{settings.FRONTEND_URL}/redefinir-senha?token={token}"
            self.emails.enviar_link_recuperacao(nome=usuario.nome, email=usuario.email, link=link)
        return MSG_RECUPERACAO_GENERICA

    def redefinir_senha(self, token: str, nova_senha: str) -> None:
        registro = self.tokens.obter_token_redefinicao_por_hash(security.hash_token(token))
        agora = datetime.now(UTC)
        if registro is None or registro.usado_em is not None or registro.expira_em <= agora:
            raise RegraDeNegocioViolada(MSG_LINK_INVALIDO)

        repositorio = self._repositorio_de(registro.tipo_usuario)
        usuario = repositorio.obter_por_id(registro.usuario_id)
        if usuario is None:
            raise RegraDeNegocioViolada(MSG_LINK_INVALIDO)
        # Recusa antes de consumir o token: o usuário pode tentar de novo pelo mesmo link.
        if security.verificar_senha(nova_senha, usuario.senha):
            raise RegraDeNegocioViolada(MSG_SENHA_IGUAL_ATUAL)

        repositorio.atualizar(
            usuario,
            senha=security.gerar_hash_senha(nova_senha),
            tentativas_login=0,
            bloqueado_ate=None,
        )
        self.tokens.marcar_token_redefinicao_usado(registro)
        # Encerra as sessões abertas com a senha antiga.
        self.tokens.revogar_todos_refresh_do_usuario(registro.tipo_usuario, registro.usuario_id)
        self.db.commit()
