"""Fábricas de dados e utilitários compartilhados pelos testes.

As fábricas gravam direto no banco (sem passar pela API) para montar o cenário
de cada teste — por exemplo, um agendamento já concluído no passado — e deixar
a API/serviço sob teste exercitar apenas a regra verificada.
"""

import itertools
import threading
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.core import security
from app.core.deps import UsuarioAtual
from app.models import (
    Agendamento,
    PerfilAdministrativo,
    Quadra,
    QuadraFaixaHoraria,
    StatusAgendamento,
    StatusQuadra,
    StatusUsuario,
    TipoUsuario,
    UsuarioAdministrativo,
    UsuarioPessoa,
)

FUSO = ZoneInfo("America/Sao_Paulo")

# "Agora" congelado dos testes: segunda-feira, 04/03/2030, 08:00 (Brasília).
HOJE = date(2030, 3, 4)
AMANHA = HOJE + timedelta(days=1)
ONTEM = HOJE - timedelta(days=1)
AGORA = datetime(2030, 3, 4, 8, 0, tzinfo=FUSO)

SENHA_PADRAO = "Senha@123"

# Grade padrão: todos os dias da semana, das 08:00 às 12:00 (4 horários de 1h).
GRADE_PADRAO = tuple((dia, time(8), time(12)) for dia in range(7))

_sequencia = itertools.count(1)


def em(dia: date, hora: int, minuto: int = 0) -> datetime:
    """Data/hora local (Brasília) com fuso — igual ao que a aplicação grava."""
    return datetime.combine(dia, time(hora, minuto), tzinfo=FUSO)


def instante(iso: str) -> datetime:
    """Converte a data/hora ISO da API (ex.: '2030-03-05T12:00:00Z') para comparação.

    A API pode serializar em UTC ou com o fuso local; o que importa é o instante.
    """
    return datetime.fromisoformat(iso)


def gerar_cpf(base: int) -> str:
    """Gera um CPF válido a partir de um número base (até 9 dígitos)."""
    digitos = [int(c) for c in f"{base:09d}"[-9:]]
    for posicao in (9, 10):
        soma = sum(d * ((posicao + 1) - i) for i, d in enumerate(digitos))
        digito = (soma * 10) % 11
        digitos.append(0 if digito == 10 else digito)
    return "".join(map(str, digitos))


def mascarar_cpf(cpf: str) -> str:
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


def _proximo() -> int:
    return next(_sequencia)


def criar_pessoa(
    db: Session,
    *,
    nome: str | None = None,
    cpf: str | None = None,
    email: str | None = None,
    senha: str = SENHA_PADRAO,
    status: StatusUsuario = StatusUsuario.ATIVO,
) -> UsuarioPessoa:
    n = _proximo()
    usuario = UsuarioPessoa(
        nome=nome or f"Cidadão {n}",
        cpf=cpf or gerar_cpf(100_000_000 + n),
        email=email or f"cidadao{n}@teste.com",
        senha=security.gerar_hash_senha(senha),
        status=status,
    )
    db.add(usuario)
    db.commit()
    return usuario


def criar_admin(
    db: Session,
    *,
    perfil: PerfilAdministrativo = PerfilAdministrativo.GESTOR,
    nome: str | None = None,
    cpf: str | None = None,
    email: str | None = None,
    senha: str = SENHA_PADRAO,
    status: StatusUsuario = StatusUsuario.ATIVO,
) -> UsuarioAdministrativo:
    n = _proximo()
    admin = UsuarioAdministrativo(
        nome=nome or f"{perfil.value} {n}",
        cpf=cpf or gerar_cpf(200_000_000 + n),
        email=email or f"{perfil.value.lower()}{n}@prefeitura.gov.br",
        senha=security.gerar_hash_senha(senha),
        perfil=perfil,
        status=status,
    )
    db.add(admin)
    db.commit()
    return admin


def criar_quadra(
    db: Session,
    *,
    nome: str = "Quadra Central",
    esporte: str = "Futebol",
    bairro: str = "Centro",
    endereco: str = "Rua 1, 100",
    descricao: str = "Quadra coberta com iluminação",
    faixas=GRADE_PADRAO,
    status: StatusQuadra = StatusQuadra.ATIVA,
) -> Quadra:
    quadra = Quadra(
        nome=nome,
        descricao=descricao,
        endereco=endereco,
        bairro=bairro,
        esporte=esporte,
        status=status,
    )
    quadra.faixas_horarias = [
        QuadraFaixaHoraria(dia_semana=d, hora_inicio=i, hora_fim=f) for d, i, f in faixas
    ]
    db.add(quadra)
    db.commit()
    return quadra


def criar_agendamento(
    db: Session,
    *,
    usuario: UsuarioPessoa,
    quadra: Quadra,
    inicio: datetime,
    status: StatusAgendamento = StatusAgendamento.CONFIRMADO,
    lembrete_enviado_em: datetime | None = None,
) -> Agendamento:
    agendamento = Agendamento(
        id_usuario=usuario.id,
        id_quadra=quadra.id,
        data_hora_inicio=inicio,
        data_hora_fim=inicio + timedelta(hours=1),
        status=status,
        lembrete_enviado_em=lembrete_enviado_em,
    )
    db.add(agendamento)
    db.commit()
    return agendamento


def autenticar(client, email: str, senha: str = SENHA_PADRAO) -> dict[str, str]:
    """Faz login pela API e devolve o cabeçalho Authorization pronto para uso."""
    resposta = client.post("/auth/login", json={"email": email, "senha": senha})
    assert resposta.status_code == 200, resposta.text
    return {"Authorization": f"Bearer {resposta.json()['access_token']}"}


def login_completo(client, email: str, senha: str = SENHA_PADRAO) -> dict:
    resposta = client.post("/auth/login", json={"email": email, "senha": senha})
    assert resposta.status_code == 200, resposta.text
    return resposta.json()


def eventos(caixa: list[dict], evento: str, para: str | None = None) -> list[dict]:
    """Filtra os e-mails capturados por tipo de evento (e destinatário)."""
    return [e for e in caixa if e["evento"] == evento and (para is None or e["para"] == para)]


def usuario_atual(usuario, perfil: PerfilAdministrativo | None = None) -> UsuarioAtual:
    """Monta o UsuarioAtual (normalmente extraído do JWT) para chamar serviços direto."""
    tipo = TipoUsuario.PESSOA if isinstance(usuario, UsuarioPessoa) else TipoUsuario.ADMINISTRATIVO
    return UsuarioAtual(
        id=usuario.id,
        nome=usuario.nome,
        email=usuario.email,
        tipo=tipo,
        perfil=perfil,
        jti="teste",
        expira_em=AGORA + timedelta(minutes=30),
    )


def executar_em_paralelo(monkeypatch, tarefas) -> list[str]:
    """Executa as tarefas em threads que passam pela validação AO MESMO TEMPO.

    Uma barreira segura cada thread logo após ``_validar_slot``: todas verificam
    a disponibilidade antes de qualquer uma gravar, reproduzindo a condição de
    corrida de dois cliques simultâneos. Só o banco pode impedir a duplicidade.
    Retorna, ordenado, "ok" ou a mensagem de conflito de cada tarefa.
    """
    from app.core.database import SessionLocal
    from app.exceptions import ConflitoDeDados
    from app.services.agendamento_service import AgendamentoService

    barreira = threading.Barrier(len(tarefas), timeout=10)
    original = AgendamentoService._validar_slot

    def validar_e_aguardar(self, *args):
        original(self, *args)
        barreira.wait()

    monkeypatch.setattr(AgendamentoService, "_validar_slot", validar_e_aguardar)
    resultados: list[str] = []

    def executar(tarefa):
        with SessionLocal() as sessao:
            try:
                tarefa(AgendamentoService(sessao))
                resultados.append("ok")
            except ConflitoDeDados as erro:
                resultados.append(erro.mensagem)

    threads = [threading.Thread(target=executar, args=(t,)) for t in tarefas]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=15)
    return sorted(resultados)
