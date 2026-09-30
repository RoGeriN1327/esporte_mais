"""Gestão de usuários pela administração: administradores (só Gestor) e
cidadãos (Gestor e Operador).
"""

from sqlalchemy.orm import Session

from app.core import security
from app.core.deps import UsuarioAtual
from app.exceptions import RecursoNaoEncontrado, RegraDeNegocioViolada
from app.models import StatusUsuario, TipoUsuario, UsuarioAdministrativo, UsuarioPessoa
from app.repositories import (
    TokenRepository,
    UsuarioAdministrativoRepository,
    UsuarioPessoaRepository,
)
from app.schemas.admin import AdministradorCreate, AdministradorUpdate, UsuarioPessoaAdminCreate
from app.services.agendamento_service import AgendamentoService
from app.services.email_service import EmailService
from app.services.usuario_service import UsuarioService

MSG_ADMIN_NAO_ENCONTRADO = "Administrador não encontrado."
MSG_USUARIO_NAO_ENCONTRADO = "Usuário não encontrado."
MSG_AUTO_DESATIVACAO = "Auto desativação administrativa não é permitida."


class AdminService:
    def __init__(self, db: Session, email_service: EmailService | None = None) -> None:
        self.db = db
        self.pessoas = UsuarioPessoaRepository(db)
        self.admins = UsuarioAdministrativoRepository(db)
        self.tokens = TokenRepository(db)
        self.emails = email_service or EmailService(db)
        self._usuarios = UsuarioService(db, email_service=self.emails)

    # --- Administradores ----------------------------------------------------

    def listar_administradores(self) -> list[UsuarioAdministrativo]:
        return self.admins.listar()

    def criar_administrador(self, dados: AdministradorCreate) -> UsuarioAdministrativo:
        self._usuarios.validar_unicidade_global(cpf=dados.cpf, email=dados.email)
        senha_temporaria = security.gerar_senha_temporaria()
        admin = self.admins.criar(
            nome=dados.nome,
            cpf=dados.cpf,
            email=dados.email,
            senha_hash=security.gerar_hash_senha(senha_temporaria),
            perfil=dados.perfil,
        )
        self.db.commit()
        self.emails.enviar_boas_vindas_administrador(
            nome=admin.nome,
            email=admin.email,
            perfil=admin.perfil.value,
            senha_temporaria=senha_temporaria,
        )
        return admin

    def editar_administrador(
        self, admin_id: int, dados: AdministradorUpdate
    ) -> UsuarioAdministrativo:
        admin = self.admins.obter_por_id(admin_id)
        if admin is None:
            raise RecursoNaoEncontrado(MSG_ADMIN_NAO_ENCONTRADO)
        self._usuarios.validar_unicidade_global(
            cpf=dados.cpf,
            email=dados.email,
            ignorar_tipo=TipoUsuario.ADMINISTRATIVO,
            ignorar_id=admin_id,
        )
        self.admins.atualizar(
            admin, nome=dados.nome, cpf=dados.cpf, email=dados.email, perfil=dados.perfil
        )
        self.db.commit()
        return admin

    def desativar_administrador(self, admin_id: int, gestor_atual: UsuarioAtual) -> None:
        if admin_id == gestor_atual.id:
            raise RegraDeNegocioViolada(MSG_AUTO_DESATIVACAO)
        admin = self.admins.obter_por_id(admin_id)
        if admin is None:
            raise RecursoNaoEncontrado(MSG_ADMIN_NAO_ENCONTRADO)
        self.admins.atualizar(admin, status=StatusUsuario.DESATIVADO)
        self.tokens.revogar_todos_refresh_do_usuario(TipoUsuario.ADMINISTRATIVO, admin.id)
        self.db.commit()

    # --- Usuários Pessoa (cidadãos) -----------------------------------------

    def listar_usuarios_pessoa(self) -> list[UsuarioPessoa]:
        return self.pessoas.listar()

    def criar_usuario_pessoa(self, dados: UsuarioPessoaAdminCreate) -> UsuarioPessoa:
        self._usuarios.validar_unicidade_global(cpf=dados.cpf, email=dados.email)
        senha = security.gerar_senha_temporaria()
        usuario = self.pessoas.criar(
            nome=dados.nome,
            cpf=dados.cpf,
            email=dados.email,
            senha_hash=security.gerar_hash_senha(senha),
        )
        self.db.commit()
        self.emails.enviar_boas_vindas_pessoa(nome=usuario.nome, email=usuario.email, senha=senha)
        return usuario

    def desativar_usuario_pessoa(self, usuario_id: int) -> None:
        usuario = self.pessoas.obter_por_id(usuario_id)
        if usuario is None:
            raise RecursoNaoEncontrado(MSG_USUARIO_NAO_ENCONTRADO)

        agendamentos = AgendamentoService(self.db, email_service=self.emails)
        cancelados = agendamentos.cancelar_confirmados_por_desativacao(usuario)
        self.pessoas.atualizar(usuario, status=StatusUsuario.DESATIVADO)
        self.tokens.revogar_todos_refresh_do_usuario(TipoUsuario.PESSOA, usuario.id)
        self.db.commit()

        agendamentos.notificar_cancelamentos(usuario.nome, usuario.email, cancelados)
        self.emails.enviar_confirmacao_desativacao(nome=usuario.nome, email=usuario.email)

    def reativar_usuario_pessoa(self, usuario_id: int) -> UsuarioPessoa:
        usuario = self.pessoas.obter_por_id(usuario_id)
        if usuario is None:
            raise RecursoNaoEncontrado(MSG_USUARIO_NAO_ENCONTRADO)
        self.pessoas.atualizar(
            usuario, status=StatusUsuario.ATIVO, tentativas_login=0, bloqueado_ate=None
        )
        self.db.commit()
        return usuario
