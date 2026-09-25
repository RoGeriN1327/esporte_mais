from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import UsuarioAtual, require_gestor
from app.schemas.agendamento import ConfiguracoesOut, ConfiguracoesUpdate
from app.services.configuracao_service import ConfiguracaoService

router = APIRouter(prefix="/admin/configuracoes", tags=["Configurações"])

@router.get(
    "",
    response_model=ConfiguracoesOut,
    summary="Consultar configurações",
    description="Prazo mínimo de antecedência para cancelamento e "
    "antecedência do lembrete automático. Exclusivo do Gestor.",
)
def obter_configuracoes(
    _gestor: UsuarioAtual = Depends(require_gestor), db: Session = Depends(get_db)
) -> ConfiguracoesOut:
    return ConfiguracoesOut(**ConfiguracaoService(db).obter_todas())

@router.put(
    "",
    response_model=ConfiguracoesOut,
    summary="Atualizar configurações",
    description="Atualiza o prazo de cancelamento e/ou a antecedência do "
    "lembrete automático. Apenas os campos informados são alterados. Exclusivo do Gestor.",
)
def atualizar_configuracoes(
    dados: ConfiguracoesUpdate,
    _gestor: UsuarioAtual = Depends(require_gestor),
    db: Session = Depends(get_db),
) -> ConfiguracoesOut:
    return ConfiguracoesOut(
        **ConfiguracaoService(db).atualizar(
            cancelamento_antecedencia_minima_horas=dados.cancelamento_antecedencia_minima_horas,
            lembrete_antecedencia_horas=dados.lembrete_antecedencia_horas,
        )
    )
