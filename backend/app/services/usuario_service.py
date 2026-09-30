"""Conta do Usuário Pessoa: cadastro, perfil, troca de e-mail e desativação."""

from sqlalchemy.orm import Session

from app.core import security
from app.core.deps import UsuarioAtual
from app.exceptions import ConflitoDeDados, RecursoNaoEncontrado
from app.models import StatusUsuario, TipoUsuario, UsuarioPessoa
from app.repositories import (
    TokenRepository,
    UsuarioAdministrativoRepository,
    UsuarioPessoaRepository,
)
from app.schemas.usuario import UsuarioPessoaCreate
from app.services.agendamento_service import AgendamentoService
from app.services.email_service import EmailService

MSG_CPF_JA_CADASTRADO = "CPF já cadastrado."
MSG_EMAIL_JA_CADASTRADO = "E-mail já cadastrado."
MSG_USUARIO_NAO_ENCONTRADO = "Usuário não encontrado."


class UsuarioService:
    def __init__(self, db: Session, email_service: EmailService | None = None) -> None:
        self.db = db
        self.pessoas = UsuarioPessoaRepository(db)
        self.admins = UsuarioAdministrativoRepository(db)
        self.tokens = TokenRepository(db)
        self.emails = email_service or EmailService(db)

    def validar_unicidade_global(
        self,
        *,
        cpf: str | None = None,
        email: str | None = None,
        ignorar_tipo: TipoUsuario | None = None,
        ignorar_id: int | None = None,
    ) -> None:
        """CPF e e-mail são únicos entre cidadãos E administradores.

        ignorar_tipo/ignorar_id excluem o próprio usuário da checagem na edição.
        """

        def _conflita(encontrado, tipo: TipoUsuario) -> bool:
            return encontrado is not None and not (
                ignorar_tipo is tipo and ignorar_id == encontrado.id
            )

        if cpf is not None and (
            _conflita(self.pessoas.obter_por_cpf(cpf), TipoUsuario.PESSOA)
            or _conflita(self.admins.obter_por_cpf(cpf), TipoUsuario.ADMINISTRATIVO)
        ):
            raise ConflitoDeDados(MSG_CPF_JA_CADASTRADO)
        if email is not None and (
            _conflita(self.pessoas.obter_por_email(email), TipoUsuario.PESSOA)
            or _conflita(self.admins.obter_por_email(email), TipoUsuario.ADMINISTRATIVO)
        ):
            raise ConflitoDeDados(MSG_EMAIL_JA_CADASTRADO)

    def cadastrar(self, dados: UsuarioPessoaCreate) -> UsuarioPessoa:
        self.validar_unicidade_global(cpf=dados.cpf, email=dados.email)
        usuario = self.pessoas.criar(
            nome=dados.nome,
            cpf=dados.cpf,
            email=dados.email,
            senha_hash=security.gerar_hash_senha(dados.senha),
        )
        self.db.commit()
        return usuario

    def obter_por_id(self, usuario_id: int) -> UsuarioPessoa:
        usuario = self.pessoas.obter_por_id(usuario_id)
        if usuario is None:
            raise RecursoNaoEncontrado(MSG_USUARIO_NAO_ENCONTRADO)
        return usuario

    def atualizar_email(self, usuario_id: int, novo_email: str) -> UsuarioPessoa:
        usuario = self.obter_por_id(usuario_id)
        self.validar_unicidade_global(
            email=novo_email, ignorar_tipo=TipoUsuario.PESSOA, ignorar_id=usuario_id
        )
        self.pessoas.atualizar(usuario, email=novo_email)
        self.db.commit()
        return usuario

    def desativar_propria_conta(self, usuario_atual: UsuarioAtual) -> None:
        usuario = self.obter_por_id(usuario_atual.id)
        agendamentos = AgendamentoService(self.db, email_service=self.emails)
        cancelados = agendamentos.cancelar_confirmados_por_desativacao(usuario)
        self.pessoas.atualizar(usuario, status=StatusUsuario.DESATIVADO)
        self.tokens.revogar_todos_refresh_do_usuario(TipoUsuario.PESSOA, usuario.id)
        self.tokens.adicionar_jti_na_denylist(usuario_atual.jti, usuario_atual.expira_em)
        self.db.commit()

        agendamentos.notificar_cancelamentos(usuario.nome, usuario.email, cancelados)
        self.emails.enviar_confirmacao_desativacao(nome=usuario.nome, email=usuario.email)
