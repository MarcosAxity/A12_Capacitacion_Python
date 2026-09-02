# syntax=docker/dockerfile:1.7

# ---------------------------------------------------------------------------
# Stage 1: builder
#   - Instala dependencias de build y construye el wheel del paquete.
#   - Esta capa NO viaja a la imagen final: solo aporta el .whl.
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /build

# Dependencias del sistema mínimas para compilar wheels de terceros si hiciera falta.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip build

# Copiamos solo lo necesario para construir el paquete (mejora cache de capas:
# si solo cambia el código de la app, no se reinstalan deps de build).
COPY pyproject.toml README.md ./
COPY src ./src

RUN python -m build --wheel --outdir /build/dist

# ---------------------------------------------------------------------------
# Stage 2: runtime
#   - Imagen final mínima: solo el intérprete, el wheel instalado y su
#     dependencia runtime. Sin compiladores, sin código fuente, sin cache de pip.
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

# Buenas prácticas: usuario no-root, sin bytecode cache, logs sin buffer.
RUN groupadd --gid 1000 app && useradd --uid 1000 --gid app --shell /bin/bash --create-home app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY --from=builder /build/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm -rf /tmp/*.whl

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)" || exit 1

# Se usa uvicorn directamente (en vez del entry point orders-api) para poder
# configurar workers/host/port desde el propio Dockerfile o vía CMD override.
CMD ["python", "-m", "uvicorn", "orders_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
