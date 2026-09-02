# ============================================================================
# Dockerfile — Módulo 19: Hardening de contenedores y del runtime
# ----------------------------------------------------------------------------
# Prácticas aplicadas (ver detalle en README):
#   1. Build multi-stage: el compilador/toolchain no viaja a la imagen final.
#   2. Imagen base "slim" oficial, con el mismo Python usado en desarrollo.
#   3. Usuario NO-root dedicado ("appuser") ejecuta la aplicación.
#   4. Sistema de archivos de solo lectura en runtime (ver docker-compose.yml
#      con read_only: true) + /tmp como tmpfs explícito.
#   5. Sin gestor de paquetes del SO innecesario en la imagen final
#      (apt se usa solo en el stage de build, si hiciera falta).
#   6. HEALTHCHECK para que el orquestador detecte contenedores no sanos.
#   7. Variables de entorno de Python endurecidas (no .pyc, no buffering).
#   8. Ningún secreto se copia ni se hornea (`COPY`/`ARG`) en la imagen:
#      se inyectan siempre en runtime vía variables de entorno.
#   9. `.dockerignore` evita que .env, .git, tests, etc. entren al contexto.
# ============================================================================

# ---------- Stage 1: builder --------------------------------------------------
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Solo copiamos el manifiesto de dependencias primero (cache de capas de Docker).
COPY requirements.txt .

# Instalamos las dependencias en un prefix aislado que luego se copia
# al stage final, sin arrastrar cabeceras de compilación ni cachés de apt.
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------- Stage 2: runtime ---------------------------------------------------
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/usr/local/bin:$PATH"

# Usuario y grupo NO privilegiados. UID/GID fijos y > 10000 para no
# colisionar con usuarios del sistema y facilitar políticas de
# "runAsNonRoot" / "runAsUser" en Kubernetes.
RUN groupadd --gid 10001 appgroup \
    && useradd --uid 10001 --gid appgroup --shell /usr/sbin/nologin \
       --home-dir /app --no-create-home appuser

WORKDIR /app

# Copiamos únicamente las dependencias ya instaladas desde el builder.
COPY --from=builder /install /usr/local

# Copiamos solo el código fuente necesario (respeta .dockerignore).
COPY --chown=appuser:appgroup src/ ./src/

# Directorio para el usuario no-root si la app necesita escribir algo
# puntual (logs de archivo, cache); el resto del filesystem será read-only
# (ver docker-compose.yml: read_only: true + tmpfs en /tmp).
RUN mkdir -p /app/tmp && chown appuser:appgroup /app/tmp

# Cambiamos a usuario no-root ANTES de arrancar el proceso.
USER appuser:appgroup

EXPOSE 8000

# Healthcheck: el orquestador puede reiniciar el contenedor si deja de
# responder. Usa el propio Python del venv, sin curl/wget adicionales
# (menos paquetes = menos superficie de ataque).
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request,sys; \
    sys.exit(0) if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).status == 200 else sys.exit(1)"

# Sin shell de entrada (`exec form`), sin privilegios extendidos, un solo
# proceso por contenedor (principio de responsabilidad única a nivel infra).
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
