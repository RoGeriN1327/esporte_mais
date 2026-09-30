#!/bin/sh
# Entrypoint do container backend: aplica as migrations e semeia o primeiro
# Gestor (idempotente) antes de subir a API. Assim um único `docker compose up`
# (ou o deploy) já deixa o sistema pronto para uso.
set -e

echo "[esporte+] alembic upgrade head"
alembic upgrade head

echo "[esporte+] seed do Gestor inicial (idempotente)"
python -m scripts.seed_gestor

echo "[esporte+] iniciando: $*"
exec "$@"
