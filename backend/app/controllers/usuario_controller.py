from fastapi import APIRouter, Request, status

from app.core.deps import PessoaLogada, SessaoDb
from app.core.rate_limit import limiter
from app.schemas.auth import MensagemResponse
from app.schemas.usuario import EmailUpdate, UsuarioPessoaCreate, UsuarioPessoaOut
from app.services.usuario_service import UsuarioService

router = APIRouter(prefix="/usuarios", tags=["Usuários Pessoa"])


@router.post(
    "",
    response_model=UsuarioPessoaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar Usuário Pessoa (auto-cadastro)",
    description="Cadastro público do cidadão: nome, CPF, e-mail e senha (de 8 a 72 "
    "caracteres, com confirmação). CPF e e-mail únicos em todo o sistema. "
    "Conta criada com status Ativo.",
)
@limiter.limit("5/hour")
def cadastrar_usuario(
    request: Request, dados: UsuarioPessoaCreate, db: SessaoDb
) -> UsuarioPessoaOut:
    return UsuarioService(db).cadastrar(dados)


@router.get(
    "/me",
    response_model=UsuarioPessoaOut,
    summary="Visualizar meu perfil",
    description="Dados do Usuário Pessoa autenticado: nome, CPF, e-mail, status e "
    "data de cadastro.",
)
def meu_perfil(usuario: PessoaLogada, db: SessaoDb) -> UsuarioPessoaOut:
    return UsuarioService(db).obter_por_id(usuario.id)


@router.patch(
    "/me",
    response_model=UsuarioPessoaOut,
    summary="Editar meu e-mail",
    description="Atualiza somente o e-mail do Usuário Pessoa autenticado "
    "(validação de formato e unicidade global).",
)
def editar_meu_email(dados: EmailUpdate, usuario: PessoaLogada, db: SessaoDb) -> UsuarioPessoaOut:
    return UsuarioService(db).atualizar_email(usuario.id, dados.email)


@router.post(
    "/me/desativar",
    response_model=MensagemResponse,
    summary="Desativar minha conta",
    description="Desativa a conta do Usuário Pessoa autenticado, encerra as sessões "
    "ativas e envia e-mail de confirmação. A reativação é feita pela administração.",
)
def desativar_minha_conta(usuario: PessoaLogada, db: SessaoDb) -> MensagemResponse:
    UsuarioService(db).desativar_propria_conta(usuario)
    return MensagemResponse(mensagem="Conta desativada com sucesso.")
