"""Serviço de classificação de procedimentos SIGTAP: pgvector top-15 → Claude Haiku."""

import json
import logging

import anthropic
from fastapi import HTTPException
from openai import AsyncOpenAI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

logger = logging.getLogger("faturasus")

EMBEDDING_MODEL = "text-embedding-3-small"
HAIKU_MODEL = "claude-haiku-4-5"
TOP_K = 15

_openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
# Instanciado de forma lazy em _get_haiku() para garantir que a chave já foi carregada
_haiku: anthropic.AsyncAnthropic | None = None


def _get_haiku() -> anthropic.AsyncAnthropic:
    global _haiku
    if _haiku is None:
        _haiku = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _haiku


def _extrair_json(raw: str) -> str:
    """Remove markdown code fence se presente (Haiku às vezes envolve a resposta)."""
    s = raw.strip()
    if s.startswith("```"):
        lines = s.splitlines()
        inner = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
        return "\n".join(inner).strip()
    return s

_SYSTEM_EXPAND = """\
Você é um especialista em terminologia médica e no sistema SIGTAP do SUS brasileiro.
Dado um texto coloquial ou com possíveis erros de transcrição de voz, reescreva-o
usando terminologia técnica médica compatível com os nomes de procedimentos do SIGTAP.
Corrija erros fonéticos comuns (ex: "papa nicolau" → "coleta citopatológica colo útero",
"gesso no braço" → "imobilização gessada fratura membro superior").
Responda SOMENTE com JSON: {"query": "terminologia técnica aqui"}"""

_SYSTEM_CLASSIFY = """\
Você é um assistente especializado em classificação de procedimentos SIGTAP do SUS.
Escolha o procedimento mais adequado para a descrição clínica, considerando o texto
original e a lista de candidatos recuperados do SIGTAP.
Responda SOMENTE com JSON no formato: {"co_procedimento": "XXXXXXXXXX"}"""


async def _buscar_candidatos(
    texto: str,
    competencia: str,
    session: AsyncSession,
) -> list[dict]:
    """Retorna até TOP_K procedimentos por similaridade semântica (pgvector)."""
    try:
        embedding_response = await _openai.embeddings.create(
            model=EMBEDDING_MODEL,
            input=[texto],
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Erro ao gerar embedding: {exc}") from exc

    query_vec = embedding_response.data[0].embedding
    query_vec_str = "[" + ",".join(str(x) for x in query_vec) + "]"

    # Vetor embutido diretamente no SQL — origem: API OpenAI, não input do usuário.
    # asyncpg não aceita ::vector como cast de parâmetro nomeado.
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
            {"competencia": competencia, "limit": TOP_K},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro na busca vetorial: {exc}") from exc

    rows = result.fetchall()
    return [
        {
            "co_procedimento": r.co_procedimento,
            "no_procedimento": r.no_procedimento,
            "vl_sa": r.vl_sa,
            "vl_sp": r.vl_sp,
        }
        for r in rows
    ]


def _formatar_valor(vl_sa: int | None, vl_sp: int | None) -> str:
    centavos = vl_sa if vl_sa is not None else (vl_sp if vl_sp is not None else 0)
    return f"R$ {centavos / 100:.2f}"


async def _expandir_query(texto: str) -> str:
    """Reformula texto coloquial para terminologia SIGTAP via Haiku (query expansion)."""
    try:
        response = await _get_haiku().messages.create(
            model=HAIKU_MODEL,
            max_tokens=64,
            system=_SYSTEM_EXPAND,
            messages=[{"role": "user", "content": texto}],
        )
        raw = response.content[0].text if response.content else ""
        query_expandida = json.loads(_extrair_json(raw))["query"]
        logger.info("Query expansion: %r → %r", texto, query_expandida)
        return query_expandida
    except Exception as exc:
        logger.warning("Query expansion falhou (%s) — usando texto original", exc, exc_info=True)
        return texto


async def classificar_procedimento(
    texto: str,
    competencia: str,
    session: AsyncSession,
) -> dict:
    """Classifica o procedimento descrito em `texto` usando pgvector + Claude Haiku.

    Pipeline: Haiku expande query → embedding → pgvector top-15 → Haiku classifica.
    Retorna {"co_procedimento": str, "no_procedimento": str, "vl_total": int}.
    """
    if not settings.ANTHROPIC_API_KEY:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY não configurada")

    # Etapa 1: reformular texto coloquial para terminologia técnica SIGTAP
    query_busca = await _expandir_query(texto)

    candidatos = await _buscar_candidatos(query_busca, competencia, session)

    if not candidatos:
        raise HTTPException(status_code=404, detail="Nenhum procedimento encontrado")

    # Monta lista numerada para o prompt
    linhas = []
    for i, c in enumerate(candidatos, 1):
        valor = _formatar_valor(c["vl_sa"], c["vl_sp"])
        linhas.append(f"{i}. {c['co_procedimento']} — {c['no_procedimento']} ({valor})")
    lista_candidatos = "\n".join(linhas)

    user_message = (
        f"Texto original: {texto}\n\n"
        f"Candidatos SIGTAP (competência {competencia}):\n{lista_candidatos}\n\n"
        "Escolha o co_procedimento mais adequado para a descrição clínica."
    )

    try:
        response = await _get_haiku().messages.create(
            model=HAIKU_MODEL,
            max_tokens=64,
            system=_SYSTEM_CLASSIFY,
            messages=[{"role": "user", "content": user_message}],
        )
        raw = response.content[0].text
        escolha = json.loads(_extrair_json(raw))["co_procedimento"]
    except Exception as exc:
        logger.warning("Haiku falhou (%s) — usando candidatos[0] como fallback", exc)
        escolha = None

    # Valida que o código retornado está entre os candidatos
    codigos_validos = {c["co_procedimento"] for c in candidatos}
    if escolha not in codigos_validos:
        logger.warning("Haiku retornou código inválido %r — fallback para candidatos[0]", escolha)
        escolha = candidatos[0]["co_procedimento"]

    match = next(c for c in candidatos if c["co_procedimento"] == escolha)
    vl_total = match["vl_sa"] if match["vl_sa"] is not None else (match["vl_sp"] if match["vl_sp"] is not None else 0)

    return {
        "co_procedimento": match["co_procedimento"],
        "no_procedimento": match["no_procedimento"],
        "vl_total": vl_total,
    }
