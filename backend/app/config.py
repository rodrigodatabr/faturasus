"""Configuração centralizada via variáveis de ambiente."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: str | None = None  # Claude Haiku — obrigatório no passo 5
    CORS_ORIGINS: list[str] = [
        "https://faturasus-production.up.railway.app",
        "https://faturasus.up.railway.app",
        "http://localhost:5173",
    ]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
