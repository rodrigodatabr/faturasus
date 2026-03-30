"""Router de busca semântica de procedimentos SIGTAP via pgvector."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from openai import AsyncOpenAI
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_session

router = APIRouter(prefix="/busca", tags=["busca"])

_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_LIMIT = 15
MAX_LIMIT = 50


class ProcedimentoResultado(BaseModel):
    co_procedimento: str
    no_procedimento: str
    vl_sa: int | None  # centavos — dividir por 100 para R$
    vl_sp: int | None  # centavos
    cbo_compativel: bool
    distancia: float


@router.get("/procedimentos", response_model=list[ProcedimentoResultado])
async def buscar_procedimentos(
    q: Annotated[
        str,
        Query(min_length=2, max_length=500, description="Texto livre da busca (transcrição ou digitado)"),
    ],
    competencia: Annotated[
        str,
        Query(min_length=6, max_length=6, pattern=r"^\d{6}$", description="Competência AAAAMM"),
    ],
    cbo: Annotated[
        str | None,
        Query(min_length=6, max_length=6, pattern=r"^\d{6}$", description="CBO do profissional (6 dígitos)"),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=MAX_LIMIT)] = DEFAULT_LIMIT,
    session: AsyncSession = Depends(get_session),
):
    """Busca semântica de procedimentos SIGTAP por similaridade de texto.

    Retorna até `limit` procedimentos ordenados por distância de cosseno ao vetor da query.
    Se `cbo` for informado, `cbo_compativel` indica se o procedimento está autorizado
    para aquela ocupação na tabela SIGTAP (anti-glosa CBO).
    """
    # 1. Gera embedding da query
    try:
        embedding_response = await _client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=[q],
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Erro ao gerar embedding: {exc}") from exc

    query_vec = embedding_response.data[0].embedding
    query_vec_str = "[" + ",".join(str(x) for x in query_vec) + "]"

    # 2. Busca pgvector por distância de cosseno
    # O vetor é embutido diretamente no SQL (origem: API OpenAI, não input do usuário)
    # porque asyncpg não aceita ::vector como cast de parâmetro nomeado.
    search_sql = text(f"""
        SELECT
            e.co_procedimento,
            p.no_procedimento,
            p.vl_sa,
            p.vl_sp,
            (e.embedding <=> '{query_vec_str}'::vector) AS distancia
        FROM embeddings_procedimentos e
        JOIN sigtap_procedimentos p
            ON p.co_procedimento = e.co_procedimento
           AND p.dt_competencia = e.dt_competencia
        WHERE e.dt_competencia = :competencia
          AND e.embedding IS NOT NULL
        ORDER BY distancia ASC
        LIMIT :limit
    """)

    try:
        result = await session.execute(
            search_sql,
            {"competencia": competencia, "limit": limit},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro na busca vetorial: {exc}") from exc

    rows = result.fetchall()

    if not rows:
        return []

    # 3. Verifica compatibilidade CBO em batch (1 query)
    cbo_compativel_set: set[str] = set()
    if cbo:
        codigos = [r.co_procedimento for r in rows]
        cbo_sql = text("""
            SELECT co_procedimento
            FROM sigtap_rl_proc_ocupacao
            WHERE co_procedimento = ANY(:codigos)
              AND co_ocupacao = :cbo
              AND dt_competencia = :competencia
        """)
        cbo_result = await session.execute(
            cbo_sql,
            {"codigos": codigos, "cbo": cbo, "competencia": competencia},
        )
        cbo_compativel_set = {r[0] for r in cbo_result.fetchall()}

    # 4. Monta resposta
    return [
        ProcedimentoResultado(
            co_procedimento=r.co_procedimento,
            no_procedimento=r.no_procedimento,
            vl_sa=r.vl_sa,
            vl_sp=r.vl_sp,
            cbo_compativel=(r.co_procedimento in cbo_compativel_set),
            distancia=float(r.distancia),
        )
        for r in rows
    ]
