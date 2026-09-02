"""CLI de Orders construido con Typer.

Comandos:
    orders-cli list                       -> lista órdenes (opcionalmente por estado)
    orders-cli create -c ... -i ... -t ... -> crea una orden
    orders-cli delete <id>                 -> elimina una orden
    orders-cli config                      -> muestra la configuración activa

La configuración (URL de la API, timeout, token) se toma de variables de
entorno (ver orders_cli/config.py), no de argumentos obligatorios, para
que el mismo binario funcione igual en local, CI y producción sin tocar
código.
"""
from __future__ import annotations

from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table

from .client import OrdersClient
from .config import get_settings

app = typer.Typer(add_completion=False, no_args_is_help=True, help="CLI para gestionar Orders consumiendo la API REST.")
console = Console()


@app.command("list")
def list_orders(
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filtrar por estado (pending, cancelled, ...)"),
) -> None:
    """Lista las órdenes registradas en la API."""
    with OrdersClient() as client:
        try:
            orders = client.list_orders(status=status)
        except Exception as exc:  # httpx.HTTPError y variantes
            console.print(f"[bold red]Error al consultar la API:[/bold red] {exc}")
            raise typer.Exit(code=1)

    if not orders:
        console.print("[yellow]No hay órdenes registradas.[/yellow]")
        raise typer.Exit(code=0)

    table = Table(title="Orders")
    table.add_column("ID", overflow="fold")
    table.add_column("Cliente")
    table.add_column("Items")
    table.add_column("Total", justify="right")
    table.add_column("Estado")
    for order in orders:
        table.add_row(
            order["id"],
            order["customer"],
            ", ".join(order["items"]),
            f'{order["total"]:.2f}',
            order["status"],
        )
    console.print(table)


@app.command("create")
def create_order(
    customer: str = typer.Option(..., "--customer", "-c", help="Nombre del cliente"),
    item: List[str] = typer.Option(..., "--item", "-i", help="Item de la orden (repetir la opción por cada item)"),
    total: float = typer.Option(..., "--total", "-t", help="Total de la orden"),
) -> None:
    """Crea una nueva orden en la API."""
    with OrdersClient() as client:
        try:
            order = client.create_order(customer=customer, items=item, total=total)
        except Exception as exc:
            console.print(f"[bold red]Error al crear la orden:[/bold red] {exc}")
            raise typer.Exit(code=1)
    console.print(f"[bold green]Orden creada:[/bold green] {order['id']}")


@app.command("delete")
def delete_order(
    order_id: str = typer.Argument(..., help="ID de la orden a eliminar"),
    yes: bool = typer.Option(False, "--yes", "-y", help="No pedir confirmación interactiva"),
) -> None:
    """Elimina una orden existente por ID."""
    if not yes and not typer.confirm(f"¿Confirmas borrar la orden {order_id}?"):
        console.print("Operación cancelada.")
        raise typer.Exit(code=0)

    with OrdersClient() as client:
        try:
            ok = client.delete_order(order_id)
        except Exception as exc:
            console.print(f"[bold red]Error al borrar la orden:[/bold red] {exc}")
            raise typer.Exit(code=1)

    if ok:
        console.print(f"[bold green]Orden {order_id} eliminada.[/bold green]")
    else:
        console.print(f"[bold red]No se pudo eliminar la orden {order_id}.[/bold red]")
        raise typer.Exit(code=1)


@app.command("config")
def show_config() -> None:
    """Muestra la configuración activa (proveniente de variables de entorno)."""
    settings = get_settings()
    console.print(f"API base URL : {settings.api_base_url}")
    console.print(f"Timeout      : {settings.api_timeout}s")
    console.print(f"Token        : {'configurado' if settings.api_token else 'no configurado'}")


def main() -> None:
    """Entry point registrado en pyproject.toml como `orders-cli`."""
    app()


if __name__ == "__main__":
    main()
