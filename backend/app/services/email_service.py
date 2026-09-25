import logging
import smtplib
from email.mime.text import MIMEText

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Agendamento, Notificacao
from app.utils import tempo

logger = logging.getLogger("esporte_mais.email")

def _formatar_horario(agendamento: Agendamento) -> tuple[str, str, str]:
    inicio = agendamento.data_hora_inicio.astimezone(tempo.fuso())
    fim = agendamento.data_hora_fim.astimezone(tempo.fuso())
    return inicio.strftime("%d/%m/%Y"), inicio.strftime("%H:%M"), fim.strftime("%H:%M")

class EmailService:
    def __init__(self, db: Session | None = None) -> None:

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
        except Exception:

            sucesso = False
            logger.exception(
                "Falha ao enviar e-mail para %s (assunto: %s)", destinatario, assunto
            )
        self._registrar(destinatario, assunto, evento, sucesso)

    def _registrar(self, destinatario: str, assunto: str, evento: str, sucesso: bool) -> None:
        registro = Notificacao(
            destinatario=destinatario, assunto=assunto, evento=evento, sucesso=sucesso
        )
        try:
            if self._db is not None:
                self._db.add(registro)
                self._db.commit()
            else:
                from app.core.database import SessionLocal

                with SessionLocal() as db:
                    db.add(registro)
                    db.commit()
        except Exception:
            logger.exception("Falha ao registrar notificação para %s", destinatario)

    def enviar_boas_vindas_administrador(
        self, *, nome: str, email: str, perfil: str, senha_temporaria: str
    ) -> None:
        corpo = (
            f"Olá, {nome}!\n\n"
            f"Sua conta administrativa ({perfil}) foi criada no Esporte+.\n\n"
            f"Acesse com o e-mail {email} e a senha temporária abaixo:\n\n"
            f"    {senha_temporaria}\n\n"
            f"Recomendamos redefinir sua senha após o primeiro acesso "
            f"(opção \"Esqueci minha senha\").\n\n"
            f"Equipe Esporte+ — Secretaria Municipal de Esportes de Rio Verde - GO"
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
            f"(opção \"Esqueci minha senha\").\n\n"
            f"Equipe Esporte+ — Secretaria Municipal de Esportes de Rio Verde - GO"
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
            f"Equipe Esporte+ — Secretaria Municipal de Esportes de Rio Verde - GO"
        )
        self.enviar(email, "Esporte+ — Redefinição de senha", corpo, evento="recuperacao_senha")

    def enviar_confirmacao_agendamento(
        self, *, nome: str, email: str, agendamento: Agendamento
    ) -> None:
        data, inicio, fim = _formatar_horario(agendamento)
        quadra = agendamento.quadra
        corpo = (
            f"Olá, {nome}!\n\n"
            f"Seu agendamento foi confirmado com sucesso:\n\n"
            f"    Quadra: {quadra.nome} ({quadra.esporte})\n"
            f"    Endereço: {quadra.endereco} — {quadra.bairro}\n"
            f"    Data: {data}\n"
            f"    Horário: {inicio} às {fim}\n\n"
            f"Bom jogo!\n\n"
            f"Equipe Esporte+ — Secretaria Municipal de Esportes de Rio Verde - GO"
        )
        self.enviar(
            email, "Esporte+ — Agendamento confirmado", corpo, evento="confirmacao_agendamento"
        )

    def enviar_cancelamento_agendamento(
        self, *, nome: str, email: str, agendamento: Agendamento
    ) -> None:
        data, inicio, fim = _formatar_horario(agendamento)
        quadra = agendamento.quadra
        corpo = (
            f"Olá, {nome}.\n\n"
            f"Seu agendamento foi cancelado:\n\n"
            f"    Quadra: {quadra.nome} ({quadra.esporte})\n"
            f"    Data: {data}\n"
            f"    Horário: {inicio} às {fim}\n\n"
            f"O horário foi liberado para outros usuários.\n\n"
            f"Equipe Esporte+ — Secretaria Municipal de Esportes de Rio Verde - GO"
        )
        self.enviar(
            email, "Esporte+ — Agendamento cancelado", corpo, evento="cancelamento_agendamento"
        )

    def enviar_remarcacao_agendamento(
        self, *, nome: str, email: str, agendamento: Agendamento
    ) -> None:
        data, inicio, fim = _formatar_horario(agendamento)
        quadra = agendamento.quadra
        corpo = (
            f"Olá, {nome}!\n\n"
            f"Seu agendamento foi remarcado pela Secretaria de Esportes:\n\n"
            f"    Quadra: {quadra.nome} ({quadra.esporte})\n"
            f"    Endereço: {quadra.endereco} — {quadra.bairro}\n"
            f"    Nova data: {data}\n"
            f"    Novo horário: {inicio} às {fim}\n\n"
            f"Em caso de dúvida, procure a Secretaria Municipal de Esportes.\n\n"
            f"Equipe Esporte+ — Secretaria Municipal de Esportes de Rio Verde - GO"
        )
        self.enviar(
            email, "Esporte+ — Agendamento remarcado", corpo, evento="remarcacao_agendamento"
        )

    def enviar_confirmacao_renovacao(
        self, *, nome: str, email: str, agendamento: Agendamento
    ) -> None:
        data, inicio, fim = _formatar_horario(agendamento)
        quadra = agendamento.quadra
        corpo = (
            f"Olá, {nome}!\n\n"
            f"Sua renovação foi confirmada. Novo agendamento:\n\n"
            f"    Quadra: {quadra.nome} ({quadra.esporte})\n"
            f"    Endereço: {quadra.endereco} — {quadra.bairro}\n"
            f"    Data: {data}\n"
            f"    Horário: {inicio} às {fim}\n\n"
            f"Bom jogo!\n\n"
            f"Equipe Esporte+ — Secretaria Municipal de Esportes de Rio Verde - GO"
        )
        self.enviar(
            email, "Esporte+ — Renovação confirmada", corpo, evento="confirmacao_renovacao"
        )

    def enviar_lembrete_agendamento(
        self, *, nome: str, email: str, agendamento: Agendamento
    ) -> None:
        data, inicio, fim = _formatar_horario(agendamento)
        quadra = agendamento.quadra
        corpo = (
            f"Olá, {nome}!\n\n"
            f"Passando para lembrar do seu agendamento no Esporte+:\n\n"
            f"    Quadra: {quadra.nome} ({quadra.esporte})\n"
            f"    Endereço: {quadra.endereco} — {quadra.bairro}\n"
            f"    Data: {data}\n"
            f"    Horário: {inicio} às {fim}\n\n"
            f"Bom jogo!\n\n"
            f"Equipe Esporte+ — Secretaria Municipal de Esportes de Rio Verde - GO"
        )
        self.enviar(
            email, "Esporte+ — Lembrete de agendamento", corpo, evento="lembrete_agendamento"
        )

    def enviar_confirmacao_desativacao(self, *, nome: str, email: str) -> None:
        corpo = (
            f"Olá, {nome}.\n\n"
            f"Confirmamos a desativação da sua conta no Esporte+.\n"
            f"Seu histórico foi preservado e a reativação pode ser solicitada "
            f"junto à Secretaria Municipal de Esportes.\n\n"
            f"Equipe Esporte+ — Secretaria Municipal de Esportes de Rio Verde - GO"
        )
        self.enviar(
            email,
            "Esporte+ — Confirmação de desativação de conta",
            corpo,
            evento="confirmacao_desativacao",
        )
