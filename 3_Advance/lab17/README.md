# Módulo 17 — Empaquetado, Distribución y CI/CD

Servicio de referencia: **Orders API** (FastAPI), usado como caso práctico para
empaquetar una librería/servicio Python en un *wheel*, contenerizarlo con un
Dockerfile multistage, y automatizar todo el ciclo (lint → type-check → tests
→ build → push) en un pipeline de CI/CD con GitHub Actions.

---

## 1. Contenidos clave — qué se revisa y por qué

### 1.1 Construcción de wheels y publicación (PyPI / artefactos internos)

Un **wheel** (`.whl`) es el formato binario estándar de distribución en Python
(PEP 427/517/518): empaqueta el código fuente ya construido según metadatos
declarativos (`pyproject.toml`), sin necesidad de ejecutar `setup.py` en la
máquina destino. Esto se revisa porque:

- Es la forma reproducible y estándar de compartir código Python entre
  proyectos, equipos o servicios (vía PyPI público, o un índice interno como
  Azure Artifacts, JFrog Artifactory o un servidor `pip` privado).
- Separa **build-time** (compilar, resolver dependencias de construcción) de
  **runtime** (solo instalar el artefacto ya construido), lo cual es la base
  de las imágenes Docker multistage del punto siguiente.
- Un wheel válido obliga a que el proyecto tenga metadatos correctos
  (`name`, `version`, `dependencies`, entry points), algo que se aprovecha
  también para el propio contenedor.

En este módulo se usa **Hatchling** como *build backend* (declarado en
`[build-system]` de `pyproject.toml`) por ser ligero y con soporte nativo de
`src/` layout, aunque el mismo flujo aplica igual con `setuptools` o `poetry-core`.

### 1.2 Docker multistage y buenas prácticas

Se revisa la construcción de imágenes Docker en **dos etapas**:

1. **`builder`**: instala herramientas de construcción y genera el wheel.
2. **`runtime`**: parte de una imagen limpia y solo copia el `.whl` ya
   construido, instalándolo con `pip`.

Esto importa porque una imagen construida en una sola etapa arrastra
compiladores, cache de `pip`, código fuente y archivos de test a producción,
lo que:

- Infla el tamaño de la imagen (más lenta de desplegar y descargar).
- Aumenta la superficie de ataque (herramientas de compilación innecesarias
  en runtime).
- Dificulta la reproducibilidad (mezcla dependencias de build y de ejecución).

Buenas prácticas aplicadas en el `Dockerfile` de este módulo:

- **Multistage** (`builder` → `runtime`) para una imagen final mínima.
- **Usuario no root** (`app`, uid 1000) — nunca correr el proceso como root.
- **`HEALTHCHECK`** para que el orquestador (Docker, Compose, Azure Container
  Apps) sepa si el contenedor está realmente sano, no solo "corriendo".
- **Variables de entorno de higiene**: `PYTHONDONTWRITEBYTECODE`,
  `PYTHONUNBUFFERED`, `PIP_NO_CACHE_DIR`.
- **`.dockerignore`** para no enviar `.venv/`, `.git/`, tests ni cachés al
  contexto de build (build más rápido y capas más limpias).
- **Orden de capas pensado para el cache**: se copian primero
  `pyproject.toml`/`README.md`/`src` (lo que cambia con el código), evitando
  invalidar capas de dependencias del sistema en cada cambio de línea de código.

### 1.3 Pipelines en GitHub Actions / Azure DevOps

Se revisa la automatización de las validaciones que antes se hacían a mano:
*lint* → *type-check* → *tests* → *build* → *push*. El objetivo es que **nada
llegue a `main` o a producción sin pasar por las mismas puertas de calidad**,
de forma idéntica en la laptop de cualquier desarrollador y en el servidor de
CI. En este módulo se implementa con **GitHub Actions**
(`.github/workflows/ci.yml`), con jobs encadenados vía `needs:` y una matriz
de versiones de Python para los tests. El mismo pipeline se podría expresar en
Azure DevOps con `stages`/`jobs`/`steps` en un `azure-pipelines.yml`
equivalente (se explica el mapeo en la sección 3.3).

### 1.4 Despliegue en Azure (App Service, Container Apps, Functions)

Se revisa **a qué servicio de Azure llevar la imagen ya construida**, y por
qué elegir uno u otro:

| Servicio | Cuándo usarlo | Notas para esta Orders API |
|---|---|---|
| **App Service (Web App for Containers)** | Servicio web "clásico", siempre encendido, con dominio y TLS gestionados. | Apunta directo a la imagen en el registry; soporta *deployment slots* para *blue/green*. |
| **Container Apps** | Microservicios, necesita *scale-to-zero*, *revisions*, tráfico dividido, KEDA/eventos. | Encaja mejor con esta API stateless: escala a 0 en tráfico bajo y factura por uso real. |
| **Functions** | Cargas orientadas a eventos/cron, no un servidor HTTP siempre vivo. | No es el mejor fit aquí porque la API mantiene un proceso FastAPI/uvicorn de larga duración; se usaría si un endpoint se reescribiera como función aislada. |

Este módulo se centra en **empaquetar y automatizar** hasta dejar la imagen
lista en el *registry*; el laboratorio no exige el despliegue final a Azure,
pero el pipeline queda preparado para añadir un job de `azure/webapps-deploy`
o `az containerapp update` apuntando a la imagen recién publicada (ver
sección 3.4).

---

## 2. Por qué deben cumplirse los objetivos señalados

**Objetivo 1 — Empaquetar, contenerizar y automatizar pipelines.**
Sin este objetivo, cada despliegue depende de pasos manuales ("en mi máquina
funciona"), sin garantía de que el código que se probó sea el mismo que se
despliega. Empaquetar (wheel) + contenerizar (Docker) + automatizar (CI)
convierte el despliegue en un proceso determinista: el mismo artefacto que
pasó lint/type-check/tests es, bit a bit, el que se ejecuta en producción.

**Objetivo 2 — Publicar artefactos reproducibles.**
Un artefacto reproducible (wheel versionado + imagen Docker con tag
inmutable, p. ej. el SHA del commit) permite:

- **Trazabilidad**: saber exactamente qué código corre en producción.
- **Rollback confiable**: volver a un tag anterior sin reconstruir nada.
- **Auditoría y seguridad**: escanear una imagen concreta, no "lo último".

Sin reproducibilidad, ni el versionado semántico ni las políticas de
seguridad tienen sentido, porque no hay garantía de que "v1.2.3" sea siempre
el mismo binario.

---

## 3. Descripción de la solución y cómo se ejecuta

### 3.1 Estructura del proyecto

```
modulo17_empaquetado_cicd/
├── pyproject.toml            # metadatos, build-system (hatchling), ruff, mypy, pytest
├── README.md                 # este documento
├── requirements-dev.txt      # pines exactos del entorno de desarrollo validado
├── Dockerfile                # build multistage (builder -> runtime)
├── .dockerignore
├── .gitignore
├── src/
│   └── orders_api/
│       ├── __init__.py       # expone create_app() y __version__
│       ├── _version.py       # única fuente de verdad de la versión
│       ├── main.py           # factory de FastAPI + entry point `orders-api`
│       ├── models.py         # Pydantic: OrderCreate, Order, HealthResponse
│       ├── repository.py     # repositorio en memoria (CRUD simple)
│       └── routes.py         # router /orders (POST, GET, GET/{id}, DELETE)
├── tests/
│   └── test_api.py           # pytest + TestClient (6 tests, 90% cobertura)
└── .github/workflows/ci.yml  # pipeline: lint -> typecheck -> test -> build/docker
```

> Nota: el dominio "Orders" se mantiene deliberadamente simple (repositorio en
> memoria, sin capas de Clean Architecture) porque el foco de este módulo es
> el empaquetado y el pipeline, no el diseño interno — eso ya se cubrió en el
> Módulo 16.

### 3.2 Laboratorio — Generar el wheel

```bash
python3 -m venv .venv
source .venv/bin/activate          # En Windows: .venv\Scripts\activate
pip install -e ".[dev]"            # instala el paquete + herramientas dev

# Calidad antes de empaquetar (igual que hace el CI):
ruff check src tests               # lint
mypy src                           # type-check estricto
pytest                             # tests + cobertura

# Construcción del wheel:
python -m build --wheel
ls dist/                           # orders_api-0.1.0-py3-none-any.whl
```

Validación de que el wheel es autocontenido (instalable en un entorno limpio,
sin el repo ni las dependencias de dev):

```bash
python3 -m venv /tmp/wheeltest && source /tmp/wheeltest/bin/activate
pip install dist/orders_api-0.1.0-py3-none-any.whl
orders-api &                       # levanta uvicorn en :8000 (entry point del pyproject.toml)
curl http://127.0.0.1:8000/health  # {"status":"ok","version":"0.1.0"}
```

*(Este flujo se ejecutó de extremo a extremo durante el desarrollo de este
módulo: lint, type-check y los 6 tests pasan con 90% de cobertura; el wheel
se instaló en un venv limpio y el servicio respondió correctamente en
`/health` y `/orders`.)*

Para publicar el wheel a PyPI o a un índice interno:

```bash
pip install twine
twine upload dist/*                       # PyPI público
twine upload --repository-url https://<indice-interno>/simple/ dist/*
```

En el pipeline (sección 3.4) esto se automatiza con `pypa/gh-action-pypi-publish`
usando *Trusted Publishing* (OIDC), sin guardar tokens en secretos.

### 3.3 Laboratorio — Dockerfile multistage para FastAPI

```bash
docker build -t orders-api:local .
docker run --rm -p 8000:8000 orders-api:local
curl http://localhost:8000/health
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{"customer":"Marcos","item":"Teclado","quantity":2,"unit_price":45.5}'
```

> **Nota de validación:** el `Dockerfile` se revisó línea por línea siguiendo
> las buenas prácticas de la sección 1.2 (multistage, usuario no root,
> healthcheck, `.dockerignore`, orden de capas) y usa exactamente el mismo
> comando de build (`python -m build --wheel`) que ya se validó en la
> sección 3.2. El entorno de este sandbox no tiene acceso al daemon de
> Docker ni a Docker Hub (solo a PyPI/npm/GitHub por política de red), así
> que el `docker build` real debe ejecutarse en tu máquina o en el runner de
> CI — el workflow de la sección siguiente lo hace automáticamente en cada push.

**Mapeo a Azure DevOps**, para quien prefiera esa plataforma en vez de GitHub
Actions: cada `job` de `ci.yml` equivale a un `job` dentro de un `stage` de
`azure-pipelines.yml`; `actions/setup-python` equivale a la tarea
`UsePythonVersion@0`; `docker/build-push-action` equivale a la tarea
`Docker@2` con `command: buildAndPush`; y `secrets.GITHUB_TOKEN` equivale a
una *service connection* de Azure DevOps hacia el registry.

### 3.4 Laboratorio — Workflow de CI (lint, type-check, tests, build) y push a registry

El pipeline vive en `.github/workflows/ci.yml` y se dispara en cada `push` a
`main`, en tags `v*.*.*` y en cada Pull Request. Jobs, en orden de
dependencia (`needs:`):

1. **`lint`** → `ruff check src tests`
2. **`typecheck`** → `mypy src` (modo estricto)
3. **`test`** → `pytest` con cobertura, en matriz Python 3.11 / 3.12
4. **`build`** → construye el wheel (`python -m build --wheel`), lo sube como
   *artifact* del workflow, y si el push es un tag `vX.Y.Z`, lo publica a
   PyPI vía Trusted Publishing.
5. **`docker`** → build multistage de la imagen (usa cache de capas de GitHub
   Actions), y hace `push` a **GHCR** (`ghcr.io`) con tags automáticos: rama,
   versión semántica en tags, y SHA corto del commit. En Pull Requests solo
   valida que la imagen compile (no hace `push`), para no publicar imágenes
   de código no revisado.

Cómo se ejecuta (en local, simulando lo que hace el CI paso a paso):

```bash
pip install -e ".[dev]"
ruff check src tests && mypy src && pytest
python -m build --wheel
docker build -t ghcr.io/<usuario>/<repo>/orders-api:local .
```

Para conectarlo con Azure como destino final del despliegue, se añadiría un
job adicional después de `docker`, por ejemplo:

```yaml
  deploy-azure:
    runs-on: ubuntu-latest
    needs: docker
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: azure/login@v2
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}
      - uses: azure/container-apps-deploy-action@v2
        with:
          imageToDeploy: ghcr.io/${{ github.repository }}/orders-api:${{ github.sha }}
          containerAppName: orders-api
          resourceGroup: rg-orders-api
```

(Se documenta como extensión porque el laboratorio pedido cubre hasta el
push al registry; el despliegue efectivo a Azure requiere credenciales y
recursos reales que no existen en este entorno de desarrollo.)

---

## 4. Resumen de validación realizada

| Paso | Resultado |
|---|---|
| `ruff check src tests` | ✅ Sin errores |
| `mypy src` (strict) | ✅ Sin errores |
| `pytest` | ✅ 6/6 tests, 90% cobertura |
| `python -m build --wheel` | ✅ `orders_api-0.1.0-py3-none-any.whl` generado |
| Instalación del wheel en venv limpio | ✅ Import y arranque correctos |
| Servicio real (`orders-api` / uvicorn) | ✅ `/health` y `POST /orders` responden correctamente |
| `Dockerfile` | ✅ Revisado contra checklist de buenas prácticas (no se pudo ejecutar `docker build` por falta de daemon Docker en este sandbox) |
| `ci.yml` | ✅ Validado por inspección (sintaxis YAML y orden de jobs); requiere ejecutarse en GitHub real para ver el resultado en Actions |
