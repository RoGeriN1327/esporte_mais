from datetime import date, datetime, time

from pydantic import BaseModel, Field, field_validator

from app.models import Agendamento
from app.models.enums import StatusAgendamento
from app.utils.cpf import cpf_valido, normalizar_cpf

class AgendamentoCreate(BaseModel):

    id_quadra: int
    data: date = Field(description="Data do agendamento (a partir de hoje)")
    hora_inicio: time = Field(description="Horário selecionado entre os disponíveis")

class RenovacaoRequest(BaseModel):

    data: date
    hora_inicio: time

class AgendamentoOut(BaseModel):

    id: int
    id_quadra: int
    nome_quadra: str
    esporte: str
    bairro: str
    data_hora_inicio: datetime
    data_hora_fim: datetime
    status: StatusAgendamento
    data_criacao: datetime

    @classmethod
    def de_modelo(cls, agendamento: Agendamento) -> "AgendamentoOut":
        return cls(
            id=agendamento.id,
            id_quadra=agendamento.id_quadra,
            nome_quadra=agendamento.quadra.nome,
            esporte=agendamento.quadra.esporte,
            bairro=agendamento.quadra.bairro,
            data_hora_inicio=agendamento.data_hora_inicio,
            data_hora_fim=agendamento.data_hora_fim,
            status=agendamento.status,
            data_criacao=agendamento.data_criacao,
        )

class AgendamentoAdminCreate(BaseModel):

    cpf_usuario: str = Field(description="CPF do Usuário Pessoa (com ou sem máscara)")
    id_quadra: int
    data: date
    hora_inicio: time

    @field_validator("cpf_usuario")
    @classmethod
    def validar_cpf(cls, valor: str) -> str:
        cpf = normalizar_cpf(valor)
        if not cpf_valido(cpf):
            raise ValueError("CPF inválido. Informe 11 dígitos numéricos válidos.")
        return cpf

class RemarcacaoRequest(BaseModel):

    data: date
    hora_inicio: time

class AgendamentoAdminOut(AgendamentoOut):

    nome_usuario: str
    cpf_usuario: str
    id_admin_responsavel: int | None

    @classmethod
    def de_modelo(cls, agendamento: Agendamento) -> "AgendamentoAdminOut":
        base = AgendamentoOut.de_modelo(agendamento)
        return cls(
            **base.model_dump(),
            nome_usuario=agendamento.usuario.nome,
            cpf_usuario=agendamento.usuario.cpf,
            id_admin_responsavel=agendamento.id_admin_responsavel,
        )

class ConfiguracoesOut(BaseModel):

    cancelamento_antecedencia_minima_horas: int
    lembrete_antecedencia_horas: int

class ConfiguracoesUpdate(BaseModel):

    cancelamento_antecedencia_minima_horas: int | None = Field(
        default=None, ge=0, le=168, description="Horas de antecedência mínima (0 a 168)"
    )
    lembrete_antecedencia_horas: int | None = Field(
        default=None, ge=1, le=168, description="D12 — horas de antecedência do lembrete (1 a 168)"
    )
