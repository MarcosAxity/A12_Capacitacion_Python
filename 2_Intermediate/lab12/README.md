# Módulo 12 · Principios SOLID aplicados en Python

Proyecto de ejemplo (dominio "gestión de pedidos") que aplica los cinco
principios **SOLID** de forma *pythonic*, usando `typing.Protocol` para
inversión de dependencias, un patrón *factory/provider* como
composition root, y una suite de tests que **verifica LSP** ejecutando
el mismo contrato contra dos implementaciones distintas de un mismo
puerto.

## 1. Objetivos cubiertos

- Aplicar SOLID a servicios y dominio (`OrderService` + puertos).
- Reducir acoplamiento (dominio no conoce SQL, consola, etc.) y
  mejorar extensibilidad (nuevas políticas / adaptadores sin tocar
  código existente).

## 2. Estructura del proyecto

```
solid_module12/
├── README.md
├── requirements.txt
├── src/
│   ├── domain/                 # Núcleo de negocio (no depende de nada externo)
│   │   ├── models.py            # Entidad Order (SRP)
│   │   ├── ports.py             # Protocols: OrderRepository, Notifier, DiscountPolicy (DIP + ISP)
│   │   ├── policies.py          # Estrategias de descuento (OCP)
│   │   └── services.py          # OrderService: orquesta el caso de uso (SRP + DIP)
│   ├── infrastructure/          # Adaptadores concretos (dependen del dominio, no al revés)
│   │   ├── memory_repository.py # OrderRepository en memoria
│   │   ├── sql_repository.py    # OrderRepository en SQLite
│   │   ├── notifiers.py         # Notifier: consola / email / sms (ISP)
│   │   └── factory.py           # Provider / composition root (DIP)
│   └── main.py                  # Demo ejecutable por CLI
└── tests/
    ├── conftest.py
    ├── test_lsp_contract.py     # ⭐ Verificación de LSP (memoria vs SQL)
    ├── test_service_srp.py      # Testabilidad de OrderService vía DIP
    ├── test_ocp_policies.py     # Extensión de políticas sin modificar código (OCP)
    └── test_isp_notifiers.py    # Adaptadores con contrato mínimo (ISP)
```

## 3. Cómo se aplicó cada principio (y dónde mirarlo)

| Principio | Dónde se ve | Idea clave |
|---|---|---|
| **SRP** | `models.py`, `services.py` | `Order` solo modela datos; `OrderService` solo orquesta el caso de uso (no persiste, no notifica "a mano", no calcula descuentos por sí mismo). Cada responsabilidad vive en su propia clase. |
| **OCP** | `policies.py` | `DiscountPolicy` es un `Protocol`. Se agregó `ThresholdDiscount` como ejemplo de extensión: **no se modificó** ni `NoDiscount`, ni `PercentageDiscount`, ni `OrderService`. |
| **LSP** | `infrastructure/memory_repository.py` + `sql_repository.py` + `tests/test_lsp_contract.py` | Ambos repos cumplen el mismo contrato observable: mismos valores de retorno, mismas excepciones ante los mismos errores. La suite de tests corre parametrizada contra ambos para comprobarlo automáticamente. |
| **ISP** | `ports.py`, `notifiers.py` | En vez de una interfaz gigante, hay Protocols chicos y enfocados (`Notifier` solo tiene `send`). Ningún adaptador se ve forzado a implementar métodos que no usa. |
| **DIP** | `services.py`, `factory.py` | `OrderService` depende de **abstracciones** (`Protocol`s), no de implementaciones. `factory.py` es el único módulo que conoce clases concretas y las conecta (patrón *provider*/composition root). |

### Inversión de dependencias con `Protocol`

`typing.Protocol` permite *structural typing*: una clase "implementa"
un puerto con solo tener los métodos correctos, sin heredar
explícitamente de nada (duck typing verificable estáticamente con
`mypy`). Esto evita jerarquías de herencia artificiales y hace que
`InMemoryOrderRepository` y `SqlOrderRepository` sean intercambiables
para `OrderService` sin acoplarse entre sí.

### Factory / provider pattern

`src/infrastructure/factory.py` centraliza la decisión de **qué
implementación concreta usar** (`repository_provider`,
`notifier_provider`, `build_order_service`). Es el único lugar del
proyecto que importa clases concretas de infraestructura; el dominio
nunca lo hace. Cambiar de memoria a SQL es una decisión de
configuración (un string `"memory"`/`"sql"`), no un cambio de código
en `services.py`.

### Acoplamiento, cohesión y testabilidad

- **Cohesión alta**: cada archivo tiene una sola razón de ser
  (modelo, puerto, política, servicio, adaptador).
- **Acoplamiento bajo**: `domain/` no importa nada de
  `infrastructure/`; la flecha de dependencia apunta siempre hacia el
  dominio.
- **Testabilidad**: gracias a DIP, `OrderService` se testea con un
  repositorio en memoria y un notifier de consola —sin mocks
  complejos, sin base de datos real— en milisegundos
  (`tests/test_service_srp.py`).

## 4. Laboratorio: refactor a puerto + verificación LSP

El laboratorio pedido está resuelto así:

1. **Refactor de servicio para depender de un puerto (`Protocol`)**:
   `OrderService` (en `src/domain/services.py`) recibe
   `OrderRepository`, `Notifier` y `DiscountPolicy` por constructor;
   ninguno es una clase concreta, los tres son `Protocol`.
2. **Implementaciones memoria/SQL**: `InMemoryOrderRepository`
   (`src/infrastructure/memory_repository.py`) y `SqlOrderRepository`
   (`src/infrastructure/sql_repository.py`, usa `sqlite3` de la
   librería estándar, sin dependencias extra).
3. **Verificación de LSP**: `tests/test_lsp_contract.py` define una
   suite `TestOrderRepositoryContract` con un fixture parametrizado
   (`params=["memory", "sql"]`). Las **mismas 5 pruebas** corren para
   ambas implementaciones (10 ejecuciones en total), comprobando que
   son sustituibles sin cambiar el comportamiento esperado por quien
   consume el puerto.

## 5. Cómo ejecutar el proyecto

### Requisitos

- Python 3.10 o superior (se usa la sintaxis `X | None` de tipos).
- No requiere base de datos externa: SQLite viene en la librería
  estándar de Python.

### 5.1 Instalación

Desde la carpeta raíz del proyecto (`solid_module12/`):

```bash
python -m venv .venv
source .venv/bin/activate        # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 5.2 Ejecutar la demo

```bash
# Usando el repositorio en memoria
python -m src.main --repo memory

# Usando el repositorio SQL (SQLite en memoria por defecto)
python -m src.main --repo sql

# Usando SQLite persistente en un archivo
python -m src.main --repo sql --db orders.db
```

Cada ejecución: crea un pedido, le aplica un 10% de descuento,
notifica al cliente por consola y lista los pedidos guardados. El
resultado es **idéntico** en forma y comportamiento sin importar el
`--repo` elegido, lo cual es la prueba "en vivo" de LSP y DIP.

**Salida**
```bash
❯ python -m src.main --repo memory

== Usando repositorio: memory ==
Pedido creado: Order(customer='ana@example.com', total=200.0, id='c33967aa-a7ab-4e54-9932-d39efb134b79', status=<OrderStatus.CREATED: 'CREATED'>)
Pedido con descuento (10%): Order(customer='ana@example.com', total=180.0, id='c33967aa-a7ab-4e54-9932-d39efb134b79', status=<OrderStatus.DISCOUNTED: 'DISCOUNTED'>)
[console] Para ana@example.com: Tu pedido c33967aa-a7ab-4e54-9932-d39efb134b79 por 180.0 fue procesado.
Pedidos almacenados:
  - Order(customer='ana@example.com', total=180.0, id='c33967aa-a7ab-4e54-9932-d39efb134b79', status=<OrderStatus.NOTIFIED: 'NOTIFIED'>)
```


### 5.3 Ejecutar los tests

Desde la raíz del proyecto:

```bash
pytest -v
```

Esto corre las 22 pruebas del proyecto, incluyendo la suite de
contrato LSP parametrizada. Para correr solo esa suite:

```bash
pytest tests/test_lsp_contract.py -v
```

Salida esperada (resumen):

```
22 passed
```

### 5.4 Explorar la extensibilidad (opcional)

Para comprobar OCP en la práctica, se puede usar cualquier política de
descuento sin tocar `OrderService`:

```python
from src.domain.policies import ThresholdDiscount
from src.infrastructure.factory import build_order_service

service = build_order_service(
    repo_kind="memory",
    notifier_kind="console",
    discount_policy=ThresholdDiscount(threshold=100, percentage=0.15),
)
order = service.place_order(customer="luis@example.com", total=150.0)
service.apply_discount(order.id)
```

## 6. Notas de diseño adicionales

- Se evitó `abc.ABC` a propósito para mostrar la vía "pythonic" de
  DIP: contratos estructurales (`Protocol`) en vez de herencia
  obligatoria.
- El manejo de errores es parte del contrato: ambas implementaciones
  de `OrderRepository` lanzan `KeyError` ante un `update` sobre un id
  inexistente, precisamente para no violar LSP.
- `factory.py` es el único punto de "cableado"; si se quisiera
  cambiar a un contenedor de inyección de dependencias más
  sofisticado (por ejemplo `dependency-injector`), solo se tocaría
  ese archivo.
