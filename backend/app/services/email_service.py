"""Envio dos e-mails do sistema.

MAIL_MODE=console apenas imprime a mensagem no log (desenvolvimento);
MAIL_MODE=smtp envia pelo servidor configurado em SMTP_*. O conteúdo vem dos templates
em app/emails/templates (texto puro + HTML na mesma mensagem). Toda tentativa,
com sucesso ou falha, é registrada na tabela "notificacao". Uma falha de
envio nunca interrompe a operação que a disparou.
"""

import logging
import smtplib
from email.message import EmailMessage

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.emails.renderizador import renderizar
from app.models import Agendamento, Notificacao
from app.utils import tempo

logger = logging.getLogger("esporte_mais.email")


_DIAS_SEMANA = (
    "segunda-feira",
    "terça-feira",
    "quarta-feira",
    "quinta-feira",
    "sexta-feira",
    "sábado",
    "domingo",
)
_MESES = (
    "janeiro",
    "fevereiro",
    "março",
    "abril",
    "maio",
    "junho",
    "julho",
    "agosto",
    "setembro",
    "outubro",
    "novembro",
    "dezembro",
)


def _dados_do_agendamento(agendamento: Agendamento) -> dict:
    """Dados de um agendamento prontos para os templates, no fuso local (sem depender do locale)."""
    quadra = agendamento.quadra
    inicio = agendamento.data_hora_inicio.astimezone(tempo.fuso())
    fim = agendamento.data_hora_fim.astimezone(tempo.fuso())
    dia_semana = _DIAS_SEMANA[inicio.weekday()]
    mes = _MESES[inicio.month - 1]
    return {
        "quadra": quadra.nome,
        "esporte": quadra.esporte,
        "endereco": quadra.endereco,
        "bairro": quadra.bairro,
        "data": f"{inicio:%d/%m/%Y}",
        "dia_semana": dia_semana,
        "dia_semana_curto": dia_semana[:3],
        "dia": f"{inicio:%d}",
        "mes_curto": mes[:3],
        "data_extensa": f"{dia_semana.capitalize()}, {inicio.day} de {mes}",
        "inicio": f"{inicio:%H:%M}",
        "fim": f"{fim:%H:%M}",
    }


class EmailService:
    def __init__(self, db: Session | None = None) -> None:
        # Sem sessão (ex.: jobs), o registro da notificação abre uma sessão própria.
        self._db = db

    def enviar(
        self,
        destinatario: str,
        assunto: str,
        corpo: str,
        evento: str = "geral",
        html: str | None = None,
    ) -> None:
        """Envia `corpo` (texto puro) e, se houver, `html` como versão alternativa."""
        sucesso = True
        try:
            if settings.MAIL_MODE == "console":
                print(
                    f"\n===== E-MAIL (console) =====\n"
                    f"Para: {destinatario}\nAssunto: {assunto}\n\n{corpo}\n"
                    f"============================\n"
                )
            else:
                self._enviar_smtp(destinatario, assunto, corpo, html)
        except Exception:
            sucesso = False
            logger.exception("Falha ao enviar e-mail para %s (assunto: %s)", destinatario, assunto)
        self._registrar(destinatario, assunto, evento, sucesso)

    def _enviar_smtp(
        self, destinatario: str, assunto: str, corpo: str, html: str | None = None
    ) -> None:
        # multipart/alternative: cada cliente de e-mail exibe a melhor versão que suporta
        mensagem = EmailMessage()
        mensagem.set_content(corpo)
        if html:
            mensagem.add_alternative(html, subtype="html")
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

    def _enviar_template(
        self,
        destinatario: str,
        assunto: str,
        template: str,
        /,
        *,
        evento: str,
        preview: str,
        **contexto,
    ) -> None:
        """Renderiza o template (texto + HTML) e envia.

        Os três primeiros parâmetros são só posicionais para não colidir com variáveis do
        template de mesmo nome (ex.: `email`, exibido nas boas-vindas). Um erro ao montar o
        e-mail é tratado como falha de envio: fica no log e na tabela "notificacao", sem
        interromper a operação que disparou o e-mail.
        """
        try:
            conteudo = renderizar(template, assunto=assunto, preview=preview, **contexto)
        except Exception:
            logger.exception("Falha ao montar o e-mail %r para %s", template, destinatario)
            self._registrar(destinatario, assunto, evento, sucesso=False)
            return
        self.enviar(destinatario, assunto, conteudo.texto, evento=evento, html=conteudo.html)

    # --- Contas -------------------------------------------------------------

    def enviar_boas_vindas_administrador(
        self, *, nome: str, email: str, perfil: str, senha_temporaria: str
    ) -> None:
        self._enviar_template(
            email,
            "Esporte+ — Bem-vindo(a) à equipe administrativa",
            "boas_vindas_administrador",
            evento="boas_vindas_administrador",
            preview=f"Sua conta de {perfil} foi criada. Veja como acessar o painel.",
            nome=nome,
            email=email,
            perfil=perfil,
            senha=senha_temporaria,
        )

    def enviar_boas_vindas_pessoa(self, *, nome: str, email: str, senha: str) -> None:
        self._enviar_template(
            email,
            "Esporte+ — Bem-vindo(a)! Sua conta foi criada",
            "boas_vindas_pessoa",
            evento="boas_vindas_pessoa",
            preview="Sua conta foi criada pela Secretaria de Esportes. Veja como acessar.",
            nome=nome,
            email=email,
            senha=senha,
        )

    def enviar_link_recuperacao(self, *, nome: str, email: str, link: str) -> None:
        self._enviar_template(
            email,
            "Esporte+ — Redefinição de senha",
            "recuperacao_senha",
            evento="recuperacao_senha",
            preview="Use o link para criar uma nova senha. Ele vale por 1 hora.",
            nome=nome,
            link=link,
        )

    def enviar_confirmacao_desativacao(self, *, nome: str, email: str) -> None:
        self._enviar_template(
            email,
            "Esporte+ — Confirmação de desativação de conta",
            "confirmacao_desativacao",
            evento="confirmacao_desativacao",
            preview="Sua conta no Esporte+ foi desativada. O histórico foi preservado.",
            nome=nome,
        )

    # --- Agendamentos -------------------------------------------------------

    def _enviar_agendamento(
        self, *, email: str, nome: str, agendamento: Agendamento, assunto: str, evento: str
    ) -> None:
        """Os e-mails de agendamento usam os mesmos dados; o template tem o nome do evento."""
        dados = _dados_do_agendamento(agendamento)
        self._enviar_template(
            email,
            assunto,
            evento,
            evento=evento,
            preview=f"{dados['quadra']} · {dados['data_extensa']}, às {dados['inicio']}.",
            nome=nome,
            agendamento=dados,
        )

    def enviar_confirmacao_agendamento(
        self, *, nome: str, email: str, agendamento: Agendamento
    ) -> None:
        self._enviar_agendamento(
            email=email,
            nome=nome,
            agendamento=agendamento,
            assunto="Esporte+ — Agendamento confirmado",
            evento="confirmacao_agendamento",
        )

    def enviar_cancelamento_agendamento(
        self, *, nome: str, email: str, agendamento: Agendamento
    ) -> None:
        self._enviar_agendamento(
            email=email,
            nome=nome,
            agendamento=agendamento,
            assunto="Esporte+ — Agendamento cancelado",
            evento="cancelamento_agendamento",
        )

    def enviar_remarcacao_agendamento(
        self, *, nome: str, email: str, agendamento: Agendamento
    ) -> None:
        self._enviar_agendamento(
            email=email,
            nome=nome,
            agendamento=agendamento,
            assunto="Esporte+ — Agendamento remarcado",
            evento="remarcacao_agendamento",
        )

    def enviar_confirmacao_renovacao(
        self, *, nome: str, email: str, agendamento: Agendamento
    ) -> None:
        self._enviar_agendamento(
            email=email,
            nome=nome,
            agendamento=agendamento,
            assunto="Esporte+ — Renovação confirmada",
            evento="confirmacao_renovacao",
        )

    def enviar_lembrete_agendamento(
        self, *, nome: str, email: str, agendamento: Agendamento
    ) -> None:
        self._enviar_agendamento(
            email=email,
            nome=nome,
            agendamento=agendamento,
            assunto="Esporte+ — Lembrete de agendamento",
            evento="lembrete_agendamento",
        )
