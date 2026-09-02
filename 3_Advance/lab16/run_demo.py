"""Demo end-to-end del módulo Orders reestructurado a Clean Architecture.

Ejecutar con:  python run_demo.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from orders.interfaces.cli.main import build_controller  # noqa: E402


def main() -> None:
    controller = build_controller()

    print("== 1) Creando una orden válida ==")
    result = controller.create_order(
        {
            "customer_id": "cust-001",
            "items": [
                {"product_id": "SKU-1", "quantity": 2, "unit_price": "19.99"},
                {"product_id": "SKU-2", "quantity": 1, "unit_price": "5.50"},
            ],
        }
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    order_id = result["id"]

    print("\n== 2) Consultando la orden recién creada ==")
    print(json.dumps(controller.get_order(order_id), indent=2, ensure_ascii=False))

    print("\n== 3) Intentando crear una orden vacía (regla de negocio del dominio) ==")
    print(
        json.dumps(
            controller.create_order({"customer_id": "cust-002", "items": []}),
            indent=2,
            ensure_ascii=False,
        )
    )

    print("\n== 4) Consultando una orden inexistente ==")
    print(json.dumps(controller.get_order("id-que-no-existe"), indent=2, ensure_ascii=False))

    print("\n== 5) Listando todas las órdenes almacenadas ==")
    print(json.dumps(controller.list_orders(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
