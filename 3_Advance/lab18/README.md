# Módulo 18 · CLI y Automatización

CLI productiva construida con **Typer** para gestionar `Orders` consumiendo una
API REST, más un par de scripts de mantenimiento (`argparse` y `click`) que
completan el temario. Todo el código está validado end-to-end: tests con
pytest, y una corrida manual real levantando la API y ejecutando el CLI
instalado como comando del sistema.

---

## 1. Contenidos clave — qué se está revisando y por qué

### 1.1 `argparse`, `click` y `typer`
El módulo pide dominar las tres herramientas de CLI más usadas en Python, no
solo una, porque cada una resuelve un problema distinto y en el trabajo real
te vas a topar con las tres:

- **`argparse`** — está en la librería estándar (sin instalar nada). Es la
  opción correcta para scripts pequeños, de un solo propósito, que se
  ejecutan desde cron o un pipeline de CI/CD y no necesitan subcomandos.
  Aquí se usa en `scripts/maintenance/health_check.py`.
- **`click`** — añade decoradores, validación de tipos, flags booleanas y
  mejores mensajes de ayuda con poco código extra. Es un buen punto medio
  cuando el script empieza a crecer pero todavía no necesita subcomandos
  anidados ni autocompletado. Aquí se usa en
  `scripts/maintenance/cleanup_old_orders.py`.
- **`typer`** — construido sobre `click`, usa *type hints* para generar
  parseo de argumentos, validación, ayuda (`--help`) y autocompletado casi
  gratis. Es la mejor opción cuando el CLI tiene varios subcomandos
  relacionados (como `list` / `create` / `delete`) que deben mantenerse
  como un producto, no como un script suelto. Aquí es el corazón del
  laboratorio: `orders_cli/cli.py`.

Tener los tres en el mismo proyecto permite comparar en código real cuándo
usar cada uno, en vez de memorizar la teoría.

### 1.2 Configuración por variables de entorno
Un CLI "productivo y mantenible" no puede tener la URL de la API, tokens ni
timeouts *hardcodeados*: eso rompe la promesa de "el mismo binario funciona
igual en local, CI y producción". Por eso toda la configuración vive en
`orders_cli/config.py`, vía `pydantic-settings`, con el prefijo `ORDERS_`:

| Variable                | Default                 | Descripción                          |
|--------------------------|--------------------------|---------------------------------------|
| `ORDERS_API_BASE_URL`    | `http://127.0.0.1:8000` | URL base de la API de Orders          |
| `ORDERS_API_TIMEOUT`     | `5.0`                    | Timeout en segundos por request       |
| `ORDERS_API_TOKEN`       | (vacío)                  | Token Bearer opcional para auth       |

`pydantic-settings` además lee automáticamente un archivo `.env` (ver
`.env.example`), que es el mecanismo estándar en despliegues reales
(Docker, Kubernetes, CI) para inyectar configuración sin tocar código.

### 1.3 Scripts de mantenimiento
Además del CLI "de producto", todo proyecto real necesita scripts chicos de
soporte: verificar que un servicio esté vivo, limpiar datos obsoletos, etc.
Se incluyen dos, cada uno mostrando una herramienta distinta:

- `scripts/maintenance/health_check.py` (argparse) — hace `GET /health` y
  devuelve código de salida `0`/`1`, pensado para monitoreo/cron/CI.
- `scripts/maintenance/cleanup_old_orders.py` (click) — borra órdenes en un
  estado dado (por defecto `cancelled`), con `--dry-run` para simular sin
  borrar nada.

---

## 2. Objetivos — por qué importan

**"Construir CLIs productivas y mantenibles"**: una CLI se usa a diario por
personas y por pipelines automatizados; si no es mantenible (código
desordenado, sin tests, sin manejo de errores) se convierte rápido en un
punto de fricción y de fallas silenciosas. Por eso aquí:
- Los comandos están separados de la lógica de red (`cli.py` vs `client.py`),
  así se pueden testear sin necesitar un servidor real corriendo.
- Los errores de red se capturan y se traducen en mensajes claros + código de
  salida distinto de `0`, para que scripts que llamen al CLI puedan detectar
  fallos automáticamente.
- Hay confirmación interactiva antes de borrar (`delete`), salvo que se pase
  `--yes`, evitando borrados accidentales en uso manual pero permitiendo
  automatización sin intervención humana.

**"Integrar automatizaciones del proyecto"**: un CLI que solo vive en la
laptop del desarrollador no automatiza nada. Por eso:
- Se registra un **entry point** (`orders-cli`) en `pyproject.toml`, de modo
  que tras `pip install` el comando queda disponible en el `PATH` del
  sistema, igual que `git` o `docker`, listo para usarse desde cron, un
  Makefile, un pipeline de CI/CD o un contenedor.
- La configuración por variables de entorno permite reutilizar el mismo
  binario en distintos entornos sin recompilar ni editar código.
- Los scripts de mantenimiento son ejecutables de forma independiente y
  devuelven códigos de salida estándar (`0` éxito / `1` error), el contrato
  que cualquier orquestador (cron, GitHub Actions, Airflow, etc.) espera.

---

## 3. Descripción de la solución

```
modulo18_cli_automation/
├── pyproject.toml            # entry point `orders-cli`
├── requirements.txt
├── .env.example
├── src/
│   ├── orders_api/            # API FastAPI en memoria (stand-in del servicio real)
│   │   ├── main.py            # endpoints: /health, /orders (GET/POST), /orders/{id} (GET/DELETE)
│   │   └── schemas.py         # OrderCreate / OrderOut (Pydantic)
│   └── orders_cli/            # el CLI del laboratorio
│       ├── config.py          # Settings (pydantic-settings, env ORDERS_*)
│       ├── client.py          # OrdersClient: encapsula las llamadas httpx a la API
│       └── cli.py             # app Typer: list / create / delete / config + entry point `main()`
├── scripts/maintenance/
│   ├── health_check.py        # argparse: chequeo de salud de la API
│   └── cleanup_old_orders.py  # click: borra órdenes por estado, con --dry-run
└── tests/
    ├── conftest.py            # levanta la API real en un thread para tests end-to-end
    ├── test_api.py            # tests de la API en memoria
    └── test_cli.py            # tests del CLI vía Typer CliRunner contra la API real
```

`orders_api` es una API mínima en memoria que representa "la API" que el
laboratorio pide consumir. En un proyecto real sería el servicio de Orders
construido con Clean Architecture (Módulo 16) corriendo en FastAPI; aquí se
simplificó a un solo archivo para que el foco quede 100% en el CLI, pero el
`OrdersClient` solo depende de un contrato HTTP (`GET/POST/DELETE /orders`),
por lo que apuntarlo a cualquier otra implementación de esa API es tan
simple como cambiar `ORDERS_API_BASE_URL`.

### Comandos del CLI

| Comando                                                                 | Qué hace                                   |
|--------------------------------------------------------------------------|---------------------------------------------|
| `orders-cli list [--status ESTADO]`                                      | Lista órdenes (opcionalmente filtradas)     |
| `orders-cli create -c CLIENTE -i ITEM [-i ITEM ...] -t TOTAL`             | Crea una orden                              |
| `orders-cli delete ORDER_ID [--yes]`                                      | Borra una orden (pide confirmación salvo `--yes`) |
| `orders-cli config`                                                       | Muestra la configuración activa (env vars)  |

---

## 4. Cómo ejecutarlo

### 4.1 Instalación

```bash
cd modulo18_cli_automation
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e . -r requirements.txt
```

El `-e .` instala el paquete en modo editable y registra el comando
`orders-cli` en el `PATH` del entorno virtual (gracias al `[project.scripts]`
de `pyproject.toml`).

### 4.2 Levantar la API (backend que consume el CLI)

```bash
uvicorn orders_api.main:app --reload --port 8000
```

Déjala corriendo en una terminal; en otra terminal (con el mismo venv
activado) se usa el CLI.

### 4.3 Configurar variables de entorno

```bash
cp .env.example .env
# editar .env si la API corre en otra URL/puerto
```

O exportarlas directamente:

```bash
export ORDERS_API_BASE_URL=http://127.0.0.1:8000
export ORDERS_API_TIMEOUT=5.0
```

### 4.4 Usar el CLI

```bash
orders-cli config
orders-cli create --customer "Marcos" --item laptop --item mouse --total 1500
orders-cli list
orders-cli list --status pending
orders-cli delete <ORDER_ID>          # pide confirmación
orders-cli delete <ORDER_ID> --yes    # sin confirmación (uso en scripts)
orders-cli --help                     # ayuda autogenerada por Typer
```

### 4.5 Scripts de mantenimiento

```bash
# argparse: chequeo de salud, código de salida 0/1
python scripts/maintenance/health_check.py
python scripts/maintenance/health_check.py --url http://127.0.0.1:8000 --timeout 3

# click: limpieza de órdenes por estado
python scripts/maintenance/cleanup_old_orders.py --dry-run
python scripts/maintenance/cleanup_old_orders.py --status cancelled
```

Ambos también respetan `ORDERS_API_BASE_URL` si no se pasa `--url`.

### 4.6 Correr los tests

```bash
pip install -e . -r requirements.txt   # si no se hizo antes
pytest tests/ -v
```

Los tests de `test_cli.py` levantan la API real (`uvicorn`) en un thread en
background durante la sesión de pytest y hacen que el CLI le pegue por HTTP
de verdad — es una prueba end-to-end, no solo unitaria. Resultado esperado:
9 tests pasando (4 de la API, 5 del CLI).

### 4.7 Empaquetar / distribuir

```bash
pip install build
python -m build
```

Genera un wheel instalable (`pip install orders_cli_toolkit-0.1.0-py3-none-any.whl`)
que en cualquier máquina deja disponible el comando `orders-cli`, listo para
usarse desde cron, un Makefile o un pipeline de CI/CD.
