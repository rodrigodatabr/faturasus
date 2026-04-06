"""Serviço de classificação de procedimentos SIGTAP: hybrid search (pgvector + substring) → Claude Haiku."""

import json
import logging
import unicodedata

import anthropic
from fastapi import HTTPException
from openai import AsyncOpenAI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

logger = logging.getLogger("faturasus")

EMBEDDING_MODEL = "text-embedding-3-small"
HAIKU_MODEL = "claude-haiku-4-5"
TOP_K = 30
# Threshold de distância coseno acima do qual ativamos o fallback substring.
# Distância coseno: 0 = idêntico, 2 = oposto. >0.35 indica confiança baixa.
DIST_THRESHOLD_FALLBACK = 0.35
# Comprimento mínimo de token para usar no fallback substring
MIN_TOKEN_LEN = 5
# Tamanho máximo da descrição do procedimento passada ao Haiku (chars)
DS_PROC_MAX_CHARS = 80

_openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
# Instanciado de forma lazy em _get_haiku() para garantir que a chave já foi carregada
_haiku: anthropic.AsyncAnthropic | None = None


def _get_haiku() -> anthropic.AsyncAnthropic:
    global _haiku
    if _haiku is None:
        _haiku = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _haiku


def _extrair_json(raw: str) -> str:
    """Extrai o primeiro objeto JSON da resposta, ignorando code fences e texto extra."""
    s = raw.strip()
    # Remove code fence se presente
    if s.startswith("```"):
        lines = s.splitlines()
        inner = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
        s = "\n".join(inner).strip()
    # Pega apenas o trecho entre o primeiro { e o } correspondente
    start = s.find("{")
    if start == -1:
        return s
    depth = 0
    for i, ch in enumerate(s[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return s[start : i + 1]
    return s[start:]


def _normalizar(texto: str) -> str:
    """Lowercase + remove acentos para comparação substring."""
    nfkd = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _tokens_relevantes(texto: str) -> list[str]:
    """Extrai tokens do texto para busca substring.

    Para cada token >= MIN_TOKEN_LEN: tenta o token original lowercase e o normalizado
    (sem acento). Para tokens longos (>= 9 chars), adiciona também um prefixo de 6 chars
    da forma normalizada — cobre casos onde o acento aparece na sílaba final
    (ex: "nebulização" → prefixo "nebuli" encontra "NEBULIZAÇÃO").
    """
    seen: set[str] = set()
    result: list[str] = []

    for raw in texto.lower().split():
        norm = _normalizar(raw)
        candidates = [raw, norm]
        if len(norm) >= 9:
            candidates.append(norm[:6])  # prefixo pré-acento
        for tok in candidates:
            if len(tok) >= MIN_TOKEN_LEN and tok not in seen:
                seen.add(tok)
                result.append(tok)
    return result


_SYSTEM_EXPAND = """\
Você é um especialista em terminologia médica e no sistema SIGTAP do SUS brasileiro.
Dado um texto coloquial ou com possíveis erros de transcrição de voz, reescreva-o
usando terminologia técnica médica compatível com os nomes de procedimentos do SIGTAP.

Regras:
- Se o texto já usa terminologia técnica SIGTAP, retorne-o com ajustes mínimos ou sem alteração.
- O PROCEDIMENTO clínico principal tem prioridade sobre a VIA DE ADMINISTRAÇÃO.
  "oral", "injetável", "via oral" descrevem rota — não são o procedimento em si.
  Ex: "quimioterapia oral" → "quimioterapia antineoplásica adultos" (não "medicamento via oral").
- Corrija erros fonéticos e mapeamentos de terminologia coloquial→SIGTAP:
  "papa nicolau" → "exame citopatológico colo utero rastreamento cervical"
  "gesso no braço" → "imobilização gessada fratura membro superior"
  "injeção no joelho" → "infiltração cavidade sinovial joelho"
  "injeção intra-articular" → "infiltração cavidade sinovial"
  "nebulização" ou "nebulizacao" → "inalação nebulização"
  "vacina" ou "vacinação" (qualquer tipo) → "administração imunoderivados"

Responda SOMENTE com JSON: {"query": "terminologia técnica aqui"}"""

_SYSTEM_CLASSIFY = """\
Você é um assistente especializado em classificação de procedimentos SIGTAP do SUS.
Escolha o procedimento mais adequado para a descrição clínica.

Regras:
- Para termos de triagem/rastreamento (ex: "Papa Nicolau", "preventivo"), prefira procedimentos
  de rastreamento (citopatológico) em vez de diagnóstico invasivo (biópsia).
- Quando a descrição se refere a uma TERAPIA (administração de medicamento, inalação terapêutica,
  infusão), prefira o procedimento terapêutico — não um procedimento de DIAGNÓSTICO POR IMAGEM
  que use o mesmo meio físico (ex: cintilografia por inalação é diagnóstico, não terapia).
- Quando a descrição descreve um ATO CLÍNICO (nebulizar, injetar, infiltrar, administrar,
  aplicar), prefira o procedimento que nomeia o ATO CLÍNICO (ex: "INALAÇÃO / NEBULIZAÇÃO",
  "INFILTRACAO DE SUBSTANCIAS EM CAVIDADE SINOVIAL") em vez de um MEDICAMENTO ou INSUMO
  utilizado nele. Medicamentos e insumos têm nomes com concentração ou forma farmacêutica
  (ex: "300MG/5ML", "SOLUÇÃO", "AMPOLA", "FRASCO", "COMPRIMIDO") — não são procedimentos.
- Quando a descrição descreve uma intervenção AMBULATORIAL SIMPLES (infiltração, injeção
  articular, punção), prefira o procedimento clínico ambulatorial em vez de procedimento
  CIRÚRGICO com terminologia similar. Ex: "RETIRADA DE CORPO ESTRANHO INTRA-ARTICULAR" é
  cirúrgico; "INFILTRACAO DE SUBSTANCIAS EM CAVIDADE SINOVIAL" é o ato ambulatorial.
- Considere tanto o texto original quanto a terminologia técnica expandida.
- Leia a descrição de cada candidato para distinguir procedimentos clinicamente similares.

Responda SOMENTE com JSON no formato: {"co_procedimento": "XXXXXXXXXX"}"""


async def _buscar_vetorial(
    query_vec_str: str,
    competencia: str,
    session: AsyncSession,
    limit: int,
) -> list[dict]:
    """Busca vetorial pgvector. Retorna lista com distancia e ds_procedimento."""
    # Vetor embutido diretamente no SQL — origem: API OpenAI, não input do usuário.
    # asyncpg não aceita ::vector como cast de parâmetro nomeado.
    search_sql = text(f"""
        SELECT
            e.co_procedimento,
            p.no_procedimento,
            p.vl_sa,
            p.vl_sp,
            LEFT(COALESCE(d.ds_procedimento, ''), {DS_PROC_MAX_CHARS}) AS ds_procedimento,
            (e.embedding <=> '{query_vec_str}'::vector) AS distancia
        FROM embeddings_procedimentos e
        JOIN sigtap_procedimentos p
            ON p.co_procedimento = e.co_procedimento
           AND p.dt_competencia = e.dt_competencia
        LEFT JOIN sigtap_descricoes d
            ON d.co_procedimento = e.co_procedimento
           AND d.dt_competencia = e.dt_competencia
        WHERE e.dt_competencia = :competencia
          AND e.embedding IS NOT NULL
        ORDER BY distancia ASC
        LIMIT :limit
    """)
    result = await session.execute(search_sql, {"competencia": competencia, "limit": limit})
    return [
        {
            "co_procedimento": r.co_procedimento,
            "no_procedimento": r.no_procedimento,
            "vl_sa": r.vl_sa,
            "vl_sp": r.vl_sp,
            "ds_procedimento": r.ds_procedimento or "",
            "distancia": r.distancia,
        }
        for r in result.fetchall()
    ]


async def _buscar_substring(
    termo: str,
    competencia: str,
    session: AsyncSession,
    limit: int,
) -> list[dict]:
    """Busca por substring em no_procedimento (PostgreSQL nativo, sem extensão).

    Roda duas queries em paralelo: uma com o termo normalizado (sem acento) e outra com o
    termo em lowercase preservando acentos. Necessário porque LOWER() no PostgreSQL preserva
    acentos, então 'inalacao' não bate com 'inalação / nebulização'.
    """
    termo_norm = _normalizar(termo)      # sem acento, para nomes sem acento (ex: INALACAO)
    termo_lower = termo.lower()          # com acento, para nomes com acento (ex: INALAÇÃO)

    substr_sql = text("""
        SELECT
            p.co_procedimento,
            p.no_procedimento,
            p.vl_sa,
            p.vl_sp,
            LEFT(COALESCE(d.ds_procedimento, ''), :ds_max) AS ds_procedimento
        FROM sigtap_procedimentos p
        LEFT JOIN sigtap_descricoes d
            ON d.co_procedimento = p.co_procedimento
           AND d.dt_competencia = p.dt_competencia
        WHERE p.dt_competencia = :competencia
          AND (
              LOWER(p.no_procedimento) LIKE '%' || :termo_norm || '%'
              OR LOWER(p.no_procedimento) LIKE '%' || :termo_lower || '%'
          )
        LIMIT :limit
    """)
    result = await session.execute(
        substr_sql,
        {
            "competencia": competencia,
            "termo_norm": termo_norm,
            "termo_lower": termo_lower,
            "limit": limit,
            "ds_max": DS_PROC_MAX_CHARS,
        },
    )
    return [
        {
            "co_procedimento": r.co_procedimento,
            "no_procedimento": r.no_procedimento,
            "vl_sa": r.vl_sa,
            "vl_sp": r.vl_sp,
            "ds_procedimento": r.ds_procedimento or "",
            "distancia": None,
        }
        for r in result.fetchall()
    ]


def _rrf_merge(vec_results: list[dict], sub_results: list[dict], k: int = 60) -> list[dict]:
    """Combina dois rankings via Reciprocal Rank Fusion. Retorna lista sem duplicatas."""
    scores: dict[str, float] = {}
    by_code: dict[str, dict] = {}

    for rank, item in enumerate(vec_results):
        code = item["co_procedimento"]
        scores[code] = scores.get(code, 0.0) + 1.0 / (k + rank + 1)
        by_code[code] = item

    for rank, item in enumerate(sub_results):
        code = item["co_procedimento"]
        scores[code] = scores.get(code, 0.0) + 1.0 / (k + rank + 1)
        if code not in by_code:
            by_code[code] = item

    ordenados = sorted(scores.keys(), key=lambda c: scores[c], reverse=True)
    return [by_code[c] for c in ordenados]


async def _buscar_candidatos_hybrid(
    texto: str,
    query_expandida: str,
    competencia: str,
    session: AsyncSession,
) -> list[dict]:
    """Hybrid search: pgvector + fallback substring com RRF quando confiança é baixa."""
    try:
        embedding_response = await _openai.embeddings.create(
            model=EMBEDDING_MODEL,
            input=[query_expandida],
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Erro ao gerar embedding: {exc}") from exc

    query_vec = embedding_response.data[0].embedding
    query_vec_str = "[" + ",".join(str(x) for x in query_vec) + "]"

    try:
        vec_results = await _buscar_vetorial(query_vec_str, competencia, session, limit=TOP_K)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro na busca vetorial: {exc}") from exc

    if not vec_results:
        return []

    top1_dist = vec_results[0]["distancia"]
    logger.info(
        "pgvector top-%d | query=%r | top-1: %s (dist=%.4f) | códigos: %s",
        len(vec_results),
        query_expandida,
        vec_results[0]["co_procedimento"],
        top1_dist,
        [c["co_procedimento"] for c in vec_results],
    )

    # Ativa fallback substring quando confiança da busca vetorial é baixa
    if top1_dist > DIST_THRESHOLD_FALLBACK:
        # Combina tokens da query expandida E do texto original para maior cobertura
        tokens_exp = _tokens_relevantes(query_expandida)
        tokens_orig = _tokens_relevantes(texto)
        # União preservando ordem: expandida primeiro, depois originais não duplicados
        tokens = tokens_exp + [t for t in tokens_orig if t not in tokens_exp]
        sub_results: list[dict] = []
        seen_codes: set[str] = set()
        for token in tokens[:4]:  # no máximo 4 tokens
            parcial = await _buscar_substring(token, competencia, session, limit=15)
            if parcial:
                logger.info("substring fallback | token=%r | %d resultados", token, len(parcial))
                for item in parcial:
                    if item["co_procedimento"] not in seen_codes:
                        sub_results.append(item)
                        seen_codes.add(item["co_procedimento"])

        if sub_results:
            merged = _rrf_merge(vec_results, sub_results)
            logger.info(
                "RRF merge: %d vetorial + %d substring → %d únicos",
                len(vec_results), len(sub_results), len(merged),
            )
            return merged[:TOP_K]

    return vec_results


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
    """Classifica o procedimento descrito em `texto` usando hybrid search + Claude Haiku.

    Pipeline: Haiku expande query → pgvector top-30 (+ substring fallback via RRF) → Haiku classifica.
    Retorna {"co_procedimento": str, "no_procedimento": str, "vl_total": int}.
    """
    if not settings.ANTHROPIC_API_KEY:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY não configurada")

    # Etapa 1: reformular texto coloquial para terminologia técnica SIGTAP
    query_busca = await _expandir_query(texto)

    # Etapa 2: hybrid search
    candidatos = await _buscar_candidatos_hybrid(texto, query_busca, competencia, session)

    if not candidatos:
        raise HTTPException(status_code=404, detail="Nenhum procedimento encontrado")

    # Monta lista numerada para o prompt — inclui descrição truncada para ajudar o Haiku
    linhas = []
    for i, c in enumerate(candidatos, 1):
        valor = _formatar_valor(c["vl_sa"], c["vl_sp"])
        desc = f" | {c['ds_procedimento']}" if c.get("ds_procedimento") else ""
        linhas.append(f"{i}. {c['co_procedimento']} — {c['no_procedimento']} ({valor}){desc}")
    lista_candidatos = "\n".join(linhas)

    user_message = (
        f"Texto original: {texto}\n"
        f"Terminologia técnica expandida: {query_busca}\n\n"
        f"Candidatos SIGTAP (competência {competencia}):\n{lista_candidatos}\n\n"
        "Escolha o co_procedimento mais adequado para a descrição clínica."
    )

    try:
        response = await _get_haiku().messages.create(
            model=HAIKU_MODEL,
            max_tokens=512,
            system=_SYSTEM_CLASSIFY,
            messages=[{"role": "user", "content": user_message}],
        )
        raw = response.content[0].text if response.content else ""
        logger.debug("Haiku classificação raw: %r", raw)
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
