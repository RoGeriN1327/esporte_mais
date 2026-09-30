"""Envio dos e-mails do sistema.

MAIL_MODE=console apenas imprime a mensagem no log (desenvolvimento);
MAIL_MODE=smtp envia pelo servidor configurado em SMTP_*. Toda tentativa,
com sucesso ou falha, é registrada na tabela "notificacao". Uma falha de
envio nunca interrompe a operação que a disparou.
"""

import logging
import smtplib
from email.mime.text import MIMEText

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models import Agendamento, Notificacao
from app.utils import tempo

logger = logging.getLogger("esporte_mais.email")

ASSINATURA = "Equipe Esporte+ — Secretaria Municipal de Esportes de Rio Verde - GO"


def _detalhes_do_agendamento(
    agendamento: Agendamento,
    *,
    com_endereco: bool = True,
    rotulo_data: str = "Data",
    rotulo_horario: str = "Horário",
) -> str:
    """Bloco com quadra, endereço, data e horário, no fuso local."""
    quadra = agendamento.quadra
    inicio = agendamento.data_hora_inicio.astimezone(tempo.fuso())
    fim = agendamento.data_hora_fim.astimezone(tempo.fuso())
    linhas = [f"    Quadra: {quadra.nome} ({quadra.esporte})"]
    if com_endereco:
        linhas.append(f"    Endereço: {quadra.endereco} — {quadra.bairro}")
    linhas.append(f"    {rotulo_data}: {inicio:%d/%m/%Y}")
    linhas.append(f"    {rotulo_horario}: {inicio:%H:%M} às {fim:%H:%M}")
    return "\n".join(linhas)


class EmailService:
    def __init__(self, db: Session | None = None) -> None:
        # Sem sessão (ex.: jobs), o registro da notificação abre uma sessão própria.
        self._db = db

    def enviar(self, destinatario: str, assunto: str, corpo: str, evento: str = "geral") -> None:
        sucesso = True
        try:
            if settings.MAIL_MODE == "console":
                print(
                    f"\n===== E-MAIL (console) =====\n"
                    f"Para: {destinatario}\nAssunto: {assunto}\n\n{corpo}\n"
                    f"============================\n"
                )
            else:
                self._enviar_smtp(destinatario, assunto, corpo)
        except Exception:
            sucesso = False
            logger.exception("Falha ao enviar e-mail para %s (assunto: %s)", destinatario, assunto)
        self._registrar(destinatario, assunto, evento, sucesso)

    def _enviar_smtp(self, destinatario: str, assunto: str, corpo: str) -> None:
        mensagem = MIMEText(corpo, "plain", "utf-8")
        mensagem["Subject"] = assunto
        mensagem["From"] = settings.SMTP_FROM
        mensagem["To"] = destinatario
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
            if settings.SMTP_TLS:
                smtp.starttls()
            if settings.SMTP_USER:
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.send_message(mensagem)

    def _registrar(self, destinatario: str, assunto: str, evento: str, sucesso: bool) -> None:
        registro = Notificacao(
            destinatario=destinatario, assunto=assunto, evento=evento, sucesso=sucesso
        )
        try:
            if self._db is not None:
                self._db.add(registro)
                self._db.commit()
            else:
                with SessionLocal() as db:
                    db.add(registro)
                    db.commit()
        except Exception:
            logger.exception("Falha ao registrar notificação para %s", destinatario)

    # --- Contas -------------------------------------------------------------

    def enviar_boas_vindas_administrador(
        self, *, nome: str, email: str, perfil: str, senha_temporaria: str
    ) -> None:
        corpo = (
            f"Olá, {nome}!\n\n"
            f"Sua conta administrativa ({perfil}) foi criada no Esporte+.\n\n"
            f"Acesse com o e-mail {email} e a senha temporária abaixo:\n\n"
            f"    {senha_temporaria}\n\n"
            f"Recomendamos redefinir sua senha após o primeiro acesso "
            f'(opção "Esqueci minha senha").\n\n'
            f"{ASSINATURA}"
        )
        self.enviar(
            email,
            "Esporte+ — Bem-vindo(a) à equipe administrativa",
            corpo,
            evento="boas_vindas_administrador",
        )

    def enviar_boas_vindas_pessoa(self, *, nome: str, email: str, senha: str) -> None:
        corpo = (
            f"Olá, {nome}!\n\n"
            f"Sua conta foi criada no Esporte+ pela equipe da Secretaria de Esportes.\n\n"
            f"Acesse com o e-mail {email} e a senha abaixo:\n\n"
            f"    {senha}\n\n"
            f"Recomendamos redefinir sua senha após o primeiro acesso "
            f'(opção "Esqueci minha senha").\n\n'
            f"{ASSINATURA}"
        )
        self.enviar(
            email,
            "Esporte+ — Bem-vindo(a)! Sua conta foi criada",
            corpo,
            evento="boas_vindas_pessoa",
        )

    def enviar_link_recuperacao(self, *, nome: str, email: str, link: str) -> None:
        corpo = (
            f"Olá, {nome}!\n\n"
            f"Recebemos uma solicitação de redefinição de senha da sua conta no Esporte+.\n\n"
            f"Para criar uma nova senha, acesse o link abaixo (válido por 1 hora):\n\n"
            f"    {link}\n\n"
            f"Se você não fez esta solicitação, ignore este e-mail — sua senha "
            f"permanecerá inalterada.\n\n"
            f"{ASSINATURA}"
        )
        self.enviar(email, "Esporte+ — Redefinição de senha", corpo, evento="recuperacao_senha")

    def enviar_confirmacao_desativacao(self, *, nome: str, email: str) -> None:
        corpo = (
            f"Olá, {nome}.\n\n"
            f"Confirmamos a desativação da sua conta no Esporte+.\n"
            f"Seu histórico foi preservado e a reativação pode ser solicitada "
            f"junto à Secretaria Municipal de Esportes.\n\n"
            f"{ASSINATURA}"
        )
        self.enviar(
            email,
            "Esporte+ — Confirmação de desativação de conta",
            corpo,
            evento="confirmacao_desativacao",
        )

    # --- Agendamentos -------------------------------------------------------

    def enviar_confirmacao_agendamento(
        self, *, nome: str, email: str, agendamento: Agendamento
    ) -> None:
        corpo = (
            f"Olá, {nome}!\n\n"
            f"Seu agendamento foi confirmado com sucesso:\n\n"
            f"{_detalhes_do_agendamento(agendamento)}\n\n"
            f"Bom jogo!\n\n"
            f"{ASSINATURA}"
        )
        self.enviar(
            email, "Esporte+ — Agendamento confirmado", corpo, evento="confirmacao_agendamento"
        )

    def enviar_cancelamento_agendamento(
        self, *, nome: str, email: str, agendamento: Agendamento
    ) -> None:
        corpo = (
            f"Olá, {nome}.\n\n"
            f"Seu agendamento foi cancelado:\n\n"
            f"{_detalhes_do_agendamento(agendamento, com_endereco=False)}\n\n"
            f"O horário foi liberado para outros usuários.\n\n"
            f"{ASSINATURA}"
        )
        self.enviar(
            email, "Esporte+ — Agendamento cancelado", corpo, evento="cancelamento_agendamento"
        )

    def enviar_remarcacao_agendamento(
        self, *, nome: str, email: str, agendamento: Agendamento
    ) -> None:
        detalhes = _detalhes_do_agendamento(
            agendamento, rotulo_data="Nova data", rotulo_horario="Novo horário"
        )
        corpo = (
            f"Olá, {nome}!\n\n"
            f"Seu agendamento foi remarcado pela Secretaria de Esportes:\n\n"
            f"{detalhes}\n\n"
            f"Em caso de dúvida, procure a Secretaria Municipal de Esportes.\n\n"
            f"{ASSINATURA}"
        )
        self.enviar(
            email, "Esporte+ — Agendamento remarcado", corpo, evento="remarcacao_agendamento"
        )

    def enviar_confirmacao_renovacao(
        self, *, nome: str, email: str, agendamento: Agendamento
    ) -> None:
        corpo = (
            f"Olá, {nome}!\n\n"
            f"Sua renovação foi confirmada. Novo agendamento:\n\n"
            f"{_detalhes_do_agendamento(agendamento)}\n\n"
            f"Bom jogo!\n\n"
            f"{ASSINATURA}"
        )
        self.enviar(email, "Esporte+ — Renovação confirmada", corpo, evento="confirmacao_renovacao")

    def enviar_lembrete_agendamento(
        self, *, nome: str, email: str, agendamento: Agendamento
    ) -> None:
        corpo = (
            f"Olá, {nome}!\n\n"
            f"Passando para lembrar do seu agendamento no Esporte+:\n\n"
            f"{_detalhes_do_agendamento(agendamento)}\n\n"
            f"Bom jogo!\n\n"
            f"{ASSINATURA}"
        )
        self.enviar(
            email, "Esporte+ — Lembrete de agendamento", corpo, evento="lembrete_agendamento"
        )
