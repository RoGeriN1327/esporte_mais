from fastapi import APIRouter

from app.core.deps import GestorLogado, SessaoDb
from app.schemas.agendamento import ConfiguracoesOut, ConfiguracoesUpdate, RegrasDeUsoOut
from app.services.configuracao_service import ConfiguracaoService
from app.services.quadra_service import DURACAO_SLOT

router = APIRouter(prefix="/admin/configuracoes", tags=["Configurações"])
regras_router = APIRouter(prefix="/regras", tags=["Regras de uso"])

# Regra fixa do sistema, garantida também por índice único no banco (ver agendamento_service).
AGENDAMENTOS_ATIVOS_POR_USUARIO = 1


@regras_router.get(
    "",
    response_model=RegrasDeUsoOut,
    summary="Consultar regras de uso (público)",
    description="Regras de agendamento exibidas na página pública de dúvidas frequentes: "
    "prazo de cancelamento e antecedência do lembrete (configurados pelo Gestor), limite "
    "de agendamentos ativos por cidadão e duração de cada horário. Não exige login.",
)
def obter_regras_de_uso(db: SessaoDb) -> RegrasDeUsoOut:
    configuracoes = ConfiguracaoService(db).obter_todas()
    return RegrasDeUsoOut(
        **configuracoes,
        agendamentos_ativos_por_usuario=AGENDAMENTOS_ATIVOS_POR_USUARIO,
        duracao_horario_minutos=int(DURACAO_SLOT.total_seconds() // 60),
    )


@router.get(
    "",
    response_model=ConfiguracoesOut,
    summary="Consultar configurações",
    description="Prazo mínimo de antecedência para cancelamento e "
    "antecedência do lembrete automático. Exclusivo do Gestor.",
)
def obter_configuracoes(_gestor: GestorLogado, db: SessaoDb) -> ConfiguracoesOut:
    return ConfiguracoesOut(**ConfiguracaoService(db).obter_todas())


@router.put(
    "",
    response_model=ConfiguracoesOut,
    summary="Atualizar configurações",
    description="Atualiza o prazo de cancelamento e/ou a antecedência do "
    "lembrete automático. Apenas os campos informados são alterados. Exclusivo do Gestor.",
)
def atualizar_configuracoes(
    dados: ConfiguracoesUpdate, _gestor: GestorLogado, db: SessaoDb
) -> ConfiguracoesOut:
    return ConfiguracoesOut(
        **ConfiguracaoService(db).atualizar(
            cancelamento_antecedencia_minima_horas=dados.cancelamento_antecedencia_minima_horas,
            lembrete_antecedencia_horas=dados.lembrete_antecedencia_horas,
        )
    )
