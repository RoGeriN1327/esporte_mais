import enum


class StatusUsuario(enum.Enum):
    ATIVO = "Ativo"
    DESATIVADO = "Desativado"


class PerfilAdministrativo(enum.Enum):
    GESTOR = "Gestor"
    OPERADOR = "Operador"


class TipoUsuario(enum.Enum):
    PESSOA = "Pessoa"
    ADMINISTRATIVO = "Administrativo"


class StatusQuadra(enum.Enum):
    ATIVA = "Ativa"
    DESATIVADA = "Desativada"


class StatusAgendamento(enum.Enum):
    CONFIRMADO = "Confirmado"
    CANCELADO = "Cancelado"
    CONCLUIDO = "Concluído"
    RENOVADO = "Renovado"
