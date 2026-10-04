"""Gera a pré-visualização dos e-mails com dados de exemplo (sem enviar nada).

Uso (com os containers no ar):
    docker compose exec backend python -m scripts.previa_emails

Saída em backend/relatorios/emails/ (ignorada pelo git): um .html e um .txt por e-mail
e um index.html para navegar entre eles no navegador.
"""

from html import escape
from pathlib import Path

from app.emails.renderizador import renderizar

SAIDA = Path(__file__).resolve().parents[1] / "relatorios" / "emails"

AGENDAMENTO_EXEMPLO = {
    "quadra": "Ginásio Municipal Odilon Rezende",
    "esporte": "Futsal",
    "endereco": "Rua Rio Verde, 100",
    "bairro": "Centro",
    "data": "10/10/2026",
    "dia_semana": "sábado",
    "dia_semana_curto": "sáb",
    "dia": "10",
    "mes_curto": "out",
    "data_extensa": "Sábado, 10 de outubro",
    "inicio": "19:00",
    "fim": "20:00",
}

# Um item por e-mail: (template, assunto, contexto). Também usado pelos testes de renderização.
_PREVIEW_AGENDAMENTO = "Ginásio Municipal Odilon Rezende · Sábado, 10 de outubro, às 19:00."
_LINK_RECUPERACAO = "https://esporte-mais-rv.vercel.app/redefinir-senha?token=exemplo-de-token"

EXEMPLOS = [
    (
        "confirmacao_agendamento",
        "Esporte+ — Agendamento confirmado",
        {
            "preview": _PREVIEW_AGENDAMENTO,
            "nome": "Marina Souza",
            "agendamento": AGENDAMENTO_EXEMPLO,
        },
    ),
    (
        "cancelamento_agendamento",
        "Esporte+ — Agendamento cancelado",
        {
            "preview": _PREVIEW_AGENDAMENTO,
            "nome": "Marina Souza",
            "agendamento": AGENDAMENTO_EXEMPLO,
        },
    ),
    (
        "remarcacao_agendamento",
        "Esporte+ — Agendamento remarcado",
        {
            "preview": _PREVIEW_AGENDAMENTO,
            "nome": "Marina Souza",
            "agendamento": AGENDAMENTO_EXEMPLO,
        },
    ),
    (
        "confirmacao_renovacao",
        "Esporte+ — Renovação confirmada",
        {
            "preview": _PREVIEW_AGENDAMENTO,
            "nome": "Marina Souza",
            "agendamento": AGENDAMENTO_EXEMPLO,
        },
    ),
    (
        "lembrete_agendamento",
        "Esporte+ — Lembrete de agendamento",
        {
            "preview": _PREVIEW_AGENDAMENTO,
            "nome": "Marina Souza",
            "agendamento": AGENDAMENTO_EXEMPLO,
        },
    ),
    (
        "recuperacao_senha",
        "Esporte+ — Redefinição de senha",
        {
            "preview": "Use o link para criar uma nova senha.",
            "nome": "Marina Souza",
            "link": _LINK_RECUPERACAO,
        },
    ),
    (
        "boas_vindas_pessoa",
        "Esporte+ — Bem-vindo(a)! Sua conta foi criada",
        {
            "preview": "Sua conta foi criada pela Secretaria de Esportes.",
            "nome": "Marina Souza",
            "email": "marina.souza@exemplo.com.br",
            "senha": "Kp7#vR2mQx",
        },
    ),
    (
        "boas_vindas_administrador",
        "Esporte+ — Bem-vindo(a) à equipe administrativa",
        {
            "preview": "Sua conta de Operador foi criada.",
            "nome": "Carlos Pereira",
            "email": "carlos.pereira@rioverde.go.gov.br",
            "perfil": "Operador",
            "senha": "Tq9!wL4zNb",
        },
    ),
    (
        "confirmacao_desativacao",
        "Esporte+ — Confirmação de desativação de conta",
        {"preview": "Sua conta no Esporte+ foi desativada.", "nome": "Marina Souza"},
    ),
]


def main() -> None:
    SAIDA.mkdir(parents=True, exist_ok=True)
    itens = []
    for template, assunto, contexto in EXEMPLOS:
        email = renderizar(template, assunto=assunto, **contexto)
        (SAIDA / f"{template}.html").write_text(email.html, encoding="utf-8")
        (SAIDA / f"{template}.txt").write_text(email.texto, encoding="utf-8")
        itens.append(
            f'<li><a href="{template}.html">{escape(assunto)}</a>'
            f' · <a href="{template}.txt">texto puro</a></li>'
        )
    (SAIDA / "index.html").write_text(
        '<!doctype html><meta charset="utf-8"><title>Prévia dos e-mails — Esporte+</title>'
        '<body style="font-family:sans-serif;padding:24px"><h1>Prévia dos e-mails</h1>'
        f"<ul>{''.join(itens)}</ul></body>",
        encoding="utf-8",
    )
    print(f"{len(itens)} e-mail(s) gerado(s) em {SAIDA}")


if __name__ == "__main__":
    main()
