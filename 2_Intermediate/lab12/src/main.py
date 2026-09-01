"""Demo ejecutable del módulo 12.

Uso:
    python -m src.main --repo memory
    python -m src.main --repo sql --db orders.db
"""

import argparse

from src.domain.policies import PercentageDiscount
from src.infrastructure.factory import build_order_service


def run(repo_kind: str, db_path: str) -> None:
    service = build_order_service(
        repo_kind=repo_kind,
        notifier_kind="console",
        discount_policy=PercentageDiscount(percentage=0.10),
        db_path=db_path,
    )

    print(f"\n== Usando repositorio: {repo_kind} ==")
    order = service.place_order(customer="ana@example.com", total=200.0)
    print(f"Pedido creado: {order}")

    order = service.apply_discount(order.id)
    print(f"Pedido con descuento (10%): {order}")

    service.notify_customer(order.id)

    print("Pedidos almacenados:")
    for o in service.list_orders():
        print(f"  - {o}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Demo módulo 12 - SOLID en Python")
    parser.add_argument(
        "--repo",
        choices=["memory", "sql"],
        default="memory",
        help="Implementación de repositorio a usar (puerto OrderRepository)",
    )
    parser.add_argument(
        "--db",
        default=":memory:",
        help="Ruta de la base SQLite (solo aplica con --repo sql)",
    )
    args = parser.parse_args()
    run(args.repo, args.db)
