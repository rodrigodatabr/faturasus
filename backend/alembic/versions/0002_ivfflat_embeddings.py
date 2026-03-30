"""ivfflat index on embeddings_procedimentos

Revision ID: 0002_ivfflat_embeddings
Revises: b676997e0213
Create Date: 2026-03-30

Notas:
  - Requer ao menos 1 row com embedding IS NOT NULL antes de executar.
  - Rodar APÓS `python -m app.ingest.embeddings --competencia AAAAMM`.
  - O bloco DO $$ garante skip gracioso se a tabela ainda estiver vazia.
  - IVFFlat com lists=100 requer ao menos 200 linhas não-NULL (lists * 2).
    Com 4.980 procedimentos indexados, condição satisfeita.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0002_ivfflat_embeddings"
down_revision: Union[str, None] = "b676997e0213"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
          IF EXISTS (
            SELECT 1 FROM embeddings_procedimentos WHERE embedding IS NOT NULL LIMIT 1
          ) THEN
            EXECUTE 'CREATE INDEX IF NOT EXISTS idx_emb_vector
                     ON embeddings_procedimentos
                     USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)';
          ELSE
            RAISE NOTICE 'Skipping IVFFlat index — no non-NULL embeddings found. Run embeddings.py first.';
          END IF;
        END;
        $$;
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_emb_vector")
