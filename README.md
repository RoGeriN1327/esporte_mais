# Esporte+

Sistema web para agendamento e gerenciamento de quadras esportivas públicas da
Secretaria Municipal de Esportes de Rio Verde – GO.

| Parte    | Tecnologias                                                        |
|----------|--------------------------------------------------------------------|
| Backend  | Python 3.13, FastAPI, SQLAlchemy, Alembic, PostgreSQL 16, APScheduler |
| Frontend | React 18, Vite, React Router, TanStack Query, Tailwind CSS          |
| Infra    | Docker / Docker Compose (Postgres, Mailpit, backend, frontend)      |

---

## 1. Rodar localmente

Pré-requisito: Docker Desktop aberto.

```bash
docker compose up -d --build     # 1ª vez ou após mudar requirements/package.json
docker compose up -d             # próximas vezes
```

| Serviço                | URL                          |
|------------------------|------------------------------|
| Frontend               | http://localhost:5173        |
| API (Swagger)          | http://localhost:8000/docs   |
| Mailpit (e-mails)      | http://localhost:8025        |
| pgAdmin (opcional)     | http://localhost:5050 — `docker compose --profile tools up -d` |

Login inicial local: o Gestor é criado automaticamente com o e-mail e a senha
das variáveis `GESTOR_INICIAL_*` (valores de desenvolvimento em `.env.example`;
nunca use esses valores em produção).

Quadras de exemplo para testar: `docker compose exec backend python -m scripts.seed_quadras_dev`

Para mudar credenciais e segredos, copie `.env.example` para `.env` na raiz e
rode `docker compose up -d` de novo.

```bash
docker compose logs -f backend   # acompanhar logs da API
docker compose down              # parar (os dados do banco são mantidos)
docker compose down -v           # parar e APAGAR o banco
```

---

## 2. Estrutura do projeto

```
esporte_mais/
├── docker-compose.yml          ambiente de desenvolvimento completo
├── .env.example                variáveis do compose (copiar para .env)
│
├── backend/
│   ├── Dockerfile              imagem da API (produção por padrão)
│   ├── docker-entrypoint.sh    roda migrations + cria o 1º Gestor antes de subir a API
│   ├── requirements.txt        dependências de produção
│   ├── requirements-dev.txt    + testes e lint
│   ├── pyproject.toml          configuração do pytest, cobertura e Ruff
│   ├── alembic/versions/       migrations do banco (histórico de schema)
│   ├── scripts/                seed do Gestor inicial e quadras de exemplo
│   ├── tests/                  unitario/ e integracao/ (Postgres real)
│   └── app/
│       ├── main.py             cria a API, registra rotas e tratamento de erros
│       ├── exceptions.py       erros de negócio -> status HTTP
│       ├── core/               config, banco, segurança (JWT/bcrypt), permissões, jobs
│       ├── controllers/        rotas HTTP (uma por área)
│       ├── schemas/            formato/validação da entrada e saída (Pydantic)
│       ├── services/           REGRAS DE NEGÓCIO
│       ├── repositories/       consultas ao banco
│       ├── models/             tabelas (SQLAlchemy)
│       └── utils/              CPF e fuso horário
│
└── frontend/
    ├── Dockerfile              build de produção servido por nginx
    ├── Dockerfile.dev          Vite com hot-reload (usado pelo compose)
    ├── nginx.conf              SPA: toda rota cai no index.html
    └── src/
        ├── main.jsx            ponto de entrada
        ├── routes/             mapa de rotas + guardas de permissão
        ├── api/                chamadas HTTP (client.js cuida dos tokens)
        ├── contexts/           sessão do usuário logado (AuthContext)
        ├── components/         Layout e componentes reutilizáveis (ui.jsx)
        ├── features/           telas, agrupadas por área
        └── utils/              CPF e datas
```

### Caminho de uma requisição no backend

```
controllers/ -> schemas/ (valida) -> services/ (regras) -> repositories/ -> models/ -> PostgreSQL
```

Exemplo — "agendar horário": `controllers/agendamento_controller.py` →
`services/agendamento_service.py::criar` → `repositories/agendamento_repository.py`.

---

## 3. Variáveis de ambiente

A lista completa, com descrição de cada uma, está em `backend/app/core/config.py`.

### Backend (variáveis de ambiente do serviço)

| Variável        | Obrigatória | Valor em produção |
|-----------------|:-----------:|-------------------|
| `DATABASE_URL`  | sim | URL do Postgres. Pode colar como o provedor entrega (`postgres://...`): a API ajusta o driver sozinha. |
| `JWT_SECRET`    | sim | Segredo aleatório, **mínimo 32 caracteres**: `python -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `FRONTEND_URL`  | sim* | URL pública do frontend, ex.: `https://esportemais.vercel.app` (libera o CORS e monta os links dos e-mails). *O padrão é localhost, o que quebra o CORS em produção. |
| `MAIL_MODE`     | — | `smtp`, com `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_TLS=true` |
| `TIMEZONE`      | — | `America/Sao_Paulo` (padrão) |
| `DOCS_ENABLED`  | — | `false` — tira do ar `/docs`, `/redoc` e `/openapi.json` (padrão `true`, para o desenvolvimento) |
| `PORT`          | — | Definida pela própria hospedagem; local usa 8000 |
| `GESTOR_INICIAL_*` | só no 1º deploy | Ver "Primeiro Gestor em produção" abaixo |

### Frontend (variável de BUILD)

| Variável       | Obrigatória | Valor em produção |
|----------------|:-----------:|-------------------|
| `VITE_API_URL` | sim | URL pública da API, ex.: `https://esportemais-api.onrender.com` |

O Vite embute esse valor no JavaScript **durante o build**: configure-o como
variável de build da hospedagem (ou `--build-arg` no Docker) e refaça o build
sempre que mudar. Se estiver faltando, o `npm run build` falha de propósito.

### Primeiro Gestor em produção

O banco de produção começa vazio e só um Gestor cria administradores. Para não
deixar credenciais guardadas em lugar nenhum:

1. No 1º deploy, defina no painel da hospedagem `GESTOR_INICIAL_NOME`,
   `GESTOR_INICIAL_CPF` (válido), `GESTOR_INICIAL_EMAIL` e `GESTOR_INICIAL_SENHA`
   (forte, 8 a 72 caracteres).
2. Faça o deploy: o log deve mostrar `Gestor inicial criado (id=1, ...)`.
3. Entre no sistema e troque a senha em "Esqueci minha senha".
4. **Apague as quatro variáveis** do painel. Sem elas o seed não faz nada nas
   próximas subidas, e a senha inicial deixa de existir em qualquer lugar.

---

## 4. Testes e análise estática

Com os containers no ar:

```bash
docker compose exec backend pytest                 # 178 testes (unitários + integração)
docker compose exec backend pytest --cov=app       # com cobertura
docker compose exec backend ruff check app scripts tests alembic/env.py
docker compose exec backend ruff format --check app scripts tests alembic/env.py
docker compose exec frontend npm test              # 22 testes (Vitest)
docker compose exec frontend npm run lint          # ESLint
```

Os testes de integração usam o banco `esporte_mais_test`, criado e migrado
automaticamente — o banco de desenvolvimento não é tocado.

### GitHub Actions

| Workflow | Quando roda | O que faz |
|----------|-------------|-----------|
| `.github/workflows/ci.yml` | Todo pull request e todo push na `main` | Backend: Ruff + pytest (com PostgreSQL 16 no próprio job). Frontend: ESLint, Vitest e build. A ruleset da `main` exige os dois jobs verdes para o merge. |
| `.github/workflows/manter-api-acordada.yml` | A cada 10 min, das 6h às 23h50 (Brasília) | Chama `/health` da API para o Render (plano gratuito) não hibernar o serviço. Pode ser executado manualmente na aba **Actions**. |

---

## 5. Quando der erro — onde olhar

| Sintoma | Onde investigar |
|---------|-----------------|
| API não sobe | Log do backend. Mensagem `ValidationError ... Settings` = `DATABASE_URL`/`JWT_SECRET` faltando ou `JWT_SECRET` curto demais. |
| Não consigo logar no 1º deploy | Log do backend: procure `Gestor inicial criado` ou `Gestor inicial NÃO criado: <motivo>` (CPF inválido, senha curta...). |
| Erro em migration | `backend/alembic/versions/`; o entrypoint roda `alembic upgrade head` a cada subida. |
| Resposta 4xx com `{"detail": "..."}` | Regra de negócio: procure o texto da mensagem em `backend/app/services/`. |
| Resposta 422 | Validação de campo: veja o schema em `backend/app/schemas/`. |
| Resposta 401 / 403 | Token ou permissão: `backend/app/core/deps.py` e `core/security.py`. |
| Resposta 500 | Bug não tratado: o traceback aparece em `docker compose logs backend`. |
| Erro de CORS no navegador | `FRONTEND_URL` do backend diferente da URL em que o frontend está aberto (confira `https://` e o domínio exato). |
| Frontend chama a URL errada da API | `VITE_API_URL` do build; depois de corrigir, é preciso **refazer o build** do frontend. |
| Recarregar a página (F5) em `/admin` dá 404 | A hospedagem do frontend precisa redirecionar toda rota para `index.html` (já configurado em `frontend/nginx.conf` para Docker). |
| E-mail não chega | Tabela `notificacao` (coluna `sucesso`) e logs com "Falha ao enviar e-mail". |
| Agendamentos não mudam para "Concluído" / lembretes não saem | Jobs em `backend/app/core/scheduler.py`; confira `SCHEDULER_ENABLED` e os logs `esporte_mais.scheduler`. |
| Tela em branco / erro no frontend | Console do navegador (F12) e aba Network para ver a resposta da API. |
