"""FastAPI app — lifespan, CORS e routers."""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.config import settings
from app.db import engine
import app.models  # noqa: F401 — registra todos os models em Base.metadata
from app.routers import busca, classificacao, health, registros, transcricao

logger = logging.getLogger("faturasus")
logger.setLevel(logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: testa conexão com o banco
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Conexão com o banco OK")
    except Exception as exc:
        logger.error("Falha ao conectar no banco: %s", exc)
    yield
    # Shutdown: fecha pool de conexões
    await engine.dispose()


app = FastAPI(title="FaturaSUS API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(transcricao.router)
app.include_router(busca.router)
app.include_router(classificacao.router)
app.include_router(registros.router)

# Serve frontend/dist/ como static files (produção)
# Registrado após os routers para que /health, /busca/* e /transcricao
# sejam resolvidos pelo FastAPI antes do catch-all do SPA.
_DIST = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
)

if os.path.isdir(_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(_DIST, "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        candidate = os.path.join(_DIST, full_path)
        if os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(_DIST, "index.html"))
