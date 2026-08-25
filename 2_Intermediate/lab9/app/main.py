from app.core.config import settings
from app.middlewares import LoggingMiddleware
from app.routers import auth, items
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API de laboratorio: routers, esquemas Pydantic, JWT, middlewares y testing.",
    version="1.0.0",
)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Middleware propio ---
app.add_middleware(LoggingMiddleware)

# --- Routers ---
app.include_router(auth.router)
app.include_router(items.router)


@app.get("/health", tags=["health"], summary="Chequeo de salud del servicio")
async def health_check() -> dict:
    return {"status": "ok"}
