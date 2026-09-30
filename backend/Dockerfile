# Imagem do backend Esporte+ (FastAPI + Uvicorn)
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependências primeiro (aproveita cache do Docker entre builds).
# Em dev o compose passa REQUIREMENTS=requirements-dev.txt (inclui testes e lint).
ARG REQUIREMENTS=requirements.txt
COPY requirements*.txt ./
RUN pip install --no-cache-dir -r ${REQUIREMENTS}

# Código da aplicação
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .
COPY scripts ./scripts
COPY docker-entrypoint.sh .
# Remove CRLF caso o checkout no Windows tenha convertido as quebras de linha
RUN sed -i 's/\r$//' docker-entrypoint.sh && chmod +x docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
# - PORT: plataformas como Render/Railway definem a porta por variável; local usa 8000.
# - --proxy-headers: atrás do proxy HTTPS da hospedagem, usa o IP real do cliente
#   (X-Forwarded-For). Sem isso o rate limit do login trataria todos os usuários
#   como um só IP.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
