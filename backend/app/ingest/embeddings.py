"""Geração de embeddings para procedimentos SIGTAP via OpenAI.

Uso:
    cd backend
    PYTHONPATH=. python -m app.ingest.embeddings --competencia 202603

Flags:
    --competencia AAAAMM  (obrigatório)
    --force               Re-indexa procedimentos que já possuem embedding.
                          Padrão: pula procedimentos já indexados.

Fluxo:
    1. Lê sigtap_procedimentos JOIN sigtap_descricoes JOIN hierarquia (grupo/subgrupo/forma_org).
    2. Filtra procedimentos sem embedding (a menos que --force).
    3. Constrói embedding_text: grupo | subgrupo | forma_org | no_procedimento | ds_procedimento
    4. Chama OpenAI text-embedding-3-small em batches de 100.
    5. UPSERT em embeddings_procedimentos (commit por batch — permite retomar sem re-chamar API).
"""

import argparse
import asyncio
import sys

from openai import AsyncOpenAI
from sqlalchemy import text

from app.config import settings
from app.db import async_session

EMBEDDING_MODEL = "text-embedding-3-small"
BATCH_SIZE = 100

_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


def _build_embedding_text(
    no_grupo: str | None,
    no_sub_grupo: str | None,
    no_forma_organizacao: str | None,
    no_procedimento: str,
    ds_procedimento: str | None,
) -> str:
    parts = [
        p.strip()
        for p in [no_grupo, no_sub_grupo, no_forma_organizacao, no_procedimento, ds_procedimento]
        if p and p.strip()
    ]
    return " | ".join(parts)


async def main(competencia: str, force: bool) -> None:
    print(f"Gerando embeddings — competência: {competencia}, force={force}")

    async with async_session() as session:
        # 1. Busca todos os procedimentos com hierarquia para a competência
        fetch_sql = text("""
            SELECT
                p.co_procedimento,
                p.no_procedimento,
                p.dt_competencia,
                d.ds_procedimento,
                g.no_grupo,
                s.no_sub_grupo,
                f.no_forma_organizacao
            FROM sigtap_procedimentos p
            LEFT JOIN sigtap_descricoes d
                ON d.co_procedimento = p.co_procedimento
               AND d.dt_competencia = p.dt_competencia
            LEFT JOIN sigtap_grupos g
                ON g.co_grupo = SUBSTRING(p.co_procedimento, 1, 2)
               AND g.dt_competencia = p.dt_competencia
            LEFT JOIN sigtap_subgrupos s
                ON s.co_sub_grupo = SUBSTRING(p.co_procedimento, 3, 2)
               AND s.dt_competencia = p.dt_competencia
            LEFT JOIN sigtap_formas_organizacao f
                ON f.co_forma_organizacao = SUBSTRING(p.co_procedimento, 5, 2)
               AND f.dt_competencia = p.dt_competencia
            WHERE p.dt_competencia = :competencia
            ORDER BY p.co_procedimento
        """)
        result = await session.execute(fetch_sql, {"competencia": competencia})
        rows = result.fetchall()

        if not rows:
            print(f"Nenhum procedimento encontrado para competência {competencia}.", file=sys.stderr)
            return

        print(f"  {len(rows)} procedimentos encontrados.")

        # 2. Identifica procedimentos já indexados (pula se não --force)
        skip_set: set[str] = set()
        if not force:
            existing_sql = text("""
                SELECT co_procedimento
                FROM embeddings_procedimentos
                WHERE dt_competencia = :competencia AND embedding IS NOT NULL
            """)
            existing_result = await session.execute(existing_sql, {"competencia": competencia})
            skip_set = {r[0] for r in existing_result.fetchall()}
            if skip_set:
                print(
                    f"  {len(skip_set)} procedimentos já indexados — pulando "
                    f"(use --force para re-indexar)."
                )

        # 3. Filtra lista de trabalho
        todo = [r for r in rows if r.co_procedimento not in skip_set]
        print(f"  {len(todo)} procedimentos a indexar.")

        if not todo:
            print("Nada a fazer.")
            return

        # 4. Processa em batches de BATCH_SIZE
        total_batches = (len(todo) + BATCH_SIZE - 1) // BATCH_SIZE
        total_done = 0

        for batch_num, i in enumerate(range(0, len(todo), BATCH_SIZE), start=1):
            batch = todo[i : i + BATCH_SIZE]

            # Monta textos para embedding
            texts = [
                _build_embedding_text(
                    r.no_grupo,
                    r.no_sub_grupo,
                    r.no_forma_organizacao,
                    r.no_procedimento,
                    r.ds_procedimento,
                )
                for r in batch
            ]

            # Chama OpenAI
            try:
                response = await _client.embeddings.create(
                    model=EMBEDDING_MODEL,
                    input=texts,
                )
            except Exception as exc:
                print(f"  [ERRO] OpenAI batch {batch_num}: {exc}", file=sys.stderr)
                raise

            # Prepara linhas para UPSERT — embedding como string para cast ::vector
            upsert_rows = [
                {
                    "co_procedimento": batch[j].co_procedimento,
                    "dt_competencia": batch[j].dt_competencia,
                    "embedding_text": texts[j],
                    "embedding_str": "[" + ",".join(str(x) for x in response.data[j].embedding) + "]",
                }
                for j in range(len(batch))
            ]

            upsert_sql = text("""
                INSERT INTO embeddings_procedimentos
                    (co_procedimento, dt_competencia, embedding_text, embedding)
                VALUES
                    (:co_procedimento, :dt_competencia, :embedding_text, CAST(:embedding_str AS vector))
                ON CONFLICT (co_procedimento, dt_competencia)
                DO UPDATE SET
                    embedding_text = EXCLUDED.embedding_text,
                    embedding = EXCLUDED.embedding
            """)

            for row in upsert_rows:
                await session.execute(upsert_sql, row)
            await session.commit()

            total_done += len(batch)
            print(
                f"  Batch {batch_num}/{total_batches}: {len(batch)} embeddings gerados "
                f"(total: {total_done}/{len(todo)})"
            )

    print("Indexação concluída.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gera embeddings SIGTAP via OpenAI")
    parser.add_argument("--competencia", required=True, help="Competência AAAAMM (ex: 202603)")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-indexa procedimentos já indexados",
    )
    args = parser.parse_args()
    asyncio.run(main(args.competencia, args.force))
