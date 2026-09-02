# Diagramas de arquitectura — Orders Service

## 1. Capas de la Arquitectura Hexagonal/Limpia

```mermaid
flowchart TB
    subgraph EXT["Actores externos"]
        CLIENT["Cliente HTTP<br/>(browser, app, curl)"]
        DB[("Base de datos<br/>PostgreSQL / SQLite")]
    end

    subgraph INFRA["Infraestructura (adaptadores)"]
        API["FastAPI Routers<br/>(auth, orders, health)"]
        MW["Middleware<br/>(request-id, logging, métricas)"]
        REPO["SqlAlchemyOrderRepository"]
        INMEM["InMemoryOrderRepository<br/>(tests)"]
        EVT["LoggingEventPublisher"]
        SEC["JWT Security"]
    end

    subgraph APP["Aplicación (casos de uso)"]
        UC1["CreateOrderUseCase"]
        UC2["AddItemToOrderUseCase"]
        UC3["ConfirmOrderUseCase"]
        UC4["CancelOrderUseCase"]
        UC5["GetOrderUseCase / ListOrdersUseCase"]
    end

    subgraph DOMAIN["Dominio (núcleo, sin dependencias externas)"]
        ORDER["Order (Aggregate Root)"]
        VO["Value Objects<br/>(Money, OrderStatus, ProductRef)"]
        EVENTS["Domain Events"]
        PORTS["Puertos (Protocol)<br/>OrderRepository, EventPublisher, UnitOfWork"]
    end

    CLIENT --> API
    API --> MW
    API --> SEC
    API --> UC1 & UC2 & UC3 & UC4 & UC5
    UC1 & UC2 & UC3 & UC4 & UC5 --> ORDER
    UC1 & UC2 & UC3 & UC4 & UC5 -.depende de.-> PORTS
    REPO -.implementa.-> PORTS
    INMEM -.implementa.-> PORTS
    EVT -.implementa.-> PORTS
    REPO --> DB
    ORDER --> VO
    ORDER --> EVENTS

    classDef domain fill:#fef3c7,stroke:#b45309,color:#78350f
    classDef app fill:#dbeafe,stroke:#1d4ed8,color:#1e3a8a
    classDef infra fill:#dcfce7,stroke:#15803d,color:#14532d
    class ORDER,VO,EVENTS,PORTS domain
    class UC1,UC2,UC3,UC4,UC5 app
    class API,MW,REPO,INMEM,EVT,SEC infra
```

**Regla de dependencia (la más importante de Clean Architecture):** las flechas de
dependencia siempre apuntan hacia adentro. El dominio (amarillo) no importa nada de
aplicación (azul) ni de infraestructura (verde). La aplicación depende solo de
**puertos** (`Protocol`), nunca de adaptadores concretos. Infraestructura es la única
capa que conoce simultáneamente el dominio y el mundo exterior (FastAPI, SQLAlchemy).

## 2. Flujo de una petición (ej. `POST /orders/{id}/confirm`)

```mermaid
sequenceDiagram
    participant C as Cliente
    participant R as Router (orders.py)
    participant D as Dependency (get_confirm_order_use_case)
    participant UOW as SqlAlchemyUnitOfWork
    participant UC as ConfirmOrderUseCase
    participant O as Order (dominio)
    participant Repo as SqlAlchemyOrderRepository
    participant EP as EventPublisher

    C->>R: POST /orders/123/confirm (Bearer token)
    R->>D: Depends(get_current_user) valida JWT
    R->>D: Depends(get_confirm_order_use_case)
    D->>UOW: abre sesión + transacción
    D->>UC: construye caso de uso con repo + publisher
    R->>UC: execute("123")
    UC->>Repo: get("123")
    Repo-->>UC: Order (reconstruida desde SQL)
    UC->>O: order.confirm()
    O-->>UC: evento OrderConfirmed acumulado
    UC->>Repo: save(order)
    UC->>EP: publish(pull_events())
    UC-->>R: OrderDTO
    R->>UOW: commit() (tras el yield de la dependencia)
    R-->>C: 200 OK + OrderResponse JSON
```

## 3. Máquina de estados de una Orden

```mermaid
stateDiagram-v2
    [*] --> created: Order.create()
    created --> confirmed: confirm()<br/>(requiere ≥1 item)
    created --> cancelled: cancel()
    confirmed --> cancelled: cancel()
    cancelled --> [*]
    confirmed --> [*]
```
