"""Adaptador de persistencia en SQL (SQLite vía stdlib, sin dependencias
externas).

Implementa el MISMO puerto `OrderRepository` que la versión en memoria.
Para respetar LSP, replica exactamente el mismo comportamiento
observable (qué devuelve `get` cuando no existe, qué excepción lanza
`update` cuando el pedido no existe, etc.), de modo que sea
intercambiable con `InMemoryOrderRepository` sin sorpresas para quien
consume el puerto (`OrderService`).
"""

import sqlite3
from typing import List, Optional

from src.domain.models import Order, OrderStatus


class SqlOrderRepository:
    def __init__(self, db_path: str = ":memory:") -> None:
        self._conn = sqlite3.connect(db_path)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                customer TEXT NOT NULL,
                total REAL NOT NULL,
                status TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def add(self, order: Order) -> None:
        self._conn.execute(
            "INSERT INTO orders (id, customer, total, status) VALUES (?, ?, ?, ?)",
            (order.id, order.customer, order.total, order.status.value),
        )
        self._conn.commit()

    def get(self, order_id: str) -> Optional[Order]:
        row = self._conn.execute(
            "SELECT id, customer, total, status FROM orders WHERE id = ?",
            (order_id,),
        ).fetchone()
        if row is None:
            return None
        return self._row_to_order(row)

    def list_all(self) -> List[Order]:
        rows = self._conn.execute(
            "SELECT id, customer, total, status FROM orders"
        ).fetchall()
        return [self._row_to_order(row) for row in rows]

    def update(self, order: Order) -> None:
        cursor = self._conn.execute(
            "UPDATE orders SET customer = ?, total = ?, status = ? WHERE id = ?",
            (order.customer, order.total, order.status.value, order.id),
        )
        self._conn.commit()
        if cursor.rowcount == 0:
            raise KeyError(f"No se puede actualizar un pedido inexistente: {order.id}")

    @staticmethod
    def _row_to_order(row) -> Order:
        order_id, customer, total, status = row
        order = Order(customer=customer, total=total, id=order_id)
        order.status = OrderStatus(status)
        return order

    def close(self) -> None:
        self._conn.close()
