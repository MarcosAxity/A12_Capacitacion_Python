#!/usr/bin/env python
"""Script de mantenimiento (click): elimina órdenes en un estado dado.

Usa click en vez de argparse porque, a diferencia de health_check.py, aquí
sí interesan cosas que click resuelve mejor con menos código: flags
booleanas (`--dry-run`), validación de tipos y mensajes de ayuda más ricos.
Sirve como comparación práctica frente a argparse y Typer.

Uso:
    python scripts/maintenance/cleanup_old_orders.py --dry-run
    python scripts/maintenance/cleanup_old_orders.py --status cancelled
    ORDERS_API_BASE_URL=http://127.0.0.1:8000 python scripts/maintenance/cleanup_old_orders.py
"""
from __future__ import annotations

import os

import click
import httpx


@click.command()
@click.option(
    "--url",
    default=lambda: os.environ.get("ORDERS_API_BASE_URL", "http://127.0.0.1:8000"),
    show_default="ORDERS_API_BASE_URL o http://127.0.0.1:8000",
    help="URL base de la API",
)
@click.option("--status", default="cancelled", show_default=True, help="Estado de las órdenes a eliminar")
@click.option("--dry-run", is_flag=True, help="Solo muestra qué se borraría, sin borrar nada")
def cleanup(url: str, status: str, dry_run: bool) -> None:
    """Elimina todas las órdenes que tengan el ESTADO indicado (por defecto: cancelled)."""
    with httpx.Client(base_url=url, timeout=10) as client:
        response = client.get("/orders", params={"status": status})
        response.raise_for_status()
        orders = response.json()

        if not orders:
            click.echo(f"No hay órdenes con estado '{status}'.")
            return

        for order in orders:
            if dry_run:
                click.echo(f"[dry-run] Se eliminaría la orden {order['id']} (cliente: {order['customer']})")
                continue
            delete_response = client.delete(f"/orders/{order['id']}")
            delete_response.raise_for_status()
            click.echo(f"Orden {order['id']} eliminada.")


if __name__ == "__main__":
    cleanup()
