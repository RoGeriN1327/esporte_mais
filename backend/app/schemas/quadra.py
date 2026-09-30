"""Schemas de quadras: consulta pública, horários disponíveis e gestão (admin)."""

from datetime import date, time, timedelta

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import StatusQuadra

ESPORTES_VALIDOS = ("Futebol", "Futsal", "Basquete", "Vôlei", "Tênis", "Handebol")


class QuadraOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    descricao: str
    endereco: str
    bairro: str
    esporte: str
    status: StatusQuadra


class OpcoesFiltroOut(BaseModel):
    esportes: list[str]
    bairros: list[str]


class HorariosDisponiveisOut(BaseModel):
    id_quadra: int
    data: date
    horarios: list[time]


class FaixaHorariaIn(BaseModel):
    dia_semana: int = Field(ge=0, le=6, description="0=segunda ... 6=domingo")
    hora_inicio: time
    hora_fim: time

    @model_validator(mode="after")
    def validar_faixa(self) -> "FaixaHorariaIn":
        inicio = timedelta(hours=self.hora_inicio.hour, minutes=self.hora_inicio.minute)
        fim = timedelta(hours=self.hora_fim.hour, minutes=self.hora_fim.minute)
        if fim - inicio < timedelta(hours=1):
            raise ValueError(
                "A faixa deve comportar ao menos um horário de 1 hora "
                "(hora_fim deve ser pelo menos 1h após hora_inicio)."
            )
        return self


class _DadosQuadraBase(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    endereco: str = Field(min_length=1, max_length=255, description="Endereço completo")
    bairro: str = Field(min_length=1, max_length=100)
    descricao: str = Field(min_length=1, max_length=300)
    faixas: list[FaixaHorariaIn] = Field(min_length=1, description="Grade de horários")

    @field_validator("faixas")
    @classmethod
    def faixas_sem_sobreposicao(cls, faixas: list[FaixaHorariaIn]) -> list[FaixaHorariaIn]:
        # Faixas sobrepostas no mesmo dia gerariam horários que se sobrepõem
        # (ex.: 08:00 e 08:30), permitindo duas reservas da quadra ao mesmo tempo.
        # Faixas adjacentes (08:00-10:00 e 10:00-12:00) são permitidas.
        ordenadas = sorted(faixas, key=lambda f: (f.dia_semana, f.hora_inicio))
        for anterior, atual in zip(ordenadas, ordenadas[1:], strict=False):
            if atual.dia_semana == anterior.dia_semana and atual.hora_inicio < anterior.hora_fim:
                raise ValueError("As faixas de horário de um mesmo dia não podem se sobrepor.")
        return faixas

    @field_validator("nome", "endereco", "bairro", "descricao")
    @classmethod
    def sem_espacos_nas_pontas(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("Campo obrigatório.")
        return valor


def _validar_esporte(valor: str) -> str:
    if valor not in ESPORTES_VALIDOS:
        raise ValueError(f"Esporte inválido. Opções: {', '.join(ESPORTES_VALIDOS)}.")
    return valor


class QuadraAdminCreate(_DadosQuadraBase):
    esportes: list[str] = Field(min_length=1)

    @field_validator("esportes")
    @classmethod
    def validar_esportes(cls, valores: list[str]) -> list[str]:
        for esporte in valores:
            _validar_esporte(esporte)
        if len(set(valores)) != len(valores):
            raise ValueError("Esportes repetidos na seleção.")
        return valores


class QuadraAdminUpdate(_DadosQuadraBase):
    esporte: str

    @field_validator("esporte")
    @classmethod
    def validar_esporte(cls, valor: str) -> str:
        return _validar_esporte(valor)


class FaixaHorariaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    dia_semana: int
    hora_inicio: time
    hora_fim: time


class QuadraAdminOut(QuadraOut):
    model_config = ConfigDict(from_attributes=True)

    faixas: list[FaixaHorariaOut] = Field(validation_alias="faixas_horarias")
