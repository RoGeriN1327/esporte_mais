"""Unitários — regras de validação de entrada (app/schemas/*).

Cada schema Pydantic implementa regras do cadastro: tamanho de nome, formato de
CPF/e-mail, tamanho e confirmação de senha, esportes permitidos, grade de
horários e limites das configurações.
"""

from datetime import time

import pytest
from pydantic import ValidationError

from app.models import PerfilAdministrativo
from app.schemas.admin import AdministradorCreate
from app.schemas.agendamento import AgendamentoAdminCreate, ConfiguracoesUpdate
from app.schemas.auth import LoginRequest, RecuperarSenhaRequest, RedefinirSenhaRequest
from app.schemas.quadra import (
    ESPORTES_VALIDOS,
    FaixaHorariaIn,
    QuadraAdminCreate,
    QuadraAdminUpdate,
)
from app.schemas.usuario import EmailUpdate, UsuarioPessoaCreate

pytestmark = pytest.mark.unitario

CPF_VALIDO = "52998224725"


def _cadastro(**alteracoes) -> dict:
    dados = {
        "nome": "Maria da Silva",
        "cpf": "529.982.247-25",
        "email": "maria@teste.com",
        "senha": "Senha@123",
        "confirmar_senha": "Senha@123",
    }
    dados.update(alteracoes)
    return dados


def _com_senha(senha: str) -> dict:
    return _cadastro(senha=senha, confirmar_senha=senha)


def _erros(modelo, dados: dict) -> str:
    """Valida os dados e devolve as mensagens de erro; falha se forem aceitos."""
    try:
        modelo(**dados)
    except ValidationError as erro:
        return " | ".join(e["msg"] for e in erro.errors())
    pytest.fail(f"{modelo.__name__} aceitou dados inválidos: {dados}")


class TestCadastroUsuarioPessoa:
    def test_dados_validos_sao_normalizados(self):
        dados = UsuarioPessoaCreate(**_cadastro(nome="  Maria da Silva  ", email="Maria@Teste.COM"))
        assert dados.nome == "Maria da Silva"
        assert dados.cpf == CPF_VALIDO
        assert dados.email == "maria@teste.com"

    def test_nome_obrigatorio_com_no_maximo_100_caracteres(self):
        for nome in ("", "   "):
            assert "O nome é obrigatório." in _erros(UsuarioPessoaCreate, _cadastro(nome=nome))
        assert len(UsuarioPessoaCreate(**_cadastro(nome="A" * 100)).nome) == 100
        mensagens = _erros(UsuarioPessoaCreate, _cadastro(nome="A" * 101))
        assert "no máximo 100 caracteres" in mensagens

    def test_cpf_invalido_e_recusado(self):
        for cpf in ("529.982.247-24", "111.111.111-11", "123", ""):
            assert "CPF inválido" in _erros(UsuarioPessoaCreate, _cadastro(cpf=cpf))

    def test_email_com_formato_invalido_e_recusado(self):
        for email in ("maria", "maria@", "@teste.com", "maria teste@x.com"):
            _erros(UsuarioPessoaCreate, _cadastro(email=email))

    def test_senha_deve_ter_de_8_caracteres_a_72_bytes(self):
        assert "no mínimo 8 caracteres" in _erros(UsuarioPessoaCreate, _com_senha("Abc@123"))
        assert UsuarioPessoaCreate(**_com_senha("Abc@1234"))
        assert UsuarioPessoaCreate(**_com_senha("A" * 72))
        # O bcrypt não processa senhas acima de 72 bytes; o limite precisa ser
        # informado ao usuário na validação, e não estourar como erro interno.
        # "ç" ocupa 2 bytes em UTF-8: 37 x 2 = 74 bytes.
        for senha in ("A" * 73, "A" * 100, "ç" * 37):
            _erros(UsuarioPessoaCreate, _com_senha(senha))

    def test_confirmacao_de_senha_diferente_e_recusada(self):
        mensagens = _erros(UsuarioPessoaCreate, _cadastro(confirmar_senha="Senha@124"))
        assert "confirmação de senha não confere" in mensagens

    def test_todos_os_campos_sao_obrigatorios(self):
        for campo in ("nome", "cpf", "email", "senha", "confirmar_senha"):
            dados = _cadastro()
            del dados[campo]
            _erros(UsuarioPessoaCreate, dados)


class TestRedefinicaoESenhas:
    def test_redefinicao_aplica_as_mesmas_regras_de_senha(self):
        def pedido(senha, confirmar=None):
            return {"token": "t", "nova_senha": senha, "confirmar_senha": confirmar or senha}

        assert "no mínimo 8 caracteres" in _erros(RedefinirSenhaRequest, pedido("1234567"))
        _erros(RedefinirSenhaRequest, pedido("A" * 73))
        assert "não confere" in _erros(RedefinirSenhaRequest, pedido("12345678", "12345679"))
        assert RedefinirSenhaRequest(**pedido("12345678"))

    def test_recuperacao_normaliza_email_e_valida_cpf(self):
        dados = RecuperarSenhaRequest(email="MARIA@TESTE.COM", cpf="529.982.247-25")
        assert (dados.email, dados.cpf) == ("maria@teste.com", CPF_VALIDO)
        _erros(RecuperarSenhaRequest, {"email": "maria@teste.com", "cpf": "000.000.000-00"})

    def test_login_e_edicao_de_email_normalizam_para_minusculas(self):
        assert LoginRequest(email="Maria@Teste.Com", senha="x").email == "maria@teste.com"
        assert EmailUpdate(email="NOVO@Teste.com").email == "novo@teste.com"
        _erros(EmailUpdate, {"email": "sem-arroba"})


class TestCadastroAdministrativo:
    def test_administrador_valido(self):
        dados = AdministradorCreate(
            nome="Operador", cpf="529.982.247-25", email="OP@RV.GO.GOV.BR", perfil="Operador"
        )
        assert dados.perfil is PerfilAdministrativo.OPERADOR
        assert dados.cpf == CPF_VALIDO
        assert dados.email == "op@rv.go.gov.br"

    def test_perfil_deve_ser_gestor_ou_operador(self):
        for perfil in ("Administrador", "gestor", "", "Pessoa"):
            _erros(
                AdministradorCreate,
                {"nome": "X", "cpf": CPF_VALIDO, "email": "x@x.com", "perfil": perfil},
            )

    def test_agendamento_administrativo_normaliza_e_valida_cpf(self):
        dados = {"id_quadra": 1, "data": "2030-03-05", "hora_inicio": "08:00"}
        assert AgendamentoAdminCreate(cpf_usuario="529.982.247-25", **dados).cpf_usuario == (
            CPF_VALIDO
        )
        _erros(AgendamentoAdminCreate, {"cpf_usuario": "529.982.247-26", **dados})


class TestFaixaHoraria:
    def test_dia_da_semana_de_0_a_6(self):
        for dia in (0, 3, 6):
            assert FaixaHorariaIn(dia_semana=dia, hora_inicio=time(8), hora_fim=time(9))
        for dia in (-1, 7):
            _erros(FaixaHorariaIn, {"dia_semana": dia, "hora_inicio": time(8), "hora_fim": time(9)})

    def test_faixa_deve_comportar_ao_menos_1_hora(self):
        assert FaixaHorariaIn(dia_semana=0, hora_inicio=time(8), hora_fim=time(9))
        mensagens = _erros(
            FaixaHorariaIn, {"dia_semana": 0, "hora_inicio": time(8), "hora_fim": time(8, 59)}
        )
        assert "ao menos um horário de 1 hora" in mensagens
        # Fim igual ou anterior ao início.
        for inicio, fim in ((time(8), time(8)), (time(18), time(8))):
            _erros(FaixaHorariaIn, {"dia_semana": 0, "hora_inicio": inicio, "hora_fim": fim})


def _quadra(**alteracoes) -> dict:
    dados = {
        "nome": "Quadra do Setor Morada do Sol",
        "endereco": "Rua 10, s/n",
        "bairro": "Morada do Sol",
        "descricao": "Quadra poliesportiva coberta",
        "esportes": ["Futsal"],
        "faixas": [{"dia_semana": 0, "hora_inicio": "08:00", "hora_fim": "12:00"}],
    }
    dados.update(alteracoes)
    return dados


def _faixa(dia: int, inicio: str, fim: str) -> dict:
    return {"dia_semana": dia, "hora_inicio": inicio, "hora_fim": fim}


class TestCadastroDeQuadra:
    def test_somente_esportes_da_lista_oficial_sao_aceitos(self):
        assert QuadraAdminCreate(**_quadra(esportes=list(ESPORTES_VALIDOS)))
        for esporte in ("Xadrez", "futsal", "Volei", ""):
            mensagens = _erros(QuadraAdminCreate, _quadra(esportes=[esporte]))
            assert "Esporte inválido" in mensagens

    def test_ao_menos_um_esporte_sem_repeticao(self):
        mensagens = _erros(QuadraAdminCreate, _quadra(esportes=["Futsal", "Futsal"]))
        assert "Esportes repetidos" in mensagens
        _erros(QuadraAdminCreate, _quadra(esportes=[]))

    def test_grade_de_horarios_e_obrigatoria(self):
        _erros(QuadraAdminCreate, _quadra(faixas=[]))

    def test_campos_de_texto_obrigatorios_e_sem_espacos_nas_pontas(self):
        for campo in ("nome", "endereco", "bairro", "descricao"):
            _erros(QuadraAdminCreate, _quadra(**{campo: "   "}))
        assert QuadraAdminCreate(**_quadra(nome="  Quadra A  ")).nome == "Quadra A"

    def test_descricao_limitada_a_300_caracteres(self):
        assert QuadraAdminCreate(**_quadra(descricao="d" * 300))
        _erros(QuadraAdminCreate, _quadra(descricao="d" * 301))

    def test_edicao_aceita_um_unico_esporte_valido(self):
        dados = {**_quadra(), "esporte": "Tênis"}
        del dados["esportes"]
        assert QuadraAdminUpdate(**dados).esporte == "Tênis"
        _erros(QuadraAdminUpdate, {**dados, "esporte": "Golfe"})

    def test_faixas_adjacentes_ou_em_dias_diferentes_sao_aceitas(self):
        adjacentes = [_faixa(0, "08:00", "10:00"), _faixa(0, "10:00", "12:00")]
        dias_diferentes = [_faixa(0, "08:00", "10:00"), _faixa(1, "08:00", "10:00")]
        assert QuadraAdminCreate(**_quadra(faixas=adjacentes))
        assert QuadraAdminCreate(**_quadra(faixas=dias_diferentes))

    def test_faixas_sobrepostas_no_mesmo_dia_sao_recusadas(self):
        # 08:00-10:00 e 08:30-10:30 geram os horários 08:00 e 08:30, que se
        # sobrepõem fisicamente: a mesma quadra poderia ser reservada por duas
        # pessoas entre 08:30 e 09:00. A grade precisa ser recusada.
        faixas = [_faixa(0, "08:00", "10:00"), _faixa(0, "08:30", "10:30")]
        _erros(QuadraAdminCreate, _quadra(faixas=faixas))


class TestConfiguracoes:
    def test_antecedencia_de_cancelamento_de_0_a_168_horas(self):
        for horas in (0, 168):
            assert ConfiguracoesUpdate(cancelamento_antecedencia_minima_horas=horas)
        for horas in (-1, 169):
            _erros(ConfiguracoesUpdate, {"cancelamento_antecedencia_minima_horas": horas})

    def test_antecedencia_do_lembrete_de_1_a_168_horas(self):
        for horas in (1, 168):
            assert ConfiguracoesUpdate(lembrete_antecedencia_horas=horas)
        for horas in (0, 169):
            _erros(ConfiguracoesUpdate, {"lembrete_antecedencia_horas": horas})

    def test_campos_sao_opcionais_para_atualizacao_parcial(self):
        dados = ConfiguracoesUpdate()
        assert dados.cancelamento_antecedencia_minima_horas is None
        assert dados.lembrete_antecedencia_horas is None
