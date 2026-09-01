# Módulo 15 — Arquitectura Hexagonal (Puertos y Adaptadores)

Laboratorio: caso de uso `CreateOrder` implementado con arquitectura
hexagonal en Python + FastAPI, con adaptadores intercambiables de
persistencia (memoria / SQLAlchemy) y de notificación (HTTP simulado).

---

## 1. Contenidos clave — qué se revisa y dónde está en el código

### 1.1 Capas: dominio, aplicación e infraestructura

| Capa | Carpeta | Responsabilidad | Qué NO debe contener |
|---|---|---|---|
| **Dominio** | `app/domain/` | Entidades (`Order`, `OrderItem`), reglas de negocio, excepciones y **puertos** (interfaces) | Ningún import de FastAPI, SQLAlchemy, `requests`, etc. |
| **Aplicación** | `app/application/` | Casos de uso (`CreateOrderUseCase`) que orquestan el dominio usando los puertos, y DTOs | Detalles de HTTP o SQL |
| **Infraestructura** | `app/infrastructure/`, `app/api/` | Adaptadores concretos: SQLAlchemy, notificador HTTP simulado, endpoints FastAPI | Reglas de negocio |

La regla de dependencia es siempre **hacia adentro**: infraestructura
depende de aplicación, aplicación depende de dominio, pero el dominio
no depende de nada externo. Puedes verificarlo tú mismo: `app/domain/`
no tiene ningún `import` de `fastapi`, `sqlalchemy` ni `pydantic`.

### 1.2 Puertos (interfaces/Protocols) y adaptadores (SQL, HTTP, mensajería)

Los **puertos** están definidos en `app/domain/ports.py` usando
`typing.Protocol` (interfaces estructurales, sin necesidad de herencia
explícita):

- `OrderRepositoryPort`: contrato de persistencia (`save`, `get_by_id`, `list_all`).
- `NotificationPort`: contrato de notificación (`notify_order_created`).

Los **adaptadores** que implementan esos puertos son intercambiables:

| Puerto | Adaptador | Archivo |
|---|---|---|
| `OrderRepositoryPort` | En memoria | `app/infrastructure/persistence/memory_repository.py` |
| `OrderRepositoryPort` | SQLAlchemy | `app/infrastructure/persistence/sqlalchemy_repository.py` |
| `NotificationPort` | HTTP simulado | `app/infrastructure/notifications/http_notifier.py` |

Cualquier clase que implemente los mismos métodos "encaja" en el
puerto sin necesidad de heredar de una clase base — es la idea de
"puertos y adaptadores" (hexágono): el dominio define el enchufe
(puerto), y cada tecnología concreta trae su propio adaptador.

### 1.3 Casos de uso y orquestación; DTOs vs entidades

- `app/application/use_cases.py` contiene `CreateOrderUseCase` y
  `GetOrderUseCase`. Un caso de uso **orquesta**: recibe un DTO,
  construye/valida entidades de dominio, llama a los puertos, y
  devuelve otro DTO. No contiene lógica de negocio "de fondo" (esa
  vive en la entidad `Order`), pero sí decide el orden de los pasos
  (guardar y luego notificar).
- `app/application/dtos.py` define los DTOs (`CreateOrderInputDTO`,
  `OrderOutputDTO`, etc.), que son estructuras planas sin
  comportamiento, distintas de las **entidades** de dominio
  (`app/domain/entities.py`) que sí tienen comportamiento y validan
  invariantes (por ejemplo, `Order` no puede crearse sin items;
  `OrderItem` no acepta cantidades negativas).

### 1.4 Inyección de dependencias y wiring en FastAPI

- `app/container.py` es el **único** lugar del proyecto donde se
  decide qué adaptador concreto se usa para cada puerto. Es el
  "wiring" del hexágono.
- `app/api/main.py` usa el sistema de `Depends` de FastAPI para
  inyectar los casos de uso (ya armados con sus adaptadores) en cada
  endpoint, sin que el endpoint sepa cómo se construyeron.
- Cambiar de repositorio en memoria a SQLAlchemy es tan simple como
  variar `Container(use_sqlalchemy=True)` (o la variable de entorno
  `USE_SQLALCHEMY=1`) — ninguna otra línea de código cambia.

### 1.5 Pruebas de dominio, contrato y end-to-end

| Tipo | Carpeta | Qué valida |
|---|---|---|
| **Dominio** | `tests/domain/` | Reglas de negocio puras de `Order`/`OrderItem`, sin infraestructura |
| **Contrato** | `tests/contract/` | Que **todos** los adaptadores de `OrderRepositoryPort` (memoria y SQLAlchemy) cumplen el mismo comportamiento observable |
| **End-to-end** | `tests/e2e/` | El flujo completo vía HTTP: request → FastAPI → caso de uso → dominio → adaptadores → response |

---

## 2. Objetivos — por qué deben cumplirse

**Objetivo 1: Separar reglas de negocio de detalles de infraestructura.**
Si la lógica de "un pedido no puede estar vacío" viviera dentro de un
endpoint de FastAPI o de una query SQL, cambiar de framework web o de
motor de base de datos obligaría a reescribir las reglas de negocio, con
alto riesgo de introducir bugs. Al aislar el dominio, las reglas se
prueban de forma aislada, rápida (sin BD, sin red) y se reutilizan sin
importar el "entregable" final (API REST, CLI, worker de colas, etc.).
En este laboratorio lo comprobamos con las **pruebas de dominio**, que
corren en milisegundos y no dependen de nada externo.

**Objetivo 2: Definir puertos estables y adaptadores intercambiables.**
Un puerto bien diseñado no cambia aunque cambie la tecnología detrás.
Esto permite:
- Evolucionar/reemplazar infraestructura (ej. migrar de SQLite a
  Postgres, o de un webhook HTTP a una cola de mensajería) sin tocar el
  dominio ni la aplicación.
- Probar el sistema con adaptadores "falsos" (en memoria, HTTP
  simulado) que son rápidos y deterministas, reservando los
  adaptadores reales para entornos de integración/producción.
- Verificar, con **pruebas de contrato**, que todo adaptador nuevo
  cumple exactamente lo que el resto del sistema espera de él — así
  evitamos que un adaptador "se comporte distinto" y rompa algo en
  producción que las pruebas unitarias no detectaron.

En este proyecto, `CreateOrderUseCase` nunca importa `sqlalchemy` ni
`requests`: solo conoce `OrderRepositoryPort` y `NotificationPort`. Eso
es la prueba de que ambos objetivos se cumplen.

---

## 3. Descripción de la solución

```
hexagonal-orders/
├── app/
│   ├── domain/                 # Dominio: entidades, excepciones, puertos
│   │   ├── entities.py         #   Order, OrderItem, OrderStatus
│   │   ├── exceptions.py       #   EmptyOrderError, InvalidQuantityError, ...
│   │   └── ports.py            #   OrderRepositoryPort, NotificationPort (Protocols)
│   ├── application/            # Aplicación: casos de uso y DTOs
│   │   ├── dtos.py
│   │   └── use_cases.py        #   CreateOrderUseCase, GetOrderUseCase
│   ├── infrastructure/         # Infraestructura: adaptadores concretos
│   │   ├── persistence/
│   │   │   ├── memory_repository.py       # Adaptador en memoria
│   │   │   └── sqlalchemy_repository.py   # Adaptador SQLAlchemy
│   │   ├── notifications/
│   │   │   └── http_notifier.py           # Adaptador HTTP simulado
│   │   └── db/
│   │       └── models.py                  # Modelos ORM (detalle de BD)
│   ├── api/                    # Adaptador de entrada: API HTTP (FastAPI)
│   │   ├── main.py
│   │   └── schemas.py
│   └── container.py            # Wiring / inyección de dependencias
├── tests/
│   ├── domain/                 # Pruebas de dominio
│   ├── contract/                # Pruebas de contrato (memoria vs SQLAlchemy)
│   └── e2e/                    # Pruebas end-to-end (API completa)
├── requirements.txt
├── pytest.ini
└── README.md
```

### Caso de uso `CreateOrder`

1. El cliente HTTP hace `POST /orders` con `customer_id` y una lista de
   `items` (`app/api/schemas.py::CreateOrderRequest`).
2. `app/api/main.py` traduce el request a un
   `CreateOrderInputDTO` (`app/application/dtos.py`).
3. `CreateOrderUseCase.execute(...)`:
   - Construye entidades `OrderItem` y `Order`, que validan las reglas
     de negocio (pedido no vacío, cantidades/precios válidos).
   - Llama a `repository.save(order)` — puerto `OrderRepositoryPort`.
   - Llama a `notifier.notify_order_created(order)` — puerto
     `NotificationPort`.
   - Devuelve un `OrderOutputDTO`.
4. `app/api/main.py` traduce el DTO de salida a `OrderResponse` (JSON).

El mismo caso de uso funciona sin cambios ya sea que el repositorio
esté respaldado por un diccionario en memoria o por SQLite/Postgres vía
SQLAlchemy, y ya sea que la notificación sea un HTTP real o (como en
este laboratorio) uno simulado.

---

## 4. Cómo ejecutar el proyecto

### 4.1 Requisitos

- Python 3.11 o superior.

### 4.2 Instalación

```bash
# 1) Entra a la carpeta del proyecto
cd lab15

# 2) (Recomendado) crea un entorno virtual
python -m venv .venv
source .venv/bin/activate        # En Windows: .venv\Scripts\activate

# 3) Instala las dependencias
pip install -r requirements.txt
```

### 4.3 Ejecutar la API

```bash
uvicorn app.api.main:app --reload
```

- La API queda disponible en `http://127.0.0.1:8000`.
- Documentación interactiva (Swagger UI): `http://127.0.0.1:8000/docs`.
- Por defecto usa el adaptador de repositorio **en memoria** (los datos
  se pierden al reiniciar el proceso). Para usar el adaptador
  **SQLAlchemy/SQLite** (persistencia real en `orders.db`):

```bash
USE_SQLALCHEMY=1 uvicorn app.api.main:app --reload
```

### 4.4 Validar la API manualmente (con el servidor corriendo)

Cuando ejecutas `uvicorn app.api.main:app --reload`, la terminal se
queda "colgada" mostrando logs (algo como `Uvicorn running on
http://127.0.0.1:8000` y `Application startup complete`). **Eso es
normal**: significa que el servidor está arriba y esperando peticiones.
No la cierres — necesitas otra ventana/pestaña de terminal, o el
navegador, para validar.

#### Opción A — Swagger UI (recomendada, sin escribir código)

1. **Confirma que el servidor está arriba.** En la terminal donde
   corriste `uvicorn` debes ver `Application startup complete`.
2. **Abre la documentación interactiva.** Ve a
   `http://127.0.0.1:8000/docs` en tu navegador. FastAPI genera
   automáticamente una interfaz Swagger UI con los dos endpoints
   (`POST /orders` y `GET /orders/{order_id}`) y botones para probarlos.
3. **Prueba `POST /orders`.** Haz clic en el endpoint, luego en
   **"Try it out"**. Verás un cuadro de texto JSON editable. Pega:

   ```json
   {
     "customer_id": "cust-123",
     "items": [
       {"product_id": "SKU-1", "quantity": 2, "unit_price": "10.00"}
     ]
   }
   ```

   Haz clic en **"Execute"**.
4. **Lee la respuesta.** Debajo aparece el "Response body" con código
   `201` y un JSON que incluye un `id` generado automáticamente (UUID),
   `status: "CREATED"` y el `total` calculado (`20.00`). Copia ese
   `id`, lo necesitas para el siguiente paso.
5. **Prueba `GET /orders/{order_id}`** con ese `id`. Haz clic en el
   endpoint, **"Try it out"**, pega el `id` en el campo `order_id` y
   **"Execute"**. Debes recibir código `200` con el mismo pedido que
   acabas de crear — así confirmas que el repositorio (en memoria por
   defecto) realmente lo guardó.
6. **Prueba un caso de error (opcional pero útil).** Repite el paso 3
   pero con `"items": []` (lista vacía). Debe devolver `422`, porque la
   entidad de dominio `Order` no permite pedidos sin items. Esto
   confirma que la validación de negocio realmente está funcionando, no
   solo el "camino feliz".

#### Opción B — línea de comandos con `curl`

Abre una **segunda terminal** (deja la primera con `uvicorn` corriendo)
y ejecuta:

Crear un pedido:

```bash
curl -X POST http://127.0.0.1:8000/orders \
  -H "Content-Type: application/json" \
  -d '{
        "customer_id": "cust-123",
        "items": [
          {"product_id": "SKU-1", "quantity": 2, "unit_price": "10.00"},
          {"product_id": "SKU-2", "quantity": 1, "unit_price": "5.50"}
        ]
      }'
```

Consultar un pedido (reemplaza `<id>` por el `id` devuelto arriba):

```bash
curl http://127.0.0.1:8000/orders/<id>
```

La salida es el mismo JSON que verías en Swagger.

#### Detalles a tener en cuenta

- **Los datos se pierden al reiniciar el proceso** si no usaste
  `USE_SQLALCHEMY=1`, porque el adaptador por defecto guarda los
  pedidos en un diccionario en memoria (RAM). Si detienes el servidor
  (`Ctrl+C`) y lo vuelves a levantar, el pedido que creaste ya no
  existirá — es el comportamiento esperado, no un bug.
- **Si algo falla** (por ejemplo, error `500`), revisa la terminal
  donde corre `uvicorn`: ahí aparece el traceback completo de Python,
  con más detalle que lo que muestra Swagger.

### 4.5 Validar con `pytest` (recomendado para desarrollo y CI)

A diferencia de la validación manual, `pytest` **no necesita que
`uvicorn` esté corriendo**. FastAPI trae un `TestClient` que simula las
peticiones HTTP directamente en memoria, sin abrir ningún puerto de
red — por eso las pruebas de `tests/e2e/` corren en milisegundos. Si
`uvicorn` sigue activo en otra terminal, puedes dejarlo así o pararlo
con `Ctrl+C`; no interfiere.

1. **Corre toda la suite**, parado en la carpeta del proyecto (donde
   está `pytest.ini`):

   ```bash
   pytest
   ```

   Verás 19 pruebas en total: 6 de dominio, 8 de contrato (memoria y
   SQLAlchemy) y 5 end-to-end. Todas deben salir en verde (`PASSED`).

2. **Corre solo las pruebas end-to-end** (el equivalente automatizado
   de lo que hiciste a mano con Swagger/`curl`):

   ```bash
   pytest tests/e2e -v
   ```

   El flag `-v` (verbose) muestra el nombre de cada prueba individual
   y si pasó o falló.

3. **Relaciona cada prueba con lo que ya probaste a mano.** Abre
   `tests/e2e/test_create_order_api.py`:
   - `test_create_order_returns_201_with_total_and_status` — equivale
     al paso 3-4 de la Opción A (crear un pedido y revisar el JSON de
     respuesta).
   - `test_get_order_after_create_returns_same_order` — equivale al
     paso 5 (encadena un `POST` y un `GET`).
   - `test_create_order_with_empty_items_returns_422` — equivale al
     paso 6 (caso de error con items vacíos).
   - `test_create_order_triggers_notification_adapter` — verifica algo
     que Swagger **no puede mostrarte**: que el adaptador de
     notificación HTTP simulado efectivamente "recibió" el evento
     `order_created`.
   - `test_get_unknown_order_returns_404` — pide un pedido con un `id`
     que no existe y espera `404`.

4. **Corre una sola prueba puntual**, útil cuando estás depurando algo
   específico sin correr toda la suite:

   ```bash
   pytest tests/e2e/test_create_order_api.py::test_create_order_with_empty_items_returns_422 -v
   ```

5. **Corre solo un tipo de prueba**, por ejemplo las de contrato (que
   comparan el adaptador en memoria contra el de SQLAlchemy):

   ```bash
   pytest tests/contract -v
   ```

6. **Interpreta un fallo.** Si una prueba falla, `pytest` imprime un
   `assert` señalando exactamente qué valor esperaba vs. qué recibió
   (por ejemplo `assert 200 == 404`), junto con el traceback de la
   petición HTTP simulada. Fíjate en qué carpeta está la prueba que
   falló (`tests/domain`, `tests/contract` o `tests/e2e`) para saber si
   el problema está en el dominio, en un adaptador o en el wiring de la
   API.

> **Nota de compatibilidad:** este proyecto se probó también con
> `pytest 9.1.1` (la familia 9.x introdujo cambios internos, pero
> ninguno afecta el código de este laboratorio) — el pin en
> `requirements.txt` es `pytest>=8.0,<10.0`.

### 4.6 ¿Validación manual o con `pytest`? — cuándo usar cada una

| | Swagger UI / `curl` | `pytest` (`tests/e2e/`) |
|---|---|---|
| ¿Necesita `uvicorn` corriendo? | Sí | No — usa `TestClient` en memoria |
| ¿Abre un puerto de red real? | Sí (`127.0.0.1:8000`) | No |
| Velocidad | Manual, un caso a la vez | Automático, toda la suite en segundos |
| ¿Repetible / apto para CI? | No (requiere intervención humana) | Sí |
| ¿Para qué sirve mejor? | Ver la API "de verdad", como la vería un cliente externo; demos | Desarrollo diario, detectar regresiones, integrarlo en un pipeline de CI |

En la práctica se usan **ambas**: `pytest` para el trabajo del día a
día (rápido, repetible, se puede automatizar), y Swagger/`curl` cuando
quieres confirmar que el servidor realmente funciona end-to-end como
lo haría un cliente real.

### 4.7 Ejercicio sugerido para extender el laboratorio

Como práctica adicional, se puede:

1. Agregar un nuevo adaptador de notificación (por ejemplo, uno que
   simule el envío a una cola de mensajería) implementando
   `NotificationPort`, sin tocar `CreateOrderUseCase`.
2. Agregar sus propias pruebas de contrato para ese nuevo adaptador,
   reutilizando `RepositoryContractTests` como referencia de patrón.
3. Cambiar `Container` para inyectar el nuevo adaptador vía una
   variable de entorno, igual que se hizo con `USE_SQLALCHEMY`.
