from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import UsuarioAtual, require_pessoa
from app.schemas.auth import MensagemResponse
from app.schemas.usuario import EmailUpdate, UsuarioPessoaCreate, UsuarioPessoaOut
from app.services.usuario_service import UsuarioService

router = APIRouter(prefix="/usuarios", tags=["Usuários Pessoa"])

@router.post(
    "",
    response_model=UsuarioPessoaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar Usuário Pessoa (auto-cadastro)",
    description="Cadastro público do cidadão: nome, CPF, e-mail e senha (mínimo 8 "
    "caracteres, com confirmação). CPF e e-mail únicos em todo o sistema. "
    "Conta criada com status Ativo.",
)
def cadastrar_usuario(dados: UsuarioPessoaCreate, db: Session = Depends(get_db)) -> UsuarioPessoaOut:
    return UsuarioService(db).cadastrar(dados)

@router.get(
    "/me",
    response_model=UsuarioPessoaOut,
    summary="Visualizar meu perfil",
    description="Dados do Usuário Pessoa autenticado: nome, CPF, e-mail, status e "
    "data de cadastro.",
)
def meu_perfil(
    usuario: UsuarioAtual = Depends(require_pessoa), db: Session = Depends(get_db)
) -> UsuarioPessoaOut:
    return UsuarioService(db).obter_por_id(usuario.id)

@router.patch(
    "/me",
    response_model=UsuarioPessoaOut,
    summary="Editar meu e-mail",
    description="Atualiza somente o e-mail do Usuário Pessoa autenticado "
    "(validação de formato e unicidade global).",
)
def editar_meu_email(
    dados: EmailUpdate,
    usuario: UsuarioAtual = Depends(require_pessoa),
    db: Session = Depends(get_db),
) -> UsuarioPessoaOut:
    return UsuarioService(db).atualizar_email(usuario.id, dados.email)

@router.post(
    "/me/desativar",
    response_model=MensagemResponse,
    summary="Desativar minha conta",
    description="Desativa a conta do Usuário Pessoa autenticado, encerra as sessões "
    "ativas e envia e-mail de confirmação. A reativação é feita pela administração.",
)
def desativar_minha_conta(
    usuario: UsuarioAtual = Depends(require_pessoa), db: Session = Depends(get_db)
) -> MensagemResponse:
    UsuarioService(db).desativar_propria_conta(usuario)
    return MensagemResponse(mensagem="Conta desativada com sucesso.")
