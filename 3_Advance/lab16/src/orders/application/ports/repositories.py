"""Puertos (interfaces) de persistencia — también llamados Gateways.

Definen QUÉ necesita la aplicación de la persistencia, nunca CÓMO se
implementa. La capa de aplicación depende de esta abstracción; los
adaptadores concretos (infraestructura) la implementan. Esto es la
"regla de dependencia" en acción: las flechas de dependencia siempre
apuntan hacia el dominio/aplicación, nunca al revés.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Optional
from orders.domain.entities import Order


class OrderRepository(ABC):
    @abstractmethod
    def add(self, order: Order) -> None:
        ...

    @abstractmethod
    def get(self, order_id: str) -> Optional[Order]:
        ...

    @abstractmethod
    def list(self) -> List[Order]:
        ...
