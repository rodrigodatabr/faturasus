"""Fixtures compartilhadas para os testes do backend FaturaSUS."""

import os
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# Carrega .env do diretório backend (um nível acima de tests/)
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(_env_path)

# Usa DATABASE_URL do ambiente (Railway) ou DATABASE_PUBLIC_URL como fallback
DATABASE_URL = os.environ.get("DATABASE_URL") or os.environ.get("DATABASE_PUBLIC_URL")


@pytest_asyncio.fixture
async def db_session():
    """AsyncSession por teste — evita problemas de event loop entre testes.

    Escopo function (padrão): cada teste recebe uma sessão fresca.
    Testes que inserem dados devem limpar na cláusula finally.
    """
    if not DATABASE_URL:
        pytest.skip("DATABASE_URL não configurada — pulando testes de integração")

    engine = create_async_engine(DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    await engine.dispose()
