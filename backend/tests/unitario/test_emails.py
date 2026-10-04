"""Unitários — e-mails (app/emails): renderização dos templates em texto puro e HTML."""

import pytest

from app.core.config import settings
from app.emails.renderizador import renderizar

pytestmark = pytest.mark.unitario

AGENDAMENTO = {
    "quadra": "Quadra Central",
    "esporte": "Futsal",
    "endereco": "Rua Rio Verde, 100",
    "bairro": "Centro",
    "data": "05/03/2030",
    "dia_semana": "terça-feira",
    "dia_semana_curto": "ter",
    "dia": "05",
    "mes_curto": "mar",
    "data_extensa": "Terça-feira, 5 de março",
    "inicio": "09:00",
    "fim": "10:00",
}


def _confirmacao(nome="Lucas Martins"):
    return renderizar(
        "confirmacao_agendamento",
        assunto="Esporte+ — Agendamento confirmado",
        preview="Quadra Central · Terça-feira, 5 de março, às 09:00.",
        nome=nome,
        agendamento=AGENDAMENTO,
    )


def test_confirmacao_tem_os_dados_da_reserva_nas_duas_versoes():
    email = _confirmacao()
    for versao in (email.texto, email.html):
        for trecho in (
            "Lucas Martins",
            "Quadra Central",
            "Futsal",
            "09:00 às 10:00",
            "Rua Rio Verde, 100 — Centro",
        ):
            assert trecho in versao, trecho
    assert "05/03/2030" in email.texto
    assert "Terça-feira, 5 de março" in email.html


def test_html_usa_o_layout_da_marca_com_logo_hospedado_no_front():
    email = _confirmacao()
    assert email.html.lstrip().startswith("<!doctype html>")
    assert f'src="{settings.FRONTEND_URL}/marca/logo-email.png"' in email.html
    assert 'alt="Esporte+"' in email.html
    assert "Secretaria Municipal de Esportes" in email.html


def test_texto_puro_nao_contem_html():
    email = _confirmacao()
    assert "<" not in email.texto
    assert email.texto.rstrip().endswith(settings.FRONTEND_URL)


def test_dados_do_usuario_sao_escapados_no_html():
    email = _confirmacao(nome='<script>alert("x")</script>')
    assert "<script>" not in email.html
    assert "&lt;script&gt;" in email.html


def test_variavel_faltando_no_contexto_e_erro_e_nao_texto_vazio():
    with pytest.raises(Exception, match="nome"):
        renderizar("confirmacao_agendamento", assunto="a", preview="p", agendamento=AGENDAMENTO)


def test_erro_ao_montar_o_email_nao_interrompe_quem_enviou(monkeypatch):
    from app.services import email_service

    registros = []
    monkeypatch.setattr(email_service, "renderizar", lambda *a, **k: 1 / 0)
    monkeypatch.setattr(
        email_service.EmailService,
        "_registrar",
        lambda self, para, assunto, evento, sucesso: registros.append((evento, sucesso)),
    )

    email_service.EmailService()._enviar_template(
        "a@b.com",
        "Assunto",
        "confirmacao_agendamento",
        evento="confirmacao_agendamento",
        preview="p",
    )

    assert registros == [("confirmacao_agendamento", False)]


# --- Todos os e-mails ---------------------------------------------------------

from scripts.previa_emails import EXEMPLOS  # noqa: E402

POR_TEMPLATE = {template: (assunto, contexto) for template, assunto, contexto in EXEMPLOS}


def _renderizar_exemplo(template):
    assunto, contexto = POR_TEMPLATE[template]
    return renderizar(template, assunto=assunto, **contexto)


@pytest.mark.parametrize("template", list(POR_TEMPLATE))
def test_todos_os_emails_tem_versao_html_e_texto_com_o_nome_do_destinatario(template):
    email = _renderizar_exemplo(template)
    nome = POR_TEMPLATE[template][1]["nome"]
    assert email.html.lstrip().startswith("<!doctype html>")
    assert f"<title>{POR_TEMPLATE[template][0]}</title>" in email.html
    assert nome in email.html
    assert nome in email.texto
    assert "<" not in email.texto


def test_recuperacao_tem_botao_com_o_link_e_o_prazo_de_validade():
    email = _renderizar_exemplo("recuperacao_senha")
    assert "padding:14px 28px" in email.html
    link = POR_TEMPLATE["recuperacao_senha"][1]["link"]
    assert f'<a href="{link}"' in email.html
    assert "Criar nova senha" in email.html
    assert link in email.texto
    assert "válido por 1 hora" in email.texto


@pytest.mark.parametrize("template", ["boas_vindas_pessoa", "boas_vindas_administrador"])
def test_boas_vindas_destaca_a_senha_e_leva_ao_login(template):
    email = _renderizar_exemplo(template)
    senha = POR_TEMPLATE[template][1]["senha"]
    assert senha in email.html
    assert f'href="{settings.FRONTEND_URL}/login"' in email.html
    # No texto, a senha fica sozinha numa linha recuada (formato lido nos testes de integração)
    assert f"\n    {senha}\n" in email.texto


def test_emails_de_aviso_nao_tem_botao():
    for template in (
        "confirmacao_agendamento",
        "cancelamento_agendamento",
        "remarcacao_agendamento",
        "confirmacao_renovacao",
        "lembrete_agendamento",
        "confirmacao_desativacao",
    ):
        # "padding:14px 28px" é exclusivo do componente botao() em _componentes.html
        assert "padding:14px 28px" not in _renderizar_exemplo(template).html, template


def test_cancelamento_nao_mostra_endereco_e_remarcacao_usa_novos_rotulos():
    cancelamento = _renderizar_exemplo("cancelamento_agendamento")
    assert "Rua Rio Verde" not in cancelamento.html
    assert "Endereço" not in cancelamento.texto
    remarcacao = _renderizar_exemplo("remarcacao_agendamento")
    assert "Nova data" in remarcacao.html and "Novo horário" in remarcacao.html
    assert "Nova data: 10/10/2026" in remarcacao.texto
