"""Models SQLAlchemy para tabelas operacionais do FaturaSUS.

Geradas pelo sistema; não importadas de fontes externas.

Decisões LGPD:
  - CNS do paciente NUNCA em texto plano.
  - cns_enc: BYTEA — AES-256-GCM (reversível para exportação BPA).
  - cns_hash: CHAR(64) — SHA-256 (irreversível, dedup e auditoria).
"""

import enum
import uuid

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import mapped_column, Mapped

from app.db import Base


class StatusRegistro(str, enum.Enum):
    """Status do registro de produção."""

    confirmado = "confirmado"
    pendente = "pendente"
    bloqueado = "bloqueado"
    corrigido = "corrigido"


class Profissional(Base):
    """Profissionais cadastrados no sistema pelo admin.

    Vincula o login ao CNS do profissional no SCNES.
    FK para cnes_profissionais é soft (sem constraint) — competência muda mensalmente.
    Constraint UNIQUE (cns, cnes, cbo) evita duplicatas de vínculo ativo.
    """

    __tablename__ = "profissionais"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    cns: Mapped[str] = mapped_column(sa.CHAR(15), nullable=False)
    cbo: Mapped[str] = mapped_column(sa.CHAR(6), nullable=False)
    cnes: Mapped[str] = mapped_column(sa.CHAR(7), nullable=False)
    competen: Mapped[str] = mapped_column(sa.CHAR(6), nullable=False)  # competência de ref. no SCNES
    ativo: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default="true")
    criado_em: Mapped[sa.DateTime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )

    __table_args__ = (
        sa.UniqueConstraint("cns", "cnes", "cbo", name="uq_profissional_vinculo"),
    )


class FpoProgramacao(Base):
    """Teto FPO (Física e Financeira por Procedimento) por CNES/procedimento/competência.

    Inserção manual pelo faturista. Registros acima do teto geram alerta (não bloqueio).
    """

    __tablename__ = "fpo_programacao"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    cnes: Mapped[str] = mapped_column(sa.CHAR(7), nullable=False)
    co_procedimento: Mapped[str] = mapped_column(sa.CHAR(10), nullable=False)
    competencia: Mapped[str] = mapped_column(sa.CHAR(6), nullable=False)
    qt_aprovada: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    criado_em: Mapped[sa.DateTime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )
    criado_por: Mapped[uuid.UUID | None] = mapped_column(
        sa.UUID(as_uuid=True), sa.ForeignKey("profissionais.id"), nullable=True
    )

    __table_args__ = (
        sa.UniqueConstraint("cnes", "co_procedimento", "competencia", name="uq_fpo_teto"),
    )


class RegistroProducao(Base):
    """Registros de produção ambulatorial capturados pelo sistema.

    cns_enc: AES-256-GCM — chave derivada por tenant (HKDF do Railway secret).
              Reversível na exportação BPA. NULL permitido para BPA-C (sem individualização).
    cns_hash: SHA-256 — irreversível. Usado para dedup e auditoria.
    co_registro: '01'=BPA-I, '02'=BPA-C.
    """

    __tablename__ = "registros_producao"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    cnes: Mapped[str] = mapped_column(sa.CHAR(7), nullable=False)
    co_procedimento: Mapped[str] = mapped_column(sa.CHAR(10), nullable=False)
    cns_enc: Mapped[bytes | None] = mapped_column(sa.LargeBinary)
    cns_hash: Mapped[str] = mapped_column(sa.CHAR(64), nullable=False)
    co_cid: Mapped[str | None] = mapped_column(sa.CHAR(4))
    cbo: Mapped[str] = mapped_column(sa.CHAR(6), nullable=False)
    co_registro: Mapped[str] = mapped_column(sa.CHAR(2), nullable=False)
    dt_atendimento: Mapped[sa.Date] = mapped_column(sa.Date, nullable=False)
    competencia: Mapped[str] = mapped_column(sa.CHAR(6), nullable=False)
    quantidade: Mapped[int] = mapped_column(
        sa.SmallInteger, nullable=False, server_default="1"
    )
    status: Mapped[StatusRegistro] = mapped_column(
        sa.Enum(StatusRegistro, name="status_registro"),
        nullable=False,
        server_default=StatusRegistro.pendente.value,
    )
    criado_em: Mapped[sa.DateTime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )
    criado_por: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), sa.ForeignKey("profissionais.id"), nullable=False
    )

    __table_args__ = (
        sa.Index("idx_reg_prod_competencia", "cnes", "competencia"),
        sa.Index("idx_reg_prod_hash", "cns_hash"),
        sa.Index("idx_reg_prod_proc_comp", "co_procedimento", "competencia"),
    )


class EmbeddingProcedimento(Base):
    """Embeddings de procedimentos SIGTAP para busca semântica (pgvector).

    embedding: vector(1536) — OpenAI text-embedding-3-small.
    Calculado apenas para procedimentos alterados no cron diário.
    """

    __tablename__ = "embeddings_procedimentos"

    co_procedimento: Mapped[str] = mapped_column(sa.CHAR(10), primary_key=True)
    dt_competencia: Mapped[str] = mapped_column(sa.CHAR(6), primary_key=True)
    embedding_text: Mapped[str] = mapped_column(sa.Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))
