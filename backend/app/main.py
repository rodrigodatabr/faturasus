"""FastAPI app — lifespan, CORS e routers."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.db import engine
import app.models  # noqa: F401 — registra todos os models em Base.metadata
from app.routers import busca, health, transcricao

logger = logging.getLogger("faturasus")


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
