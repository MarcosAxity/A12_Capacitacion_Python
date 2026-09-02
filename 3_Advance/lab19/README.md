# Módulo 19 — Seguridad y Mantenimiento

Servicio FastAPI mínimo usado como laboratorio para aplicar prácticas de
seguridad y mantenimiento en un proyecto Python real: gestión de secretos,
auditoría de dependencias y hardening de contenedores.

Rol aplicado en esta entrega: Científico de Datos Senior + Data Engineer
Senior + Desarrollador de Python Senior — foco en que la solución sea
correcta, verificada de punta a punta y explicable, no solo "que corra".

---

## 1. Contenidos clave — qué se revisa y por qué existe cada uno

### 1.1 Gestión de secretos y configuración

Un "secreto" es cualquier dato que, si se filtra, compromete el sistema:
claves de firma, contraseñas de base de datos, API keys, tokens. El
problema clásico es que estos valores terminan hardcodeados en el código,
subidos por accidente a git, o impresos en un log de debug.

Lo que se revisa aquí:

- **Separación código/configuración** (principio de los [12-factor apps](https://12factor.net/config)):
  el código no cambia entre entornos, la configuración sí. Se implementa
  con `pydantic-settings`, que carga la config desde variables de entorno
  o un archivo `.env` local.
- **Tipado y validación de la configuración**: en vez de leer `os.environ`
  a mano (propenso a errores de tipeo, sin valores por defecto, sin
  validación), se define un modelo `Settings` tipado que valida al
  arrancar la aplicación.
- **Enmascarado de secretos en memoria y en logs**: los campos sensibles
  usan `SecretStr`, que oculta el valor real en `repr()`/`str()`/logs, y
  solo se revela explícitamente con `.get_secret_value()` cuando el
  código realmente necesita el valor crudo (por ejemplo, para abrir una
  conexión).
- **`.env` fuera de git**: el archivo con valores reales se excluye vía
  `.gitignore`; solo se versiona una plantilla `.env.example` sin datos
  sensibles.

### 1.2 Auditoría de dependencias: `pip-audit`, `safety`

Un proyecto Python moderno depende de decenas de paquetes de terceros, y
cada uno puede tener vulnerabilidades conocidas (CVEs) publicadas después
de que el proyecto fijó esa versión. Auditar dependencias significa
comparar automáticamente las versiones instaladas contra bases de datos
públicas de vulnerabilidades:

- **`pip-audit`** (mantenido por PyPA): compara `requirements.txt` /
  el entorno instalado contra la base [OSV](https://osv.dev/) y el feed de
  vulnerabilidades de PyPI. No requiere cuenta ni API key.
- **`safety`**: herramienta equivalente, orientada también a CI/CD, con
  una base de datos propia (requiere autenticación / API key en su
  versión actual para consultar la base completa).

Ambas se ejecutan como parte del laboratorio (ver sección 3) y se
documentan los hallazgos reales encontrados y cómo se resolvieron.

### 1.3 Actualizaciones (PEP 440) y compatibilidad

[PEP 440](https://peps.python.org/pep-0440/) define la sintaxis estándar
de versionado de paquetes Python. Entender sus operadores es lo que
permite decidir *cómo* fijar una dependencia sin romper el proyecto en la
próxima actualización:

| Especificador | Significado                                   | Cuándo usarlo |
|---|---|---|
| `==1.2.3`      | Versión exacta                                | Reproducibilidad total (builds de producción) |
| `~=1.2.3`      | "Compatible release": `>=1.2.3, ==1.2.*`      | Deja pasar parches de seguridad automáticamente |
| `>=1.2,<2.0`   | Rango explícito                               | Cuando se quiere permitir MINOR nuevos, no MAJOR |
| `!=1.4.0`      | Excluye una versión puntual (con bug conocido)| Bloquear una versión rota específica |

Este proyecto usa `~=` en `requirements.txt`, documentado inline en el
propio archivo, y explica por qué se **fijó una dependencia transitiva**
(`starlette`) de forma explícita tras la auditoría (ver sección 3.1).

### 1.4 Hardening de contenedores y del runtime

"Hardening" = reducir la superficie de ataque de todo lo que rodea al
código: la imagen Docker, el usuario que ejecuta el proceso, los permisos
del filesystem, las capabilities del kernel expuestas al contenedor. Se
aplica en `Dockerfile` y `docker-compose.yml` (detalle en sección 4).

---

## 2. Objetivos — por qué son innegociables

### Objetivo 1: Proteger secretos y reducir superficie de riesgo

Un secreto filtrado (en un log, en un commit de git, en un traceback de
error 500 expuesto al cliente) suele ser el punto de entrada más común en
incidentes reales de seguridad — más que exploits sofisticados. Reducir
"superficie de riesgo" significa: menos lugares donde un secreto puede
aparecer en texto plano, menos permisos de los estrictamente necesarios
(usuario no-root, filesystem de solo lectura, capabilities mínimas), y
menos código de terceros sin auditar corriendo con privilegios.

Este objetivo se cumple aquí con: `SecretStr` en toda la configuración
sensible, un endpoint `/config` que expone la config activa siempre
enmascarada, y un contenedor que corre sin privilegios de root.

### Objetivo 2: Mantener dependencias seguras y actualizadas

El código propio no es la única superficie de ataque: la mayoría de un
proyecto real es código de terceros (frameworks, librerías). Un CVE
público sobre una dependencia es, en la práctica, una vulnerabilidad
conocida y explotable contra cualquiera que no haya actualizado. Auditar
de forma recurrente (no solo una vez) y automatizada (CI) es lo que
convierte esto en un proceso sostenible en vez de un chequeo manual que
se olvida.

Este objetivo se cumple aquí con: `pip-audit`/`safety` integrados como
scripts y como job de CI (incluso con corrida programada semanal,
independiente de si hay cambios de código), y con el hallazgo real de 9
CVEs corregido durante la construcción de este mismo laboratorio (sección
3.1).

---

## 3. Laboratorio — qué se construyó y cómo se ejecuta

### 3.0 Estructura del proyecto

```
modulo19_seguridad_mantenimiento/
├── README.md
├── requirements.txt              # dependencias de producción (PEP 440)
├── requirements-dev.txt          # + testing y auditoría
├── pytest.ini
├── .env.example                  # plantilla sin secretos reales
├── .gitignore
├── .dockerignore
├── Dockerfile                    # multi-stage, hardened
├── docker-compose.yml            # perfil de ejecución endurecido
├── src/
│   ├── config.py                 # Settings con pydantic-settings
│   ├── security_utils.py         # redacción de secretos en logs
│   └── main.py                   # API FastAPI de demostración
├── tests/
│   ├── test_config.py
│   ├── test_security_utils.py
│   └── test_main.py
├── scripts/
│   ├── audit.sh                  # corre pip-audit + safety
│   └── run.sh                    # levanta la app localmente
├── audit-reports/                # reportes generados (JSON) — ver 3.1
└── .github/workflows/ci.yml      # tests + auditoría + build docker en CI
```

### 3.1 Integrar `pydantic-settings`

Implementado en `src/config.py`. Puntos clave del diseño:

- `Settings(BaseSettings)` con `env_prefix="APP_"`: todas las variables de
  entorno relevantes empiezan con `APP_` (evita colisión con variables de
  entorno de otros procesos del sistema).
- Precedencia: **variable de entorno del sistema > archivo `.env` >
  default**. En producción, el valor real siempre debe venir de una
  variable de entorno inyectada por el orquestador/gestor de secretos,
  nunca del `.env` (que ni siquiera debería existir en ese entorno).
- `secret_key` y `database_url` son **obligatorios** (`...` como default):
  si faltan, la app **no arranca** (`ValidationError` al instanciar
  `Settings()`), en vez de fallar más tarde con un error confuso.
- Validadores custom: `secret_key` debe tener ≥16 caracteres;
  `database_url` no puede estar vacío; y una regla cruzada
  (`model_post_init`) prohíbe `debug=True` si `environment="production"`.
- `safe_dict()`: serializa la config para logging con los campos
  `SecretStr` enmascarados como `**********`.

**Cómo probarlo:**

```bash
cp .env.example .env
# editar .env con un secret_key real (>=16 caracteres) y tu database_url
./scripts/run.sh
# GET http://localhost:8000/config   -> secretos enmascarados
# GET http://localhost:8000/whoami   -> usa el secreto sin exponerlo
```

Validado en este entorno: `pytest tests/test_config.py tests/test_main.py`
— **8 + 3 tests en verde** cubriendo carga válida, falta de secretos
obligatorios, secreto corto rechazado, enmascarado en `safe_dict()`,
regla `debug` vs `production`, y los tres endpoints de la API.

### 3.2 Ejecutar `pip-audit` / `safety` y resolver hallazgos

Este es un hallazgo **real**, no simulado, encontrado al construir este
mismo laboratorio:

**Antes** — con `fastapi~=0.115.14` (que resuelve `starlette==0.46.2`),
`pip-audit -r requirements.txt` reportó:

```
Found 9 known vulnerabilities in 1 package
```

Entre ellas: `CVE-2026-48710`/`GHSA-86qp-5c8j-p5mr` (bypass de
autenticación por inconsistencia al reconstruir la URL desde el header
`Host`), `CVE-2025-62727` (denegación de servicio por procesamiento
cuadrático de headers `Range` en `FileResponse`), y
`CVE-2026-48818`/`GHSA-wqp7-x3pw-xc5r` (SSRF vía rutas UNC en `StaticFiles`
en Windows), entre otras 6.

**Resolución aplicada:**

1. Se actualizó `fastapi` a `~=0.141.1` (versión reciente que soporta una
   línea de Starlette parcheada).
2. Se fijó explícitamente `starlette~=1.6.0` en `requirements.txt` — no
   por ser una dependencia directa, sino para que el resolver de pip
   **nunca** vuelva a instalar una versión vulnerable como transitiva,
   incluso si `fastapi` en el futuro relaja su rango permitido.
3. Se reinstaló el entorno y se re-auditó:

```
$ pip-audit -r requirements.txt
No known vulnerabilities found
```

Reporte completo (24 paquetes auditados, 0 vulnerabilidades) queda en
`audit-reports/pip-audit-report.json`, generado en este mismo proceso de
construcción del laboratorio.

**Sobre `safety`:** al ejecutar `safety check -r requirements.txt` en este
entorno de construcción, la herramienta requiere autenticarse contra su
plataforma (`safetycli.com`) para poder consultar su base de datos, y
falló con `InvalidCredentialError: Your authentication credential
'Failed authentication.' is invalid` por no tener una `SAFETY_API_KEY`
configurada ni acceso de red a ese dominio en este sandbox (ver
`audit-reports/safety-stderr.txt` con la traza real). Esto es esperado y
se documenta explícitamente porque es exactamente el tipo de fricción que
te vas a encontrar en un pipeline real: `safety` no es "cero-config" como
`pip-audit`. La solución queda lista para usarse en un entorno con
credenciales:

```bash
safety auth login          # una sola vez, interactivo
# o exportar SAFETY_API_KEY como secret en CI (ver .github/workflows/ci.yml)
./scripts/audit.sh
```

**Cómo re-ejecutar la auditoría completa:**

```bash
pip install -r requirements-dev.txt
./scripts/audit.sh
```

### 3.3 Docker sin root y permisos mínimos

Implementado en `Dockerfile` (build) y `docker-compose.yml` (runtime).
Medidas de hardening aplicadas, con su justificación:

| Medida | Dónde | Por qué |
|---|---|---|
| Build **multi-stage** | `Dockerfile` | El stage final no incluye herramientas de build ni caché de pip: menos superficie, imagen más chica |
| Usuario **no-root** (`appuser`, UID 10001) | `Dockerfile` (`USER`) + compose (`user:`) | Si el proceso es comprometido, el atacante no tiene privilegios de root dentro del contenedor |
| Filesystem raíz **read-only** | `docker-compose.yml` (`read_only: true`) | Un proceso comprometido no puede escribir/persistir malware en el propio contenedor |
| `tmpfs` explícito en `/tmp` y `/app/tmp` con `noexec,nosuid` | `docker-compose.yml` | Las únicas rutas escribibles son efímeras y no permiten ejecutar binarios ni set-uid |
| `cap_drop: ALL` + solo `NET_BIND_SERVICE` | `docker-compose.yml` | El contenedor pierde todas las capabilities de Linux salvo la mínima para bindear el puerto |
| `no-new-privileges:true` | `docker-compose.yml` | Bloquea escalamiento de privilegios vía binarios setuid/setgid |
| `pids_limit`, `mem_limit`, `cpus` | `docker-compose.yml` | Contiene el radio de explosión de un proceso descontrolado (fork bomb, memory leak) |
| Sin secretos en `COPY`/`ARG`/capas de imagen | `Dockerfile`, `.dockerignore` | Los secretos nunca quedan grabados en el historial de capas de la imagen (`docker history`) |
| `HEALTHCHECK` sin dependencias extra | `Dockerfile` | Usa el propio intérprete Python, no se instala `curl`/`wget` solo para esto (menos paquetes = menos CVEs potenciales) |

**Cómo ejecutarlo:**

```bash
docker compose up --build
curl http://localhost:8000/health
```

**Cómo verificar que NO corre como root** (lo mismo que valida el job
`docker-build` en CI):

```bash
docker run --rm modulo19-seguridad:latest python -c "import os; print(os.getuid())"
# Debe imprimir 10001, nunca 0
```

> Nota de entrega: la imagen no pudo construirse dentro de este sandbox de
> generación (no hay daemon de Docker disponible en este entorno), por lo
> que el `Dockerfile`/`docker-compose.yml` fueron validados por revisión
> estática línea a línea contra el checklist de hardening de la tabla
> anterior. El job `docker-build` en `.github/workflows/ci.yml` construye
> la imagen y verifica el UID no-root automáticamente en cada push.

---

## 4. Validación end-to-end realizada en esta entrega

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

pytest
# 20 passed — cobertura ~93% sobre src/

pip-audit -r requirements.txt
# No known vulnerabilities found (tras el fix de starlette)
```

## 5. Cómo levantar el proyecto (resumen rápido)

```bash
# 1. Configuración
cp .env.example .env   # y editar con un secret_key real

# 2. Local (sin Docker)
pip install -r requirements-dev.txt
pytest
./scripts/run.sh

# 3. Docker (hardened)
docker compose up --build

# 4. Auditoría de seguridad
./scripts/audit.sh
```
