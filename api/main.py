from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import get_settings
from database import engine, Base
from routers.users_auth import router as auth_router
from routers.users import router as users_router
from routers.logs import router as logs_router
from routers.mixtures import router as mixtures_router
from routers.ingredients import router as ingredients_router

settings = get_settings()

# ── Create tables (use Alembic in production) ──────────────────────────────────
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="VegFuel API",
    description="Plant-powered nutrition tracker for athletes",
    version="1.0.0",
    docs_url="/docs" if settings.app_env == "development" else None,
    redoc_url="/redoc" if settings.app_env == "development" else None,
)

# ── CORS ───────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(logs_router)
app.include_router(mixtures_router)
app.include_router(ingredients_router)


# ── Health check ───────────────────────────────────────────────────────────────
@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok", "env": settings.app_env}


# ── Global error handler ───────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    if settings.app_env == "development":
        raise exc
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
