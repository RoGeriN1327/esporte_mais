#!/bin/sh
# Entrypoint do container backend — decisão D13:
# Aplica migrations e semeia o primeiro Gestor (idempotente) antes de subir a API,
# Para que `docker compose up` deixe o sistema utilizável em uma única execução.
set -e

echo "[esporte+] alembic upgrade head"
alembic upgrade head

echo "[esporte+] seed do Gestor inicial (idempotente)"
python -m scripts.seed_gestor

echo "[esporte+] iniciando: $*"
exec "$@"
