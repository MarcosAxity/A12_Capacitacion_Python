#!/usr/bin/env python
"""Script de mantenimiento (argparse): verifica que la API de Orders esté viva.

Pensado para ejecutarse desde cron / un pipeline de CI/CD como chequeo de
salud. Usa argparse porque es un script pequeño, de un solo propósito, sin
subcomandos: para eso argparse (stdlib, sin dependencias) es suficiente.

Uso:
    python scripts/maintenance/health_check.py
    python scripts/maintenance/health_check.py --url http://127.0.0.1:8000 --timeout 3

También respeta las variables de entorno ORDERS_API_BASE_URL /
ORDERS_API_TIMEOUT como valores por defecto, igual que el CLI Typer.
"""
from __future__ import annotations

import argparse
import os
import sys

import httpx


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verifica que la API de Orders esté disponible.")
    parser.add_argument(
        "--url",
        default=os.environ.get("ORDERS_API_BASE_URL", "http://127.0.0.1:8000"),
        help="URL base de la API (default: %(default)s o ORDERS_API_BASE_URL)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=float(os.environ.get("ORDERS_API_TIMEOUT", "5")),
        help="Timeout en segundos (default: %(default)s)",
    )
    return parser.parse_args(argv)


def run_health_check(url: str, timeout: float) -> int:
    try:
        response = httpx.get(f"{url}/health", timeout=timeout)
        response.raise_for_status()
        print(f"OK: API disponible en {url} -> {response.json()}")
        return 0
    except Exception as exc:
        print(f"ERROR: API no disponible en {url}: {exc}", file=sys.stderr)
        return 1


def main(argv=None) -> None:
    args = parse_args(argv)
    sys.exit(run_health_check(args.url, args.timeout))


if __name__ == "__main__":
    main()
