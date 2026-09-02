# Módulo 16 — Arquitectura Limpia: reestructuración de `Orders`

Este repositorio reestructura un servicio de **Órdenes (Orders)** aplicando
**Clean Architecture**, con **Unit of Work**, **eventos de dominio** y
**Presenters**. Está escrito en Python puro (sin frameworks), para que las
reglas de dependencia queden lo más visibles posible.

---

## 1. Contenidos clave: qué se está revisando y dónde se ve en el código

### 1.1 Entidades, casos de uso, controladores/presenters/gateways

Este es el famoso "diagrama de círculos" de Robert C. Martin, y cada círculo
tiene su carpeta:

| Círculo (Clean Arch.) | Carpeta | Responsabilidad |
|---|---|---|
| **Entidades** | `src/orders/domain/` | Reglas de negocio puras: `Order`, `OrderItem`, `Money`, `OrderStatus`, excepciones de negocio y eventos de dominio. No importan nada de fuera de `domain`. |
| **Casos de uso** | `src/orders/application/use_cases/` | Orquestan el flujo: `CreateOrderUseCase`, `GetOrderUseCase`, `ListOrdersUseCase`. Sólo dependen de **puertos** (`application/ports`), nunca de infraestructura concreta. |
| **Gateways (puertos)** | `src/orders/application/ports/` | Interfaces abstractas: `OrderRepository`, `UnitOfWork`, `EventBus`. Son "enchufes" que la aplicación define y que infraestructura implementa. |
| **Adaptadores de infraestructura** | `src/orders/infrastructure/` | Implementaciones concretas de los puertos: `InMemoryOrderRepository`, `InMemoryUnitOfWork`, `InMemoryEventBus`. Se pueden reemplazar por SQL/Mongo/Kafka sin tocar el resto. |
| **Controladores** | `src/orders/interfaces/controllers/order_controller.py` | Reciben entrada "cruda" (un `dict`, que en producción vendría de HTTP/CLI), la traducen a un DTO de aplicación y llaman al caso de uso. No tienen reglas de negocio. |
| **Presenters** | `src/orders/interfaces/presenters/order_presenter.py` | Toman la salida del caso de uso (un DTO) y la formatean para el canal de salida (aquí, `dict` listo para JSON/consola). Separan "qué pasó" de "cómo se muestra". |
| **Composition root** | `src/orders/interfaces/cli/main.py` (`build_controller`) | El único lugar que conoce todas las capas a la vez y las conecta ("inyección de dependencias" manual). |

### 1.2 Reglas de dependencia y separación de capas

La regla de dependencia dice: **las flechas de código siempre apuntan hacia
adentro** (hacia el dominio). Una capa interna nunca importa una externa.

```
 interfaces (controllers/presenters/cli)
        │  depende de
        ▼
 application (use cases, DTOs, ports)
        │  depende de
        ▼
 domain (entities, value objects, events)

 infrastructure (repos/UoW/event bus concretos)
        │  implementa
        ▼
 application.ports   (¡infraestructura apunta HACIA la aplicación,
                       no al revés!)
```

Cómo se verifica en este repo:
- `domain/` **no importa nada** de `application` ni de `infrastructure`
  (revísalo: sus `import` sólo traen otros módulos de `domain`).
- `application/use_cases/*` sólo importa `domain` y `application.ports`
  (interfaces), nunca `infrastructure`.
- `infrastructure/*` es la única capa que importa `application.ports` **para
  implementarlos** (`InMemoryOrderRepository(OrderRepository)`, etc.).
- Quien conecta infraestructura concreta con casos de uso es únicamente
  `interfaces/cli/main.py` (composition root).

Gracias a esto, los casos de uso y las entidades se prueban con Python puro,
sin bases de datos ni mocks complejos (ver `tests/`).

### 1.3 Unit of Work y eventos de dominio

- **Unit of Work** (`application/ports/unit_of_work.py` +
  `infrastructure/persistence/in_memory_unit_of_work.py`): agrupa las
  operaciones sobre el repositorio dentro de una sola transacción lógica
  (`with uow as u: ... u.commit()`). Si no se llama a `commit()`, no se
  persiste ni se publica nada (ver `tests/test_unit_of_work.py`).
- **Eventos de dominio** (`domain/events.py`): la entidad `Order` registra
  internamente un evento `OrderCreated` en su método de fábrica
  `Order.create(...)`, pero **no los publica ella misma**. Es el `UnitOfWork`
  quien, sólo tras un `commit()` exitoso, recolecta los eventos pendientes de
  todas las entidades tocadas (`order.pull_domain_events()`) y los publica en
  el `EventBus`. Esto evita el problema clásico de "el evento se publicó pero
  el dato no se guardó" (o al revés).
- El evento `OrderCreated` es manejado en la **capa de aplicación**
  (`application/event_handlers/order_created_handlers.py`), no en el
  dominio ni en infraestructura: así el caso de uso `CreateOrderUseCase` no
  necesita saber que existe una notificación.

### 1.4 Estrategias de migración hacia arquitectura limpia

En un proyecto real casi nunca se reescribe todo de golpe. Estrategias
recomendadas (aplicables sobre este mismo ejemplo):

1. **Extraer el dominio primero.** Identificar las reglas de negocio
   escondidas en controladores/ORMs (validaciones, cálculos) y moverlas a
   Entidades y Value Objects puros — como `Order.total()` o la regla
   "no hay orden vacía" en `Order.create`.
2. **Introducir puertos alrededor de la infraestructura existente**
   (patrón *Strangler Fig* / *Adapter*). Se define `OrderRepository` como
   interfaz y se envuelve el acceso a datos actual (ORM/SQL directo) en una
   implementación concreta, sin cambiar aún la base de datos real.
3. **Mover la orquestación a casos de uso**, dejando que controladores
   HTTP/CLI existentes simplemente llamen al nuevo caso de uso (patrón
   *Anti-Corruption Layer* entre el framework web y el core de negocio).
4. **Añadir Unit of Work y eventos de forma incremental**, primero para el
   flujo más crítico (p. ej. creación de orden), y luego extenderlo a otros
   agregados.
5. **Migrar módulo por módulo**, manteniendo pruebas de caracterización
   (*characterization tests*) que verifiquen que el comportamiento no
   cambió, y usando *feature flags* para alternar entre la implementación
   vieja y la nueva mientras se valida en producción.
6. **Retirar el código legado** sólo cuando el nuevo camino está probado y
   en uso, evitando el riesgo de un "big bang rewrite".

---

## 2. Objetivos: por qué deben cumplirse

### Objetivo 1 — "Estructurar un servicio con capas independientes y reglas claras"

Debe cumplirse porque:
- **Aísla el negocio del framework.** Si mañana cambiamos de CLI a una API
  REST con FastAPI, o la base de datos en memoria por PostgreSQL, el
  dominio y los casos de uso (`Order`, `CreateOrderUseCase`, etc.) **no se
  tocan**. Sólo se escribe un nuevo adaptador de infraestructura y un nuevo
  controlador/presenter.
- **Facilita las pruebas.** Como los casos de uso dependen de interfaces
  (`UnitOfWork`, `OrderRepository`) y no de implementaciones concretas, se
  pueden probar con adaptadores en memoria, rápidos y sin efectos
  secundarios (`tests/test_create_order_use_case.py`).
- **Reduce el acoplamiento y el "efecto dominó".** Un cambio en la forma en
  que se presenta la respuesta (JSON vs texto) no obliga a tocar la lógica
  de negocio; un cambio en la regla de negocio no obliga a tocar la capa
  HTTP.

### Objetivo 2 — "Gestionar transacciones y publicar eventos"

Debe cumplirse porque:
- **Consistencia transaccional.** Sin un Unit of Work, es fácil terminar
  guardando datos a medias o publicando eventos de operaciones que en
  realidad fallaron. El patrón UoW garantiza que "guardar" y "publicar
  eventos" ocurran como una sola unidad atómica, y sólo si hay `commit()`.
- **Desacoplamiento de efectos secundarios.** Publicar un evento
  (`OrderCreated`) permite que otras partes del sistema reaccionen (enviar
  notificación, actualizar un reporte, etc.) **sin que el caso de uso
  principal conozca esos consumidores**, cumpliendo el principio de
  responsabilidad única y abriendo la puerta a una arquitectura orientada a
  eventos (útil para escalar a microservicios más adelante).

---

## 3. Descripción de la solución

### 3.1 Qué hace el sistema

Un mini-servicio de órdenes con tres operaciones:

1. **Crear una orden** (`CreateOrderUseCase`): valida que tenga al menos un
   item, calcula el total, la persiste vía el `UnitOfWork` y — sólo tras el
   `commit()` — publica el evento `OrderCreated`, que dispara el envío de
   una notificación (impresa en consola / registrada en
   `notifications_log`).
2. **Consultar una orden por id** (`GetOrderUseCase`).
3. **Listar todas las órdenes** (`ListOrdersUseCase`).

### 3.2 Estructura de carpetas

```
orders_clean_architecture/
├── README.md
├── requirements.txt
├── run_demo.py                      # script de demostración end-to-end
├── src/orders/
│   ├── domain/                      # ── Entidades (círculo interno)
│   │   ├── entities.py              #    Order, OrderItem
│   │   ├── value_objects.py         #    Money, OrderStatus
│   │   ├── events.py                #    DomainEvent, OrderCreated
│   │   └── exceptions.py
│   ├── application/                 # ── Casos de uso
│   │   ├── dto.py                   #    Request/Response DTOs
│   │   ├── ports/                   #    Interfaces (Repository, UoW, EventBus)
│   │   ├── use_cases/               #    CreateOrder, GetOrder, ListOrders
│   │   └── event_handlers/          #    Reacciona a OrderCreated
│   ├── infrastructure/              # ── Adaptadores concretos
│   │   ├── persistence/             #    InMemoryOrderRepository, InMemoryUnitOfWork
│   │   └── events/                  #    InMemoryEventBus
│   └── interfaces/                  # ── Entrega / delivery
│       ├── controllers/             #    OrderController
│       ├── presenters/              #    OrderPresenter
│       └── cli/main.py              #    Composition root (build_controller)
└── tests/
    ├── test_order_entity.py         # pruebas de dominio puro
    ├── test_create_order_use_case.py# pruebas de caso de uso con dobles en memoria
    └── test_unit_of_work.py         # pruebas de que UoW sólo publica tras commit
```

### 3.3 Flujo de una petición "crear orden"

```
dict (payload) 
   → OrderController.create_order()
       → construye CreateOrderRequest (DTO)
       → CreateOrderUseCase.execute(request)
            → Order.create(...)                 [regla de negocio + evento OrderCreated en memoria]
            → uow.orders.add(order)
            → uow.commit()
                 → persiste (en memoria)
                 → recolecta eventos pendientes de las entidades
                 → event_bus.publish(OrderCreated)
                       → send_order_confirmation(event)   [handler en application]
       → OrderResponse (DTO)
   → OrderPresenter.present_order(response)
       → dict listo para mostrar / serializar a JSON
```

---

## 4. Cómo ejecutar la solución

### 4.1 Requisitos

- Python 3.10 o superior (usa `from __future__ import annotations` y
  sintaxis moderna de tipos).
- `pytest` (sólo para correr las pruebas).

### 4.2 Instalación

```bash
cd orders_clean_architecture
pip install -r requirements.txt
```

### 4.3 Ejecutar la demo end-to-end

```bash
python run_demo.py
```

Esto:
1. Crea una orden válida y muestra el JSON de salida (con su notificación
   impresa por el manejador de `OrderCreated`).
2. Consulta esa misma orden por id.
3. Intenta crear una orden vacía y muestra el error de negocio manejado
   (`EmptyOrderError` → `domain_error`).
4. Consulta una orden inexistente (`OrderNotFoundError` → `domain_error`).
5. Lista todas las órdenes almacenadas.

### 4.4 Ejecutar las pruebas unitarias

```bash
python -m pytest tests/ -v
```

Incluye:
- Pruebas de **dominio puro** (`Order`, reglas de negocio, generación del
  evento `OrderCreated`) sin ninguna dependencia externa.
- Pruebas del **caso de uso** `CreateOrder` usando los adaptadores en
  memoria (repositorio, UoW y event bus), verificando que se persiste la
  orden y se publica el evento correcto.
- Pruebas específicas del **Unit of Work**, verificando que los eventos de
  dominio **sólo** se publican cuando hay un `commit()` explícito.

### 4.5 Cómo extender esta base (siguientes pasos naturales)

- Reemplazar `InMemoryOrderRepository` / `InMemoryUnitOfWork` por una
  implementación con SQLAlchemy (el `UnitOfWork` pasaría a envolver una
  `Session` real, con `session.commit()` / `session.rollback()`).
- Agregar un controlador HTTP (por ejemplo con FastAPI) que reutilice
  exactamente los mismos casos de uso y el mismo `OrderPresenter`,
  cambiando sólo la capa `interfaces`.
- Sustituir `InMemoryEventBus` por un bus real (RabbitMQ/Kafka/SNS) sin
  tocar `application/event_handlers` ni los casos de uso.
