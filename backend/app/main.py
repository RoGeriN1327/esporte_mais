"""Ponto de entrada da API Esporte+ (FastAPI).

Organização em camadas (cada requisição percorre nesta ordem):
    controllers/   rotas HTTP: validam a entrada (schemas) e chamam um service
    services/      regras de negócio; lançam exceções de app.exceptions
    repositories/  consultas e gravações no banco (SQLAlchemy)
    models/        tabelas do banco

Erros de negócio (ErroDeDominio) viram respostas JSON {"detail": "..."} com o
status HTTP definido em cada exceção — ver tratar_erro_de_dominio abaixo.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.controllers.admin_controller import router as admin_router
from app.controllers.agendamento_admin_controller import router as agendamento_admin_router
from app.controllers.agendamento_controller import router as agendamento_router
from app.controllers.auth_controller import router as auth_router
from app.controllers.configuracao_controller import router as configuracao_router
from app.controllers.quadra_admin_controller import router as quadra_admin_router
from app.controllers.quadra_controller import router as quadra_router
from app.controllers.usuario_controller import router as usuario_router
from app.core.config import settings
from app.core.rate_limit import limiter
from app.core.scheduler import criar_scheduler
from app.exceptions import ErroDeDominio


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Liga os jobs periódicos junto com a API e os desliga ao encerrar."""
    scheduler = criar_scheduler() if settings.SCHEDULER_ENABLED else None
    if scheduler is not None:
        scheduler.start()
    yield
    if scheduler is not None:
        scheduler.shutdown(wait=False)


app = FastAPI(
    title="Esporte+ API",
    description="API do sistema de agendamento de quadras esportivas públicas da "
    "Secretaria Municipal de Esportes de Rio Verde - GO. "
    "Módulos: Autenticação e Gestão de Usuários, "
    "Agendamentos e Gestão de Quadras/Painel.",
    version="0.3.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DOCS_ENABLED else None,
    redoc_url="/redoc" if settings.DOCS_ENABLED else None,
    openapi_url="/openapi.json" if settings.DOCS_ENABLED else None,
)

app.state.limiter = limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def cabecalhos_de_seguranca(request: Request, call_next):
    """Cabeçalhos de segurança em todas as respostas da API."""
    resposta = await call_next(request)
    resposta.headers.setdefault("X-Content-Type-Options", "nosniff")
    resposta.headers.setdefault("X-Frame-Options", "DENY")
    resposta.headers.setdefault("Referrer-Policy", "no-referrer")
    return resposta


@app.exception_handler(ErroDeDominio)
async def tratar_erro_de_dominio(request: Request, exc: ErroDeDominio) -> JSONResponse:
    headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
    return JSONResponse(
        status_code=exc.status_code, content={"detail": exc.mensagem}, headers=headers
    )


@app.exception_handler(RateLimitExceeded)
async def tratar_rate_limit(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": "Muitas requisições. Aguarde um instante e tente novamente."},
    )


# Área do cidadão e autenticação
app.include_router(auth_router)
app.include_router(usuario_router)
app.include_router(quadra_router)
app.include_router(agendamento_router)

# Área administrativa (Gestor e Operador)
app.include_router(admin_router)
app.include_router(quadra_admin_router)
app.include_router(agendamento_admin_router)
app.include_router(configuracao_router)


# HEAD além de GET: monitores de disponibilidade (ex.: UptimeRobot) pingam com HEAD.
# Fica fora da documentação para não duplicar a operação do GET.
@app.head("/health", include_in_schema=False)
@app.get("/health", tags=["Infraestrutura"], summary="Verificação de saúde da API")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
