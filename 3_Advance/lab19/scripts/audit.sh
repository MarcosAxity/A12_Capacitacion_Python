#!/usr/bin/env bash
# ============================================================================
# audit.sh — Ejecuta la auditoría de dependencias del Módulo 19.
#
# Uso:
#   ./scripts/audit.sh
#
# Requiere tener activado el entorno virtual con requirements-dev.txt
# instalado (incluye pip-audit y safety).
# ============================================================================
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p audit-reports

echo "==> [1/2] pip-audit (contra requirements.txt, base OSV/PyPI)"
pip-audit -r requirements.txt -f json -o audit-reports/pip-audit-report.json
pip-audit -r requirements.txt

echo
echo "==> [2/2] safety (requiere cuenta/API key de safetycli.com; usar 'safety auth login')"
echo "    Si no hay credenciales configuradas, este paso fallará con un error"
echo "    de autenticación explícito — ver README, sección 'safety'."
safety check -r requirements.txt --output json > audit-reports/safety-report.json || \
    echo "safety check finalizó con hallazgos o error de auth (ver audit-reports/safety-report.json)"

echo
echo "Reportes generados en ./audit-reports/"
