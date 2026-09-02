# syntax=docker/dockerfile:1

# ---------- Etapa 1: builder ----------
# Instala dependencias en un virtualenv aislado. Esta etapa incluye
# herramientas de compilación que NO queremos en la imagen final.
FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ---------- Etapa 2: runtime ----------
# Imagen final: solo el intérprete de Python, el virtualenv ya construido
# y el código fuente. Sin compiladores, sin cache de pip, usuario no-root.
FROM python:3.12-slim AS runtime

RUN groupadd --gid 1000 orders && \
    useradd --uid 1000 --gid orders --shell /bin/bash --create-home orders

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY --chown=orders:orders src ./src
COPY --chown=orders:orders alembic.ini ./alembic.ini
COPY --chown=orders:orders scripts/entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

USER orders

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["./entrypoint.sh"]
CMD ["uvicorn", "orders.infrastructure.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
