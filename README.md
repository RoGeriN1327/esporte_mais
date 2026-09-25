# Esporte+

Sistema web para agendamento e gerenciamento de quadras esportivas públicas da
Secretaria Municipal de Esportes de Rio Verde – GO (TFC de Engenharia de Software).

Documentação do projeto em `docs/`: análise do DERS, decisões técnicas,
arquitetura do frontend e progresso por módulo.

## Subir tudo com Docker

Pré-requisito: Docker Desktop rodando.

```
docker compose up -d --build
```

Serviços disponíveis:

| Serviço  | URL                          |
|----------|------------------------------|
| Frontend | http://localhost:5173        |
| Backend  | http://localhost:8000/docs   |
| Mailpit  | http://localhost:8025        |

Login inicial (Gestor semeado automaticamente):

- E-mail: `gestor@esportemais.local`
- Senha:  `Admin@2026`

Para trocar credenciais/segredos, copie `.env.example` para `.env` na raiz e
ajuste — o compose faz `up --build` para reaplicar as variáveis.

Outros comandos úteis:

```
docker compose logs -f backend    # acompanhar logs
docker compose down               # derrubar (volume do Postgres é preservado)
docker compose down -v            # derrubar e apagar o banco
```
