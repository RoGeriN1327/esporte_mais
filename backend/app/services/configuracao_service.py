"""Parâmetros ajustáveis pelo Gestor, guardados na tabela "configuracao".

Enquanto o Gestor não altera um valor, vale o padrão definido aqui.
"""

from sqlalchemy.orm import Session

from app.models import CHAVE_ANTECEDENCIA_CANCELAMENTO, CHAVE_ANTECEDENCIA_LEMBRETE
from app.repositories import ConfiguracaoRepository

ANTECEDENCIA_PADRAO_HORAS = 2
LEMBRETE_PADRAO_HORAS = 24


class ConfiguracaoService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.configuracoes = ConfiguracaoRepository(db)

    def _obter_int(self, chave: str, padrao: int) -> int:
        valor = self.configuracoes.obter_valor(chave)
        return int(valor) if valor is not None else padrao

    def obter_antecedencia_cancelamento_horas(self) -> int:
        return self._obter_int(CHAVE_ANTECEDENCIA_CANCELAMENTO, ANTECEDENCIA_PADRAO_HORAS)

    def obter_lembrete_antecedencia_horas(self) -> int:
        return self._obter_int(CHAVE_ANTECEDENCIA_LEMBRETE, LEMBRETE_PADRAO_HORAS)

    def obter_todas(self) -> dict[str, int]:
        return {
            "cancelamento_antecedencia_minima_horas": self.obter_antecedencia_cancelamento_horas(),
            "lembrete_antecedencia_horas": self.obter_lembrete_antecedencia_horas(),
        }

    def atualizar(
        self,
        *,
        cancelamento_antecedencia_minima_horas: int | None = None,
        lembrete_antecedencia_horas: int | None = None,
    ) -> dict[str, int]:
        if cancelamento_antecedencia_minima_horas is not None:
            self.configuracoes.definir_valor(
                CHAVE_ANTECEDENCIA_CANCELAMENTO, str(cancelamento_antecedencia_minima_horas)
            )
        if lembrete_antecedencia_horas is not None:
            self.configuracoes.definir_valor(
                CHAVE_ANTECEDENCIA_LEMBRETE, str(lembrete_antecedencia_horas)
            )
        self.db.commit()
        return self.obter_todas()
