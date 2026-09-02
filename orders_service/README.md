# Orders Service — Proyecto Final Integrador (Arquitectura Hexagonal/Limpia)

Servicio de órdenes construido con **Arquitectura Hexagonal (Puertos y Adaptadores) /
Clean Architecture**, expuesto como API REST con **FastAPI**, con persistencia en
**PostgreSQL** (o SQLite para desarrollo), migraciones con **Alembic**, autenticación
**JWT**, observabilidad (logs estructurados + métricas Prometheus), y un pipeline
completo de **CI/CD** con lint, tipado, pruebas y auditoría de dependencias.

Este README cubre, en orden, lo que pide el enunciado del módulo: **contenidos
clave** que se están evaluando, **por qué** deben cumplirse los objetivos, y **cómo**
se resolvió y se ejecuta cada entregable.

---

## Índice

1. [Contenidos clave que se están revisando](#1-contenidos-clave-que-se-están-revisando)
2. [Por qué deben cumplirse los objetivos](#2-por-qué-deben-cumplirse-los-objetivos)
3. [Arquitectura del proyecto](#3-arquitectura-del-proyecto)
4. [Entregables: solución y cómo ejecutarlos](#4-entregables-solución-y-cómo-ejecutarlos)
   - [4.1 Código por capas + API](#41-código-por-capas--api)
   - [4.2 Pruebas (unitarias, contrato, integración/E2E)](#42-pruebas-unitarias-contrato-integracióne2e)
   - [4.3 Migraciones Alembic](#43-migraciones-alembic)
   - [4.4 Docker multistage y CI](#44-docker-multistage-y-ci)
   - [4.5 Auditoría de dependencias](#45-auditoría-de-dependencias)
5. [Ejecución rápida (quickstart)](#5-ejecución-rápida-quickstart)
6. [Referencia de la API](#6-referencia-de-la-api)
7. [Validación interactiva (Swagger UI)](#7-validación-interactiva-swagger-ui)
8. [Mapeo contra la rúbrica de evaluación](#8-mapeo-contra-la-rúbrica-de-evaluación)

---

## 1. Contenidos clave que se están revisando

Este proyecto integra, en un solo servicio, los contenidos vistos en los módulos
anteriores del curso, más los propios de este módulo final:

| Contenido clave | Dónde se aplica en este proyecto |
|---|---|
| **Arquitectura Hexagonal / Clean Architecture** | Separación estricta en `domain/`, `application/`, `infrastructure/`. El dominio no importa nada de fuera. |
| **Dominio rico (DDD táctico)** | `Order` es un *Aggregate Root* con invariantes protegidas (no se puede confirmar una orden vacía, no se puede transicionar de `cancelled` a nada). `Money`, `OrderStatus`, `ProductRef` son *Value Objects* inmutables. |
| **Puertos y Adaptadores** | Puertos definidos con `typing.Protocol` (`OrderRepository`, `EventPublisher`, `UnitOfWork`, `Clock`). Adaptadores: SQLAlchemy (real) e in-memory (pruebas). |
| **Principios SOLID pythónicos** | DIP vía `Protocol` (no ABC); un caso de uso = una responsabilidad (SRP); nuevos adaptadores se agregan sin modificar casos de uso (OCP). |
| **Eventos de dominio** | `OrderCreated`, `OrderItemAdded`, `OrderConfirmed`, `OrderCancelled`, acumulados en el agregado y publicados tras persistir (patrón *outbox* simplificado). |
| **API FastAPI segura y documentada** | JWT (OAuth2 Password flow), esquemas Pydantic con ejemplos, documentación automática en `/docs` y `/redoc`. |
| **Testing por niveles** | Unitario (dominio + aplicación, con **Hypothesis** para invariantes), **contrato** (misma suite corre contra 2 adaptadores distintos del mismo puerto), integración (API + DB real en SQLite), E2E (journey completo de negocio). |
| **Calidad de código** | `ruff` (lint + formato de imports), `mypy` estricto en modo `disallow_untyped_defs`. |
| **Persistencia versionada** | Migraciones Alembic (`upgrade`/`downgrade` probadas). |
| **Delivery** | Dockerfile multistage (build sin herramientas de compilación en la imagen final, usuario no-root, healthcheck), `docker-compose.yml` con Postgres. |
| **CI/CD** | Pipeline de GitHub Actions con jobs independientes: lint, tipado, tests con cobertura mínima, validación de migraciones, auditoría de dependencias, build de imagen Docker. |
| **Seguridad** | JWT con expiración, hashing de contraseñas con bcrypt/passlib (combinación de versiones validada para evitar el bug conocido), CORS configurable, auditoría de CVEs en dependencias. |
| **Observabilidad** | Logs JSON estructurados con `request_id` de correlación, métricas Prometheus (`/metrics`), endpoint `/health`. |

## 2. Por qué deben cumplirse los objetivos

**Construir un servicio con dominio, casos de uso, puertos y adaptadores.**
Sin esta separación, la lógica de negocio termina mezclada con SQL y con detalles de
FastAPI, lo que hace el código difícil de probar (hay que levantar una base de datos
para probar una regla de negocio) y frágil ante cambios de infraestructura (cambiar de
Postgres a otra base de datos obligaría a reescribir reglas de negocio). Aquí, la
prueba de que el objetivo se cumple es literal: los **77 tests unitarios y de
contrato corren sin base de datos ni HTTP**, y los mismos casos de uso funcionan
igual con el repositorio in-memory que con SQLAlchemy.

**Exponer una API FastAPI segura y documentada.**
Un servicio sin autenticación expone datos de negocio a cualquiera; sin documentación
generada automáticamente, cada consumidor tiene que leer el código fuente para saber
qué payload enviar. FastAPI genera OpenAPI/Swagger automáticamente a partir de los
mismos esquemas Pydantic que validan las peticiones, así que documentación y
validación nunca se desincronizan.

**Asegurar calidad (pruebas, lint, tipado) y delivery (Docker, CI/CD).**
El código que "funciona en mi máquina" no sirve en producción. El pipeline de CI
reproduce, de forma automática y en cada cambio, exactamente los mismos checks que se
corrieron localmente durante el desarrollo (ver sección 4.4), evitando que una
regresión llegue a `main`. La imagen Docker multistage garantiza que el artefacto que
se prueba en CI es el mismo que se despliega.

## 3. Arquitectura del proyecto

```
orders_service/
├── src/orders/
│   ├── domain/                     # Núcleo: SIN dependencias externas
│   │   ├── entities.py             # Order (Aggregate Root), OrderItem
│   │   ├── value_objects.py        # Money, OrderStatus, ProductRef
│   │   ├── events.py               # Eventos de dominio
│   │   ├── exceptions.py           # Excepciones de negocio puras
│   │   └── ports/                  # Protocols: OrderRepository, EventPublisher, UnitOfWork, Clock
│   ├── application/                # Casos de uso, orquestan dominio + puertos
│   │   ├── use_cases/              # Create/AddItem/Confirm/Cancel/Get/List
│   │   ├── dto.py                  # DTOs de aplicación (no son schemas HTTP)
│   │   └── mappers.py
│   └── infrastructure/             # Adaptadores + framework
│       ├── adapters/db/            # Modelos ORM, repos (SQLAlchemy e in-memory), UoW
│       ├── adapters/events/        # Publishers de eventos
│       ├── api/                    # FastAPI: routers, schemas, security, middleware
│       ├── observability/          # Logging JSON, métricas Prometheus
│       ├── db/migrations/          # Alembic
│       ├── config.py               # Settings (pydantic-settings)
│       └── composition_root.py     # Único lugar que conecta adaptadores concretos
├── tests/
│   ├── unit/{domain,application}/  # Sin DB, sin HTTP
│   ├── contract/                   # Misma suite contra 2 adaptadores
│   ├── integration/                # API real + SQLite real (sin mocks)
│   └── e2e/                        # Journey de negocio completo
├── diagrams/architecture.md        # Diagramas Mermaid (capas, secuencia, estados)
├── audit/                          # Evidencia de auditoría de dependencias
├── Dockerfile                      # Multistage
├── docker-compose.yml              # API + Postgres
├── .github/workflows/ci.yml        # Pipeline CI/CD
├── alembic.ini
├── requirements.txt / requirements-dev.txt
└── pyproject.toml                  # Config de pytest, ruff, mypy
```

Ver `diagrams/architecture.md` para los diagramas completos (capas, flujo de una
petición, máquina de estados de una orden).

## 4. Entregables: solución y cómo ejecutarlos

### 4.1 Código por capas + API

- **Dominio** (`src/orders/domain/`): `Order` es el *Aggregate Root*; toda mutación
  (`add_item`, `confirm`, `cancel`) pasa por sus métodos, que validan invariantes y
  registran eventos. No importa FastAPI, SQLAlchemy ni Pydantic.
- **Aplicación** (`src/orders/application/`): 6 casos de uso, cada uno una clase con
  un método `execute()`, que dependen únicamente de los `Protocol` del dominio.
- **Infraestructura** (`src/orders/infrastructure/`): adaptadores concretos
  (SQLAlchemy, JWT, FastAPI) y el *Composition Root* (`composition_root.py`), el
  único módulo que instancia adaptadores concretos y los inyecta en los casos de uso
  vía las dependencias de FastAPI (`api/dependencies.py`).

**Ejecutar la API en local (sin Docker):**

> **Nota sobre la versión de Python:** el proyecto requiere **Python 3.12**.
> `pydantic-core` (dependencia de `pydantic`/FastAPI) distribuye wheels
> precompilados solo hasta ciertas versiones de Python; si tu sistema tiene
> instalado Python 3.13/3.14 y creas el entorno con `python -m venv`, pip
> intentará **compilar `pydantic-core` desde código fuente con `maturin`/Rust**
> y la instalación fallará (ese es el error `Building wheel for pydantic-core
> ... did not run successfully` / `maturin pep517 build-wheel ... returned
> non-zero exit status`). La forma más simple de evitarlo es crear el entorno
> con **conda**, fijando explícitamente la versión de Python:

```bash
# 1. Crear el entorno con Python 3.12 (independiente de la versión del sistema)
conda create -n orders-service python=3.12 -y
conda activate orders-service

# 2. Instalar dependencias
pip install -r requirements-dev.txt
pip show fastapi sqlalchemy greenlet alembic pytest | grep -E "Name|Version"   # verificacion paso 2

# 3. Configurar variables de entorno
cp .env.example .env   # ajustar si es necesario
cat .env               # verificacion paso 3

# 4. Crear el esquema de base de datos (ver 4.3)
alembic upgrade head
ls -la orders.db       # verificacion paso 4

# 5. Levantar la API
uvicorn orders.infrastructure.api.main:app --reload --app-dir src

```
**Verificación:** la consola debe mostrar Uvicorn running on http://127.0.0.1:8000. Deja esta terminal abierta y corriendo.

Pasos opcionales:
- Para desactivar el entorno al terminar: `conda deactivate`.
- Para eliminarlo: `conda env remove -n orders-service`.

<details>
<summary>Alternativa sin conda (venv nativo)</summary>

Si prefieres no usar conda, funciona igual siempre que el `python` con el que
crees el `venv` sea 3.12. Verifica primero la versión disponible en tu sistema
(`python3.12 --version`; en macOS puedes instalarla con
`brew install python@3.12`) y apunta el `venv` a ese binario explícitamente:

```bash
python3.12 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
```

Usar `python` a secas (sin el sufijo de versión) creará el entorno con la
versión por defecto del sistema, que es justamente lo que provoca el error de
`pydantic-core` si esa versión es 3.13+.

La API queda disponible en `http://localhost:8000`, con documentación interactiva en
`http://localhost:8000/docs`.
</details>


**Usuario de demostración** (solo para el flujo de auth del laboratorio, ver
`infrastructure/api/security.py`): `demo` / `demo1234`.

### 4.2 Pruebas (unitarias, contrato, integración/E2E)

77 pruebas organizadas en 4 niveles, con marcadores de pytest (`@pytest.mark.unit`,
`contract`, `integration`, `e2e`) para poder correrlas por separado:

| Nivel | Qué valida | Dependencias externas |
|---|---|---|
| **Unit** (`tests/unit/`) | Invariantes del dominio (incluye pruebas basadas en propiedades con **Hypothesis**) y casos de uso con adaptadores fake | Ninguna |
| **Contract** (`tests/contract/`) | La **misma suite de aserciones** corre contra `InMemoryOrderRepository` y `SqlAlchemyOrderRepository`, garantizando que ambos cumplen el contrato del puerto `OrderRepository` | SQLite en memoria (para el adaptador SQL) |
| **Integration** (`tests/integration/`) | Endpoints HTTP reales (routing, validación Pydantic, autenticación JWT, mapeo de errores de dominio a códigos HTTP) contra una base de datos SQLite real por test | SQLite en archivo temporal |
| **E2E** (`tests/e2e/`) | Journey de negocio completo: login → crear orden → agregar items → confirmar → consultar → intentar mutar una orden cerrada (debe fallar) → cancelar | SQLite en archivo temporal |

**Ejecutar todas las pruebas con cobertura:**

```bash
pytest -v --cov=src/orders --cov-report=term-missing
```

**Ejecutar solo un nivel:**

```bash
pytest -m unit           # solo pruebas unitarias
pytest -m contract       # solo pruebas de contrato
pytest -m integration    # solo integración
pytest -m e2e            # solo end-to-end
```

Resultado de referencia (última corrida validada en el sandbox de desarrollo):
**77 passed, cobertura de línea 97%** sobre `src/orders`.

### 4.3 Migraciones Alembic

La migración inicial (`0001_initial_schema.py`) crea las tablas `orders` y
`order_items` con sus índices y la relación `FOREIGN KEY ... ON DELETE CASCADE`.

```bash
# Aplicar todas las migraciones pendientes
alembic upgrade head

# Revertir todo (útil para probar que el downgrade es correcto)
alembic downgrade base

# Ver el historial
alembic history
```

`alembic.ini` apunta por defecto a SQLite; para usar Postgres, exportar
`ORDERS_DATABASE_URL` antes de correr Alembic (el `env.py` la lee y sobreescribe la
URL del `.ini`):

```bash
export ORDERS_DATABASE_URL="postgresql+asyncpg://orders:orders@localhost:5432/orders"
alembic upgrade head
```

Dentro de Docker, `scripts/entrypoint.sh` aplica `alembic upgrade head`
automáticamente antes de arrancar `uvicorn`, así que el contenedor nunca corre con un
esquema desactualizado.

### 4.4 Docker multistage y CI

**Dockerfile** (`Dockerfile`): 2 etapas.
1. `builder`: instala dependencias (incluye compiladores) en un virtualenv aislado.
2. `runtime`: copia solo el virtualenv ya construido + el código fuente; sin
   compiladores, sin cache de pip, corre como usuario `orders` (no-root), con
   `HEALTHCHECK` sobre `/health`.

```bash
docker build -t orders-service:latest .
docker run -p 8000:8000 --env-file .env orders-service:latest
```

**docker-compose.yml**: levanta la API junto a Postgres 16, con `healthcheck` para
que la API no arranque antes de que la base de datos esté lista.

```bash
docker compose up --build
# API en http://localhost:8000, Postgres en localhost:5432
```

**Pipeline CI** (`.github/workflows/ci.yml`), en GitHub Actions, con 6 jobs
independientes (paralelizables donde no hay dependencia entre ellos):

1. `lint` — `ruff check`
2. `typecheck` — `mypy` en modo estricto
3. `test` — suite completa con `--cov-fail-under=85` (falla el build si la cobertura
   cae por debajo del umbral)
4. `migrations` — `alembic upgrade head` → `downgrade base` → `upgrade head` sobre
   una base de datos limpia, para detectar migraciones rotas
5. `dependency-audit` — `pip-audit` contra `requirements.txt` (ver 4.5)
6. `docker-build` — construye la imagen (sin publicarla), solo tras que `test`,
   `migrations` y `dependency-audit` pasen

### 4.5 Auditoría de dependencias

Ver `audit/README.md` y `audit/pip-audit-report.json` para el detalle completo.
En resumen: se ejecutó `pip-audit` sobre `requirements.txt`, se detectaron CVEs
conocidos en 3 paquetes (`pyjwt`, `python-multipart`, `starlette`), se corrigieron
fijando versiones más nuevas y se re-validó que la suite de 77 pruebas seguía
pasando. La corrida final no reporta vulnerabilidades conocidas:

```bash
pip-audit -r requirements.txt
# -> No known vulnerabilities found
```

## 5. Ejecución rápida (quickstart)

```bash
# 1. Clonar/descomprimir el proyecto y entrar al directorio
cd orders_service

# 2. Entorno virtual (Python 3.12 vía conda) + dependencias de desarrollo
conda create -n orders-service python=3.12 -y
conda activate orders-service
pip install -r requirements-dev.txt

# 3. Migraciones (SQLite por defecto, no requiere nada más instalado)
alembic upgrade head
ls -la orders.db

# 4. Levantar la API
uvicorn orders.infrastructure.api.main:app --reload --app-dir src

# 5. En otra terminal: correr la suite completa
pytest -v --cov=src/orders

# 6. Calidad de código
ruff check src tests
mypy src

# 7. Auditoría de dependencias
pip-audit -r requirements.txt
```

O, con Docker (no requiere Python instalado localmente):

```bash
docker compose up --build
```

## 6. Referencia de la API

| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| `POST` | `/auth/token` | Login (OAuth2 Password), devuelve JWT | No |
| `POST` | `/orders` | Crea una orden vacía | Sí |
| `GET` | `/orders` | Lista órdenes (filtro `customer_id`, paginación) | Sí |
| `GET` | `/orders/{id}` | Detalle de una orden | Sí |
| `POST` | `/orders/{id}/items` | Agrega un item a una orden `created` | Sí |
| `POST` | `/orders/{id}/confirm` | Confirma una orden con items | Sí |
| `POST` | `/orders/{id}/cancel` | Cancela una orden `created` o `confirmed` | Sí |
| `GET` | `/health` | Liveness/readiness | No |
| `GET` | `/metrics` | Métricas Prometheus | No |
| `GET` | `/docs` | Swagger UI | No |

Ejemplo de flujo completo con `curl`:

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/token \
  -d "username=demo&password=demo1234" | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

ORDER_ID=$(curl -s -X POST http://localhost:8000/orders \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"customer_id": "cust-1", "currency": "MXN"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")

curl -X POST http://localhost:8000/orders/$ORDER_ID/items \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"product_id": "prod-1", "product_name": "Teclado", "quantity": 1, "unit_price": "499.99"}'

curl -X POST http://localhost:8000/orders/$ORDER_ID/confirm -H "Authorization: Bearer $TOKEN"
```

## 7. Validación interactiva (Swagger UI)

Además de `curl` (sección 6), la forma más visual e intuitiva de demostrar el
funcionamiento del servicio en una evaluación es a través de **Swagger UI**, la
documentación interactiva que FastAPI genera automáticamente a partir de los
esquemas Pydantic. No es necesario escribir un solo comando.

> **Requisito previo:** el servidor debe estar corriendo (sección 4.1, paso 5, o
> `docker compose up --build`).

### 7.1 Abrir la documentación

Con el servidor corriendo, ve a:

```
http://127.0.0.1:8000/docs
```

Verás la interfaz Swagger UI con todos los endpoints agrupados por *tags*:
`auth`, `orders`, `observability`.

### 7.2 Obtener un token (login)

1. Despliega **`POST /auth/token`** haciendo clic sobre él.
2. Haz clic en el botón **"Try it out"**.
3. En los campos del formulario, llena:
   - `username`: `demo`
   - `password`: `demo1234`
4. Haz clic en **"Execute"**.
5. En la sección **"Response body"** verás algo como:
   ```json
   {
     "access_token": "eyJhbGciOiJIUzI1NiIs...",
     "token_type": "bearer"
   }
   ```
   Copia el valor de `access_token` (sin las comillas).

### 7.3 Autorizarte en la interfaz

1. Sube al inicio de la página y haz clic en el botón **"Authorize"** (con el
   ícono de candado 🔒, arriba a la derecha).
2. En el campo `Value`, pega el token que copiaste.
3. Haz clic en **"Authorize"** y luego en **"Close"**.

Desde este momento, **todos** los endpoints protegidos con candado enviarán
automáticamente el header `Authorization: Bearer <token>` — ya no necesitas
volver a pegarlo en cada llamada.

### 7.4 Crear una orden

1. Despliega **`POST /orders`**.
2. **"Try it out"**.
3. En el "Request body", edita el JSON de ejemplo:
   ```json
   {
     "customer_id": "cust-1",
     "currency": "MXN"
   }
   ```
4. **"Execute"**.
5. En la respuesta (código **201**), copia el valor de `"id"` — lo necesitas
   para los siguientes pasos.

### 7.5 Agregar un item a la orden

1. Despliega **`POST /orders/{order_id}/items`**.
2. **"Try it out"**.
3. Pega el `id` de la orden en el campo `order_id`.
4. En el body:
   ```json
   {
     "product_id": "prod-1",
     "product_name": "Teclado mecánico",
     "quantity": 2,
     "unit_price": "499.99"
   }
   ```
5. **"Execute"** → debe responder **200** con el item agregado y
   `total_amount` calculado.

### 7.6 Confirmar la orden

1. Despliega **`POST /orders/{order_id}/confirm`**.
2. **"Try it out"**, pega el mismo `order_id`, **"Execute"**.
3. Debe responder **200** con `"status": "confirmed"`.

### 7.7 Consultar el detalle

1. Despliega **`GET /orders/{order_id}`**.
2. **"Try it out"**, pega el `order_id`, **"Execute"**.
3. Verifica que el JSON completo refleje el estado final: items, total,
   status `confirmed`.

### 7.8 Probar los casos de error (robustez del dominio)

Esto es lo más útil para la evaluación, porque demuestra que las reglas de
negocio se respetan y no solo el "camino feliz":

| Acción | Resultado esperado |
|---|---|
| `POST /orders/{order_id}/items` sobre una orden ya **confirmada** | **409 Conflict** — `"error_type": "InvalidOrderStateError"` |
| `POST /orders/{order_id}/confirm` sobre una orden **sin items** | **422** — `"error_type": "EmptyOrderError"` |
| `GET /orders/algo-que-no-existe` | **404** — `"error_type": "OrderNotFoundError"` |
| Cualquier endpoint de `orders` tras **"Authorize" → "Logout"** | **401 Unauthorized** |

### 7.9 Revisar observabilidad

- **`GET /health`** (sin autenticación) → responde `{"status": "ok", ...}`.
- **`GET /metrics`** (sin autenticación) → responde en texto plano, formato
  Prometheus, con contadores de requests por ruta/método/status.

### Ventaja de usar `/docs` en la evaluación

Cada llamada desde Swagger muestra automáticamente:

- El **`curl` equivalente** generado (útil si el evaluador quiere ver el
  comando exacto).
- La **URL completa** de la petición.
- Los **códigos de respuesta HTTP reales** y el **body** de respuesta.
- Los headers de respuesta (incluyendo `X-Request-ID`, agregado por el
  middleware de correlación).

Es exactamente la misma API que se probó por `curl` en la sección 6 — Swagger
solo ofrece una interfaz gráfica sobre el mismo esquema OpenAPI autogenerado a
partir de los `schemas.py` con Pydantic. Si algo funciona en `/docs`, funciona
igual en producción o desde cualquier otro cliente HTTP.

## 8. Mapeo contra la rúbrica de evaluación

| Criterio de la rúbrica | Evidencia en este repositorio |
|---|---|
| Arquitectura | `domain/`, `application/`, `infrastructure/` con dependencias apuntando hacia el dominio; diagrama en `diagrams/architecture.md` |
| Dominio | `Order` (Aggregate Root) con invariantes y eventos; `Money`/`OrderStatus`/`ProductRef` como Value Objects inmutables |
| Puertos/Adaptadores | `domain/ports/*.py` (Protocols); 2 adaptadores por puerto de repositorio, validados con pruebas de contrato |
| API | FastAPI con JWT, CORS, esquemas Pydantic documentados, manejo de errores de dominio → HTTP |
| Pruebas | 77 tests en 4 niveles, 97% cobertura, Hypothesis para invariantes |
| Calidad | `ruff` y `mypy` sin errores (ver jobs `lint`/`typecheck` del CI) |
| CI/CD | `.github/workflows/ci.yml` con 6 jobs (lint, tipado, tests, migraciones, auditoría, build Docker) |
| Seguridad | JWT + bcrypt/passlib, CORS configurable, `pip-audit` sin CVEs conocidos |
| Observabilidad | Logs JSON con `request_id`, métricas Prometheus en `/metrics`, `/health` |
| Rendimiento | Operaciones async de punta a punta (FastAPI + SQLAlchemy async + aiosqlite/asyncpg), paginación en listados |
| Documentación | Este README + `diagrams/architecture.md` + OpenAPI autogenerado en `/docs` |
