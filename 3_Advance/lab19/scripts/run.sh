#!/usr/bin/env bash
# ============================================================================
# run.sh — Levanta la API localmente (fuera de Docker) para desarrollo.
# ============================================================================
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
    echo "No existe .env — copiando desde .env.example"
    cp .env.example .env
    echo "Edita .env con tus valores reales antes de usar en un entorno real."
fi

uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
