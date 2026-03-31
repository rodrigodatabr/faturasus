"""Router POST /classificar — classificação de procedimentos SIGTAP via pgvector + Haiku."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.services.classificacao import classificar_procedimento

router = APIRouter(tags=["classificacao"])


class ClassificarRequest(BaseModel):
    texto: str
    competencia: str  # AAAAMM


class ClassificarResponse(BaseModel):
    co_procedimento: str
    no_procedimento: str
    vl_total: int  # centavos


@router.post("/classificar", response_model=ClassificarResponse)
async def classificar(
    body: ClassificarRequest,
    session: AsyncSession = Depends(get_session),
) -> ClassificarResponse:
    """Recebe texto transcrito e retorna o procedimento SIGTAP mais adequado.

    Pipeline: embedding OpenAI → pgvector top-15 → Claude Haiku escolhe o mais adequado.
    """
    resultado = await classificar_procedimento(body.texto, body.competencia, session)
    return ClassificarResponse(**resultado)
