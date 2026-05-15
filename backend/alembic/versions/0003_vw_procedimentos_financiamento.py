"""view vw_procedimentos_financiamento — mapeamento MAC/FAEC para diagnóstico de subregistro

Revision ID: 0003_vw_procedimentos_financiamento
Revises: 0002_ivfflat_embeddings
Create Date: 2026-04-07

Notas:
  - View reutilizável pelo script sia_producao.py (etapas 7b/7c).
  - co_financiamento vem direto de sigtap_procedimentos (não existe tabela rl_proc_financiamento).
  - LEFT JOIN em sigtap_financiamentos para obter no_financiamento sem perder linhas.
  - vl_unitario_sigtap = (vl_sa + vl_sp) / 100.0 — VL_SH omitido do schema (hospitalar).
  - Filtro MAX(dt_competencia) segue convenção DEC-014/DEC-015.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0003_financiamento_view"
down_revision: Union[str, None] = "0002_ivfflat_embeddings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE OR REPLACE VIEW vw_procedimentos_financiamento AS
        SELECT
            p.co_procedimento,
            p.no_procedimento,
            p.co_financiamento,
            f.no_financiamento,
            (COALESCE(p.vl_sa, 0) + COALESCE(p.vl_sp, 0)) / 100.0 AS vl_unitario_sigtap,
            p.dt_competencia
        FROM sigtap_procedimentos p
        LEFT JOIN sigtap_financiamentos f
               ON f.co_financiamento = p.co_financiamento
              AND f.dt_competencia   = p.dt_competencia
        WHERE p.dt_competencia = (SELECT MAX(dt_competencia) FROM sigtap_procedimentos);
    """)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS vw_procedimentos_financiamento")
