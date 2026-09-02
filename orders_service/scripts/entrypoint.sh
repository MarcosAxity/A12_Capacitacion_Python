#!/bin/bash
# Entrypoint del contenedor: aplica migraciones Alembic pendientes y luego
# arranca el proceso principal (uvicorn, o cualquier comando pasado como CMD).
set -euo pipefail

echo "[entrypoint] Aplicando migraciones de base de datos..."
python -m alembic -c alembic.ini upgrade head

echo "[entrypoint] Migraciones aplicadas. Iniciando: $*"
exec "$@"
