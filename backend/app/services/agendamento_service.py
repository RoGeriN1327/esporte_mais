from datetime import date, time, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.deps import UsuarioAtual
from app.exceptions import ConflitoDeDados, RecursoNaoEncontrado, RegraDeNegocioViolada
from app.models import Agendamento, StatusAgendamento, StatusUsuario, UsuarioPessoa
from app.repositories import AgendamentoRepository, UsuarioPessoaRepository
from app.services.configuracao_service import ConfiguracaoService
from app.services.email_service import EmailService
from app.services.quadra_service import DURACAO_SLOT, QuadraService
from app.utils import tempo

MSG_AGENDAMENTO_NAO_ENCONTRADO = "Agendamento não encontrado."
MSG_JA_POSSUI_ATIVO = (
    "Você já possui um agendamento ativo. Cada usuário pode ter apenas um "
    "agendamento confirmado por vez."
)
MSG_HORARIO_OCUPADO = "O horário selecionado acabou de ser ocupado. Escolha outro horário."
MSG_HORARIO_FORA_DA_GRADE = "Horário indisponível para esta quadra na data selecionada."
MSG_PRAZO_ENCERRADO = "O prazo de cancelamento foi encerrado."
MSG_SOMENTE_CONFIRMADO_CANCELA = "Apenas agendamentos confirmados podem ser cancelados."
MSG_SOMENTE_CONCLUIDO_RENOVA = "Apenas agendamentos concluídos podem ser renovados."
MSG_SOMENTE_CONFIRMADO_REMARCA = "Apenas agendamentos confirmados podem ser remarcados."
MSG_USUARIO_NAO_ENCONTRADO = "Usuário não encontrado."
MSG_USUARIO_DESATIVADO = "Usuário desativado não pode receber novos agendamentos."

class AgendamentoService:
    def __init__(self, db: Session, email_service: EmailService | None = None) -> None:
        self.db = db
        self.agendamentos = AgendamentoRepository(db)
        self.pessoas = UsuarioPessoaRepository(db)
        self.quadras = QuadraService(db)
        self.configuracoes = ConfiguracaoService(db)
        self.emails = email_service or EmailService(db)

    def _obter_do_usuario(self, agendamento_id: int, usuario_id: int) -> Agendamento:
        agendamento = self.agendamentos.obter_por_id(agendamento_id)

        if agendamento is None or agendamento.id_usuario != usuario_id:
            raise RecursoNaoEncontrado(MSG_AGENDAMENTO_NAO_ENCONTRADO)
        return agendamento

    def _validar_slot(self, quadra_id: int, dia: date, hora: time) -> None:
        if hora not in self.quadras.slots_da_grade(quadra_id, dia):
            raise RegraDeNegocioViolada(MSG_HORARIO_FORA_DA_GRADE)
        if hora not in self.quadras.horarios_disponiveis(quadra_id, dia):

            raise ConflitoDeDados(MSG_HORARIO_OCUPADO)

    def _gravar_confirmado(
        self,
        usuario_id: int,
        quadra_id: int,
        dia: date,
        hora: time,
        id_admin_responsavel: int | None = None,
    ) -> Agendamento:
        inicio = tempo.combinar(dia, hora)
        try:
            agendamento = self.agendamentos.criar(
                id_usuario=usuario_id,
                id_quadra=quadra_id,
                data_hora_inicio=inicio,
                data_hora_fim=inicio + DURACAO_SLOT,
                id_admin_responsavel=id_admin_responsavel,
            )
            self.db.commit()
        except IntegrityError as erro:
            self.db.rollback()
            if "uq_agendamento_usuario_confirmado" in str(erro.orig):
                raise ConflitoDeDados(MSG_JA_POSSUI_ATIVO)
            raise ConflitoDeDados(MSG_HORARIO_OCUPADO)
        return self.agendamentos.obter_por_id(agendamento.id)

    def criar(self, usuario_atual: UsuarioAtual, quadra_id: int, dia: date, hora: time) -> Agendamento:
        self.quadras.obter_quadra_ativa(quadra_id)

        if self.agendamentos.existe_confirmado_do_usuario(usuario_atual.id):
            raise ConflitoDeDados(MSG_JA_POSSUI_ATIVO)
        self._validar_slot(quadra_id, dia, hora)
        agendamento = self._gravar_confirmado(usuario_atual.id, quadra_id, dia, hora)

        self.emails.enviar_confirmacao_agendamento(
            nome=usuario_atual.nome,
            email=usuario_atual.email,
            agendamento=agendamento,
        )
        return agendamento

    def listar_meus(
        self,
        usuario_id: int,
        *,
        dia: date | None = None,
        nome_quadra: str | None = None,
        esporte: str | None = None,
        status: StatusAgendamento | None = None,
    ) -> list[Agendamento]:
        inicio_dia = fim_dia = None
        if dia is not None:
            inicio_dia = tempo.combinar(dia, time.min)
            fim_dia = inicio_dia + timedelta(days=1)
        return self.agendamentos.listar_do_usuario(
            usuario_id,
            inicio_dia=inicio_dia,
            fim_dia=fim_dia,
            nome_quadra=nome_quadra,
            esporte=esporte,
            status=status,
        )

    def proximo(self, usuario_id: int) -> Agendamento | None:
        return self.agendamentos.proximo_confirmado(usuario_id, tempo.agora_local())

    def cancelar(self, usuario_atual: UsuarioAtual, agendamento_id: int) -> Agendamento:
        agendamento = self._obter_do_usuario(agendamento_id, usuario_atual.id)
        if agendamento.status is not StatusAgendamento.CONFIRMADO:
            raise RegraDeNegocioViolada(MSG_SOMENTE_CONFIRMADO_CANCELA)

        antecedencia = self.configuracoes.obter_antecedencia_cancelamento_horas()
        limite = agendamento.data_hora_inicio - timedelta(hours=antecedencia)
        if tempo.agora_local() > limite:
            raise RegraDeNegocioViolada(MSG_PRAZO_ENCERRADO)

        self.agendamentos.atualizar(agendamento, status=StatusAgendamento.CANCELADO)
        self.db.commit()

        self.emails.enviar_cancelamento_agendamento(
            nome=usuario_atual.nome, email=usuario_atual.email, agendamento=agendamento
        )
        return agendamento

    def renovar(
        self, usuario_atual: UsuarioAtual, agendamento_id: int, dia: date, hora: time
    ) -> Agendamento:
        anterior = self._obter_do_usuario(agendamento_id, usuario_atual.id)

        if anterior.status is not StatusAgendamento.CONCLUIDO:
            raise RegraDeNegocioViolada(MSG_SOMENTE_CONCLUIDO_RENOVA)

        self.quadras.obter_quadra_ativa(anterior.id_quadra)
        if self.agendamentos.existe_confirmado_do_usuario(usuario_atual.id):
            raise ConflitoDeDados(MSG_JA_POSSUI_ATIVO)
        self._validar_slot(anterior.id_quadra, dia, hora)

        self.agendamentos.atualizar(anterior, status=StatusAgendamento.RENOVADO)
        novo = self._gravar_confirmado(usuario_atual.id, anterior.id_quadra, dia, hora)

        self.emails.enviar_confirmacao_renovacao(
            nome=usuario_atual.nome, email=usuario_atual.email, agendamento=novo
        )
        return novo

    def concluir_vencidos(self) -> int:
        total = self.agendamentos.concluir_vencidos(tempo.agora_local())
        self.db.commit()
        return total

    def enviar_lembretes(self) -> int:
        agora = tempo.agora_local()
        antecedencia = self.configuracoes.obter_lembrete_antecedencia_horas()
        pendentes = self.agendamentos.listar_para_lembrete(
            agora, agora + timedelta(hours=antecedencia)
        )
        for agendamento in pendentes:
            self.agendamentos.atualizar(agendamento, lembrete_enviado_em=agora)
        self.db.commit()
        for agendamento in pendentes:
            self.emails.enviar_lembrete_agendamento(
                nome=agendamento.usuario.nome,
                email=agendamento.usuario.email,
                agendamento=agendamento,
            )
        return len(pendentes)

    def listar_consolidado(
        self,
        *,
        dia: date | None = None,
        nome_quadra: str | None = None,
        esporte: str | None = None,
        status: StatusAgendamento | None = None,
        cpf_usuario: str | None = None,
        nome_usuario: str | None = None,
    ) -> list[Agendamento]:
        inicio_dia = fim_dia = None
        if dia is not None:
            inicio_dia = tempo.combinar(dia, time.min)
            fim_dia = inicio_dia + timedelta(days=1)
        return self.agendamentos.listar_consolidado(
            inicio_dia=inicio_dia,
            fim_dia=fim_dia,
            nome_quadra=nome_quadra,
            esporte=esporte,
            status=status,
            cpf_usuario=cpf_usuario,
            nome_usuario=nome_usuario,
        )

    def criar_para_usuario(
        self, admin_atual: UsuarioAtual, cpf_usuario: str, quadra_id: int, dia: date, hora: time
    ) -> Agendamento:
        usuario = self.pessoas.obter_por_cpf(cpf_usuario)
        if usuario is None:
            raise RecursoNaoEncontrado(MSG_USUARIO_NAO_ENCONTRADO)
        if usuario.status is not StatusUsuario.ATIVO:
            raise RegraDeNegocioViolada(MSG_USUARIO_DESATIVADO)
        self.quadras.obter_quadra_ativa(quadra_id)
        if self.agendamentos.existe_confirmado_do_usuario(usuario.id):
            raise ConflitoDeDados(MSG_JA_POSSUI_ATIVO)
        self._validar_slot(quadra_id, dia, hora)
        agendamento = self._gravar_confirmado(
            usuario.id, quadra_id, dia, hora, id_admin_responsavel=admin_atual.id
        )

        self.emails.enviar_confirmacao_agendamento(
            nome=usuario.nome, email=usuario.email, agendamento=agendamento
        )
        return agendamento

    def remarcar(
        self, admin_atual: UsuarioAtual, agendamento_id: int, dia: date, hora: time
    ) -> Agendamento:
        agendamento = self.agendamentos.obter_por_id(agendamento_id)
        if agendamento is None:
            raise RecursoNaoEncontrado(MSG_AGENDAMENTO_NAO_ENCONTRADO)
        if agendamento.status is not StatusAgendamento.CONFIRMADO:
            raise RegraDeNegocioViolada(MSG_SOMENTE_CONFIRMADO_REMARCA)
        self.quadras.obter_quadra_ativa(agendamento.id_quadra)
        self._validar_slot(agendamento.id_quadra, dia, hora)

        inicio = tempo.combinar(dia, hora)
        try:
            self.agendamentos.atualizar(
                agendamento,
                data_hora_inicio=inicio,
                data_hora_fim=inicio + DURACAO_SLOT,
                id_admin_responsavel=admin_atual.id,
            )
            self.db.commit()
        except IntegrityError:

            self.db.rollback()
            raise ConflitoDeDados(MSG_HORARIO_OCUPADO)
        usuario = agendamento.usuario
        self.emails.enviar_remarcacao_agendamento(
            nome=usuario.nome, email=usuario.email, agendamento=agendamento
        )
        return agendamento

    def cancelar_como_admin(self, admin_atual: UsuarioAtual, agendamento_id: int) -> Agendamento:
        agendamento = self.agendamentos.obter_por_id(agendamento_id)
        if agendamento is None:
            raise RecursoNaoEncontrado(MSG_AGENDAMENTO_NAO_ENCONTRADO)
        if agendamento.status is not StatusAgendamento.CONFIRMADO:
            raise RegraDeNegocioViolada(MSG_SOMENTE_CONFIRMADO_CANCELA)
        self.agendamentos.atualizar(
            agendamento,
            status=StatusAgendamento.CANCELADO,
            id_admin_responsavel=admin_atual.id,
        )
        self.db.commit()
        usuario = agendamento.usuario

        self.emails.enviar_cancelamento_agendamento(
            nome=usuario.nome, email=usuario.email, agendamento=agendamento
        )
        return agendamento

    def cancelar_confirmados_por_desativacao(self, usuario: UsuarioPessoa) -> list[Agendamento]:
        cancelados = self.agendamentos.listar_confirmados_do_usuario(usuario.id)
        for agendamento in cancelados:
            self.agendamentos.atualizar(agendamento, status=StatusAgendamento.CANCELADO)
        return cancelados

    def notificar_cancelamentos(self, nome: str, email: str, cancelados: list[Agendamento]) -> None:
        for agendamento in cancelados:
            self.emails.enviar_cancelamento_agendamento(
                nome=nome, email=email, agendamento=agendamento
            )
