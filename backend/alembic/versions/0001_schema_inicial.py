"""schema inicial

Revision ID: 0001
Revises:
Create Date: 2026-03-28

Tabelas criadas:
  SIGTAP (19 tabelas): sigtap_financiamentos, sigtap_rubricas, sigtap_registros,
    sigtap_grupos, sigtap_subgrupos, sigtap_formas_organizacao, sigtap_ocupacoes,
    sigtap_habilitacoes, sigtap_grupos_habilitacao, sigtap_servicos,
    sigtap_servicos_classificacao, sigtap_cids, sigtap_procedimentos,
    sigtap_descricoes, sigtap_rl_proc_ocupacao, sigtap_rl_proc_registro,
    sigtap_rl_proc_habilitacao, sigtap_rl_proc_servico, sigtap_rl_proc_cid,
    sigtap_rl_proc_compativel
  CNES (4 tabelas): cnes_estabelecimentos, cnes_profissionais,
    cnes_habilitacoes, cnes_servicos
  Operacional (4 tabelas): profissionais, fpo_programacao,
    registros_producao, embeddings_procedimentos

Ajustes manuais vs autogenerate:
  - CREATE EXTENSION IF NOT EXISTS vector (pgvector)
  - Indexes adicionais de anti-glosa (não gerados pelo autogenerate)
  - IVFFlat index comentado — requer dados para treinar; ativar após 1ª ingestão SIGTAP
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Extensão pgvector ──────────────────────────────────────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ── SIGTAP — tabelas de domínio ────────────────────────────────────────────

    op.create_table(
        "sigtap_financiamentos",
        sa.Column("co_financiamento", sa.CHAR(2), nullable=False),
        sa.Column("no_financiamento", sa.String(100), nullable=False),
        sa.Column("dt_competencia", sa.CHAR(6), nullable=False),
        sa.PrimaryKeyConstraint("co_financiamento", "dt_competencia"),
    )

    op.create_table(
        "sigtap_rubricas",
        sa.Column("co_rubrica", sa.CHAR(6), nullable=False),
        sa.Column("no_rubrica", sa.String(100), nullable=False),
        sa.Column("dt_competencia", sa.CHAR(6), nullable=False),
        sa.PrimaryKeyConstraint("co_rubrica", "dt_competencia"),
    )

    op.create_table(
        "sigtap_registros",
        sa.Column("co_registro", sa.CHAR(2), nullable=False),
        sa.Column("no_registro", sa.String(50), nullable=False),
        sa.Column("dt_competencia", sa.CHAR(6), nullable=False),
        sa.PrimaryKeyConstraint("co_registro", "dt_competencia"),
    )

    op.create_table(
        "sigtap_grupos",
        sa.Column("co_grupo", sa.CHAR(2), nullable=False),
        sa.Column("no_grupo", sa.String(100), nullable=False),
        sa.Column("dt_competencia", sa.CHAR(6), nullable=False),
        sa.PrimaryKeyConstraint("co_grupo", "dt_competencia"),
    )

    op.create_table(
        "sigtap_subgrupos",
        sa.Column("co_sub_grupo", sa.CHAR(2), nullable=False),
        sa.Column("co_grupo", sa.CHAR(2), nullable=False),
        sa.Column("no_sub_grupo", sa.String(100), nullable=False),
        sa.Column("dt_competencia", sa.CHAR(6), nullable=False),
        sa.PrimaryKeyConstraint("co_sub_grupo", "dt_competencia"),
    )

    op.create_table(
        "sigtap_formas_organizacao",
        sa.Column("co_forma_organizacao", sa.CHAR(2), nullable=False),
        sa.Column("co_grupo", sa.CHAR(2), nullable=False),
        sa.Column("co_sub_grupo", sa.CHAR(2), nullable=False),
        sa.Column("no_forma_organizacao", sa.String(100), nullable=False),
        sa.Column("dt_competencia", sa.CHAR(6), nullable=False),
        sa.PrimaryKeyConstraint("co_forma_organizacao", "dt_competencia"),
    )

    op.create_table(
        "sigtap_ocupacoes",
        sa.Column("co_ocupacao", sa.CHAR(6), nullable=False),
        sa.Column("no_ocupacao", sa.String(150), nullable=False),
        sa.PrimaryKeyConstraint("co_ocupacao"),
    )

    op.create_table(
        "sigtap_habilitacoes",
        sa.Column("co_habilitacao", sa.CHAR(4), nullable=False),
        sa.Column("no_habilitacao", sa.String(150), nullable=False),
        sa.Column("dt_competencia", sa.CHAR(6), nullable=False),
        sa.PrimaryKeyConstraint("co_habilitacao", "dt_competencia"),
    )

    op.create_table(
        "sigtap_grupos_habilitacao",
        sa.Column("nu_grupo_habilitacao", sa.CHAR(4), nullable=False),
        sa.Column("no_grupo_habilitacao", sa.String(20), nullable=False),
        sa.Column("ds_grupo_habilitacao", sa.String(250), nullable=True),
        sa.PrimaryKeyConstraint("nu_grupo_habilitacao"),
    )

    op.create_table(
        "sigtap_servicos",
        sa.Column("co_servico", sa.CHAR(3), nullable=False),
        sa.Column("no_servico", sa.String(120), nullable=False),
        sa.Column("dt_competencia", sa.CHAR(6), nullable=False),
        sa.PrimaryKeyConstraint("co_servico", "dt_competencia"),
    )

    op.create_table(
        "sigtap_servicos_classificacao",
        sa.Column("co_servico", sa.CHAR(3), nullable=False),
        sa.Column("co_classificacao", sa.CHAR(3), nullable=False),
        sa.Column("no_classificacao", sa.String(150), nullable=False),
        sa.Column("dt_competencia", sa.CHAR(6), nullable=False),
        sa.PrimaryKeyConstraint("co_servico", "co_classificacao", "dt_competencia"),
    )

    op.create_table(
        "sigtap_cids",
        sa.Column("co_cid", sa.CHAR(4), nullable=False),
        sa.Column("no_cid", sa.String(100), nullable=False),
        sa.Column("tp_sexo", sa.CHAR(1), nullable=True),
        sa.PrimaryKeyConstraint("co_cid"),
    )

    op.create_table(
        "sigtap_procedimentos",
        sa.Column("co_procedimento", sa.CHAR(10), nullable=False),
        sa.Column("no_procedimento", sa.String(250), nullable=False),
        sa.Column("tp_complexidade", sa.CHAR(1), nullable=True),
        sa.Column("tp_sexo", sa.CHAR(1), nullable=True),
        sa.Column("qt_maxima_execucao", sa.SmallInteger(), nullable=True),
        sa.Column("qt_pontos", sa.SmallInteger(), nullable=True),
        sa.Column("vl_idade_minima", sa.SmallInteger(), nullable=True),
        sa.Column("vl_idade_maxima", sa.SmallInteger(), nullable=True),
        sa.Column("vl_sa", sa.Integer(), nullable=True),
        sa.Column("vl_sp", sa.Integer(), nullable=True),
        sa.Column("co_financiamento", sa.CHAR(2), nullable=True),
        sa.Column("co_rubrica", sa.CHAR(6), nullable=True),
        sa.Column("dt_competencia", sa.CHAR(6), nullable=False),
        sa.PrimaryKeyConstraint("co_procedimento", "dt_competencia"),
    )

    op.create_table(
        "sigtap_descricoes",
        sa.Column("co_procedimento", sa.CHAR(10), nullable=False),
        sa.Column("ds_procedimento", sa.Text(), nullable=False),
        sa.Column("dt_competencia", sa.CHAR(6), nullable=False),
        sa.PrimaryKeyConstraint("co_procedimento", "dt_competencia"),
    )

    # ── SIGTAP — tabelas de relacionamento ─────────────────────────────────────

    op.create_table(
        "sigtap_rl_proc_ocupacao",
        sa.Column("co_procedimento", sa.CHAR(10), nullable=False),
        sa.Column("co_ocupacao", sa.CHAR(6), nullable=False),
        sa.Column("dt_competencia", sa.CHAR(6), nullable=False),
        sa.PrimaryKeyConstraint("co_procedimento", "co_ocupacao", "dt_competencia"),
    )
    op.create_index("idx_rl_proc_ocupacao_cbo", "sigtap_rl_proc_ocupacao", ["co_ocupacao"])

    op.create_table(
        "sigtap_rl_proc_registro",
        sa.Column("co_procedimento", sa.CHAR(10), nullable=False),
        sa.Column("co_registro", sa.CHAR(2), nullable=False),
        sa.Column("dt_competencia", sa.CHAR(6), nullable=False),
        sa.PrimaryKeyConstraint("co_procedimento", "co_registro", "dt_competencia"),
    )

    op.create_table(
        "sigtap_rl_proc_habilitacao",
        sa.Column("co_procedimento", sa.CHAR(10), nullable=False),
        sa.Column("co_habilitacao", sa.CHAR(4), nullable=False),
        sa.Column("nu_grupo_habilitacao", sa.CHAR(4), nullable=False),
        sa.Column("dt_competencia", sa.CHAR(6), nullable=False),
        sa.PrimaryKeyConstraint(
            "co_procedimento", "co_habilitacao", "nu_grupo_habilitacao", "dt_competencia"
        ),
    )
    op.create_index(
        "idx_rl_proc_habilitacao_grupo",
        "sigtap_rl_proc_habilitacao",
        ["nu_grupo_habilitacao"],
    )

    op.create_table(
        "sigtap_rl_proc_servico",
        sa.Column("co_procedimento", sa.CHAR(10), nullable=False),
        sa.Column("co_servico", sa.CHAR(3), nullable=False),
        sa.Column("co_classificacao", sa.CHAR(3), nullable=False),
        sa.Column("dt_competencia", sa.CHAR(6), nullable=False),
        sa.PrimaryKeyConstraint(
            "co_procedimento", "co_servico", "co_classificacao", "dt_competencia"
        ),
    )
    op.create_index(
        "idx_rl_proc_servico",
        "sigtap_rl_proc_servico",
        ["co_servico", "co_classificacao"],
    )

    op.create_table(
        "sigtap_rl_proc_cid",
        sa.Column("co_procedimento", sa.CHAR(10), nullable=False),
        sa.Column("co_cid", sa.CHAR(4), nullable=False),
        sa.Column("st_principal", sa.CHAR(1), nullable=True),
        sa.Column("dt_competencia", sa.CHAR(6), nullable=False),
        sa.PrimaryKeyConstraint("co_procedimento", "co_cid", "dt_competencia"),
    )

    op.create_table(
        "sigtap_rl_proc_compativel",
        sa.Column("co_procedimento", sa.CHAR(10), nullable=False),
        sa.Column("co_registro_principal", sa.CHAR(2), nullable=False),
        sa.Column("co_procedimento_compativel", sa.CHAR(10), nullable=False),
        sa.Column("co_registro_compativel", sa.CHAR(2), nullable=False),
        sa.Column("tp_compatibilidade", sa.CHAR(1), nullable=True),
        sa.Column("qt_permitida", sa.SmallInteger(), nullable=True),
        sa.Column("dt_competencia", sa.CHAR(6), nullable=False),
        sa.PrimaryKeyConstraint(
            "co_procedimento",
            "co_registro_principal",
            "co_procedimento_compativel",
            "co_registro_compativel",
            "dt_competencia",
        ),
    )

    # ── CNES ───────────────────────────────────────────────────────────────────

    op.create_table(
        "cnes_estabelecimentos",
        sa.Column("cnes", sa.CHAR(7), nullable=False),
        sa.Column("codufmun", sa.CHAR(6), nullable=False),
        sa.Column("cpf_cnpj", sa.String(14), nullable=True),
        sa.Column("vinc_sus", sa.CHAR(1), nullable=True),
        sa.Column("tp_unid", sa.CHAR(2), nullable=True),
        sa.Column("niv_hier", sa.CHAR(2), nullable=True),
        sa.Column("tp_prest", sa.CHAR(2), nullable=True),
        sa.Column("atendamb", sa.CHAR(1), nullable=True),
        sa.Column("nivate_a", sa.CHAR(1), nullable=True),
        sa.Column("competen", sa.CHAR(6), nullable=False),
        sa.PrimaryKeyConstraint("cnes", "competen"),
    )

    op.create_table(
        "cnes_profissionais",
        sa.Column("cnes", sa.CHAR(7), nullable=False),
        sa.Column("cns_prof", sa.CHAR(15), nullable=False),
        sa.Column("cbo", sa.CHAR(6), nullable=False),
        sa.Column("nomeprof", sa.String(60), nullable=True),
        sa.Column("prof_sus", sa.CHAR(1), nullable=False, server_default="S"),
        sa.Column("hora_amb", sa.SmallInteger(), nullable=True),
        sa.Column("vinculac", sa.CHAR(6), nullable=True),
        sa.Column("conselho", sa.CHAR(2), nullable=True),
        sa.Column("competen", sa.CHAR(6), nullable=False),
        sa.ForeignKeyConstraint(
            ["cnes", "competen"],
            ["cnes_estabelecimentos.cnes", "cnes_estabelecimentos.competen"],
        ),
        sa.PrimaryKeyConstraint("cnes", "cns_prof", "cbo", "competen"),
    )
    op.create_index("idx_cnes_prof_cns", "cnes_profissionais", ["cns_prof"])
    op.create_index("idx_cnes_prof_cbo", "cnes_profissionais", ["cbo"])

    op.create_table(
        "cnes_habilitacoes",
        sa.Column("cnes", sa.CHAR(7), nullable=False),
        sa.Column("sgruphab", sa.CHAR(4), nullable=False),
        sa.Column("cmpt_ini", sa.CHAR(6), nullable=True),
        sa.Column("cmpt_fim", sa.CHAR(6), nullable=True),
        sa.Column("portaria", sa.String(20), nullable=True),
        sa.Column("competen", sa.CHAR(6), nullable=False),
        sa.ForeignKeyConstraint(
            ["cnes", "competen"],
            ["cnes_estabelecimentos.cnes", "cnes_estabelecimentos.competen"],
        ),
        sa.PrimaryKeyConstraint("cnes", "sgruphab", "competen"),
    )
    op.create_index(
        "idx_cnes_hab_vigencia",
        "cnes_habilitacoes",
        ["cnes", "sgruphab", "cmpt_ini", "cmpt_fim"],
    )

    op.create_table(
        "cnes_servicos",
        sa.Column("cnes", sa.CHAR(7), nullable=False),
        sa.Column("serv_esp", sa.CHAR(3), nullable=False),
        sa.Column("class_sr", sa.CHAR(3), nullable=False),
        sa.Column("ambul", sa.CHAR(1), nullable=True),
        sa.Column("competen", sa.CHAR(6), nullable=False),
        sa.ForeignKeyConstraint(
            ["cnes", "competen"],
            ["cnes_estabelecimentos.cnes", "cnes_estabelecimentos.competen"],
        ),
        sa.PrimaryKeyConstraint("cnes", "serv_esp", "class_sr", "competen"),
    )
    op.create_index("idx_cnes_srv_servico", "cnes_servicos", ["cnes", "serv_esp", "class_sr"])

    # ── Operacional ────────────────────────────────────────────────────────────

    op.create_table(
        "profissionais",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("cns", sa.CHAR(15), nullable=False),
        sa.Column("cbo", sa.CHAR(6), nullable=False),
        sa.Column("cnes", sa.CHAR(7), nullable=False),
        sa.Column("competen", sa.CHAR(6), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cns", "cnes", "cbo", name="uq_profissional_vinculo"),
    )

    op.create_table(
        "fpo_programacao",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("cnes", sa.CHAR(7), nullable=False),
        sa.Column("co_procedimento", sa.CHAR(10), nullable=False),
        sa.Column("competencia", sa.CHAR(6), nullable=False),
        sa.Column("qt_aprovada", sa.Integer(), nullable=False),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("criado_por", sa.UUID(), sa.ForeignKey("profissionais.id"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cnes", "co_procedimento", "competencia", name="uq_fpo_teto"),
    )

    op.create_table(
        "registros_producao",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("cnes", sa.CHAR(7), nullable=False),
        sa.Column("co_procedimento", sa.CHAR(10), nullable=False),
        sa.Column("cns_enc", sa.LargeBinary(), nullable=True),
        sa.Column("cns_hash", sa.CHAR(64), nullable=False),
        sa.Column("co_cid", sa.CHAR(4), nullable=True),
        sa.Column("cbo", sa.CHAR(6), nullable=False),
        sa.Column("co_registro", sa.CHAR(2), nullable=False),
        sa.Column("dt_atendimento", sa.Date(), nullable=False),
        sa.Column("competencia", sa.CHAR(6), nullable=False),
        sa.Column("quantidade", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column(
            "status",
            sa.Enum(
                "confirmado", "pendente", "bloqueado", "corrigido",
                name="status_registro",
            ),
            nullable=False,
            server_default="pendente",
        ),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("criado_por", sa.UUID(), sa.ForeignKey("profissionais.id"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_reg_prod_competencia", "registros_producao", ["cnes", "competencia"])
    op.create_index("idx_reg_prod_hash", "registros_producao", ["cns_hash"])
    op.create_index(
        "idx_reg_prod_proc_comp", "registros_producao", ["co_procedimento", "competencia"]
    )

    op.create_table(
        "embeddings_procedimentos",
        sa.Column("co_procedimento", sa.CHAR(10), nullable=False),
        sa.Column("dt_competencia", sa.CHAR(6), nullable=False),
        sa.Column("embedding_text", sa.Text(), nullable=False),
        # vector(1536) — OpenAI text-embedding-3-small
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.PrimaryKeyConstraint("co_procedimento", "dt_competencia"),
    )

    # IVFFlat index — COMENTADO intencionalmente.
    # Requer ao menos ~1000 linhas para treinar (error: "lists (100) > rows").
    # Ativar após a primeira ingestão SIGTAP:
    #
    # op.execute(
    #     "CREATE INDEX idx_emb_vector ON embeddings_procedimentos "
    #     "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    # )


def downgrade() -> None:
    op.drop_table("embeddings_procedimentos")
    op.drop_index("idx_reg_prod_proc_comp", table_name="registros_producao")
    op.drop_index("idx_reg_prod_hash", table_name="registros_producao")
    op.drop_index("idx_reg_prod_competencia", table_name="registros_producao")
    op.drop_table("registros_producao")
    op.execute("DROP TYPE IF EXISTS status_registro")
    op.drop_table("fpo_programacao")
    op.drop_table("profissionais")

    op.drop_index("idx_cnes_srv_servico", table_name="cnes_servicos")
    op.drop_table("cnes_servicos")
    op.drop_index("idx_cnes_hab_vigencia", table_name="cnes_habilitacoes")
    op.drop_table("cnes_habilitacoes")
    op.drop_index("idx_cnes_prof_cbo", table_name="cnes_profissionais")
    op.drop_index("idx_cnes_prof_cns", table_name="cnes_profissionais")
    op.drop_table("cnes_profissionais")
    op.drop_table("cnes_estabelecimentos")

    op.drop_table("sigtap_rl_proc_compativel")
    op.drop_table("sigtap_rl_proc_cid")
    op.drop_index("idx_rl_proc_servico", table_name="sigtap_rl_proc_servico")
    op.drop_table("sigtap_rl_proc_servico")
    op.drop_index("idx_rl_proc_habilitacao_grupo", table_name="sigtap_rl_proc_habilitacao")
    op.drop_table("sigtap_rl_proc_habilitacao")
    op.drop_table("sigtap_rl_proc_registro")
    op.drop_index("idx_rl_proc_ocupacao_cbo", table_name="sigtap_rl_proc_ocupacao")
    op.drop_table("sigtap_rl_proc_ocupacao")
    op.drop_table("sigtap_descricoes")
    op.drop_table("sigtap_procedimentos")
    op.drop_table("sigtap_cids")
    op.drop_table("sigtap_servicos_classificacao")
    op.drop_table("sigtap_servicos")
    op.drop_table("sigtap_grupos_habilitacao")
    op.drop_table("sigtap_habilitacoes")
    op.drop_table("sigtap_ocupacoes")
    op.drop_table("sigtap_formas_organizacao")
    op.drop_table("sigtap_subgrupos")
    op.drop_table("sigtap_grupos")
    op.drop_table("sigtap_registros")
    op.drop_table("sigtap_rubricas")
    op.drop_table("sigtap_financiamentos")

    op.execute("DROP EXTENSION IF EXISTS vector")
