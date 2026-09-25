from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import UsuarioAtual, require_admin, require_gestor
from app.schemas.admin import (
    AdministradorCreate,
    AdministradorOut,
    AdministradorUpdate,
    UsuarioPessoaAdminCreate,
)
from app.schemas.auth import MensagemResponse
from app.schemas.usuario import UsuarioPessoaOut
from app.services.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["Administração de Usuários"])

@router.get(
    "/administradores",
    response_model=list[AdministradorOut],
    summary="Listar administradores",
    description="Lista Gestores e Operadores, ativos e desativados. Exclusivo do Gestor.",
)
def listar_administradores(
    _gestor: UsuarioAtual = Depends(require_gestor), db: Session = Depends(get_db)
) -> list[AdministradorOut]:
    return AdminService(db).listar_administradores()

@router.post(
    "/administradores",
    response_model=AdministradorOut,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar administrador (Gestor/Operador)",
    description="Cria um usuário administrativo com perfil Gestor ou Operador. "
    "Uma senha temporária é gerada e enviada por e-mail. Exclusivo do Gestor.",
)
def cadastrar_administrador(
    dados: AdministradorCreate,
    _gestor: UsuarioAtual = Depends(require_gestor),
    db: Session = Depends(get_db),
) -> AdministradorOut:
    return AdminService(db).criar_administrador(dados)

@router.put(
    "/administradores/{admin_id}",
    response_model=AdministradorOut,
    summary="Editar administrador",
    description="Edita nome, CPF, e-mail e perfil de um administrador. "
    "Exclusivo do Gestor.",
)
def editar_administrador(
    admin_id: int,
    dados: AdministradorUpdate,
    _gestor: UsuarioAtual = Depends(require_gestor),
    db: Session = Depends(get_db),
) -> AdministradorOut:
    return AdminService(db).editar_administrador(admin_id, dados)

@router.post(
    "/administradores/{admin_id}/desativar",
    response_model=MensagemResponse,
    summary="Desativar administrador",
    description="Desativa um Gestor/Operador e invalida suas sessões ativas. "
    "Auto-desativação não é permitida. Exclusivo do Gestor.",
)
def desativar_administrador(
    admin_id: int,
    gestor: UsuarioAtual = Depends(require_gestor),
    db: Session = Depends(get_db),
) -> MensagemResponse:
    AdminService(db).desativar_administrador(admin_id, gestor)
    return MensagemResponse(mensagem="Administrador desativado com sucesso.")

@router.get(
    "/usuarios-pessoa",
    response_model=list[UsuarioPessoaOut],
    summary="Listar usuários pessoa",
    description="Lista os cidadãos cadastrados, ativos e desativados. "
    "Acessível a Gestor e Operador.",
)
def listar_usuarios_pessoa(
    _admin: UsuarioAtual = Depends(require_admin), db: Session = Depends(get_db)
) -> list[UsuarioPessoaOut]:
    return AdminService(db).listar_usuarios_pessoa()

@router.post(
    "/usuarios-pessoa",
    response_model=UsuarioPessoaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar usuário pessoa (pela administração)",
    description="Cria um Usuário Pessoa com senha aleatória enviada por e-mail de "
    "boas-vindas. Acessível a Gestor e Operador.",
)
def cadastrar_usuario_pessoa(
    dados: UsuarioPessoaAdminCreate,
    _admin: UsuarioAtual = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UsuarioPessoaOut:
    return AdminService(db).criar_usuario_pessoa(dados)

@router.post(
    "/usuarios-pessoa/{usuario_id}/desativar",
    response_model=MensagemResponse,
    summary="Desativar usuário pessoa",
    description="Desativa o cidadão, encerra suas sessões ativas e envia e-mail de "
    "confirmação. Acessível a Gestor e Operador.",
)
def desativar_usuario_pessoa(
    usuario_id: int,
    _admin: UsuarioAtual = Depends(require_admin),
    db: Session = Depends(get_db),
) -> MensagemResponse:
    AdminService(db).desativar_usuario_pessoa(usuario_id)
    return MensagemResponse(mensagem="Usuário desativado com sucesso.")

@router.post(
    "/usuarios-pessoa/{usuario_id}/reativar",
    response_model=UsuarioPessoaOut,
    summary="Reativar usuário pessoa",
    description="Reativa um cidadão desativado; o login volta a funcionar "
    "imediatamente com as credenciais anteriores. Acessível a Gestor e Operador.",
)
def reativar_usuario_pessoa(
    usuario_id: int,
    _admin: UsuarioAtual = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UsuarioPessoaOut:
    return AdminService(db).reativar_usuario_pessoa(usuario_id)
