"""Models SQLAlchemy para tabelas do pacote BDSIA (SIGTAP/DATASUS).

Campos de código SIGTAP são sempre CHAR de tamanho fixo — nunca Integer.
DT_COMPETENCIA (AAAAMM) faz parte da PK em todas as tabelas versionadas.
tb_ocupacao, tb_cid e tb_grupo_habilitacao não são versionados por competência.
Valores monetários (vl_sa, vl_sp) são inteiros sem separador decimal:
dividir por 100 para obter R$. Ex: 1250 → R$ 12,50.
"""

import sqlalchemy as sa
from sqlalchemy.orm import mapped_column, Mapped

from app.db import Base


class SigtapFinanciamento(Base):
    """tb_financiamento — tipos de financiamento (MAC, PAB, FAEC)."""

    __tablename__ = "sigtap_financiamentos"

    co_financiamento: Mapped[str] = mapped_column(sa.CHAR(2), primary_key=True)
    no_financiamento: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    dt_competencia: Mapped[str] = mapped_column(sa.CHAR(6), primary_key=True)


class SigtapRubrica(Base):
    """tb_rubrica — rubricas orçamentárias."""

    __tablename__ = "sigtap_rubricas"

    co_rubrica: Mapped[str] = mapped_column(sa.CHAR(6), primary_key=True)
    no_rubrica: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    dt_competencia: Mapped[str] = mapped_column(sa.CHAR(6), primary_key=True)


class SigtapRegistro(Base):
    """tb_registro — instrumentos de registro (BPA-C=02, BPA-I=01, APAC=03, AIH=04)."""

    __tablename__ = "sigtap_registros"

    co_registro: Mapped[str] = mapped_column(sa.CHAR(2), primary_key=True)
    no_registro: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    dt_competencia: Mapped[str] = mapped_column(sa.CHAR(6), primary_key=True)


class SigtapGrupo(Base):
    """tb_grupo — grupos de procedimentos (hierarquia nível 1)."""

    __tablename__ = "sigtap_grupos"

    co_grupo: Mapped[str] = mapped_column(sa.CHAR(2), primary_key=True)
    no_grupo: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    dt_competencia: Mapped[str] = mapped_column(sa.CHAR(6), primary_key=True)


class SigtapSubgrupo(Base):
    """tb_sub_grupo — subgrupos (hierarquia nível 2)."""

    __tablename__ = "sigtap_subgrupos"

    co_sub_grupo: Mapped[str] = mapped_column(sa.CHAR(2), primary_key=True)
    co_grupo: Mapped[str] = mapped_column(sa.CHAR(2), nullable=False)
    no_sub_grupo: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    dt_competencia: Mapped[str] = mapped_column(sa.CHAR(6), primary_key=True)


class SigtapFormaOrganizacao(Base):
    """tb_forma_organizacao — formas de organização (hierarquia nível 3)."""

    __tablename__ = "sigtap_formas_organizacao"

    co_forma_organizacao: Mapped[str] = mapped_column(sa.CHAR(2), primary_key=True)
    co_grupo: Mapped[str] = mapped_column(sa.CHAR(2), nullable=False)
    co_sub_grupo: Mapped[str] = mapped_column(sa.CHAR(2), nullable=False)
    no_forma_organizacao: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    dt_competencia: Mapped[str] = mapped_column(sa.CHAR(6), primary_key=True)


class SigtapOcupacao(Base):
    """tb_ocupacao — ocupações CBO. Sem DT_COMPETENCIA — única tabela não versionada."""

    __tablename__ = "sigtap_ocupacoes"

    co_ocupacao: Mapped[str] = mapped_column(sa.CHAR(6), primary_key=True)
    no_ocupacao: Mapped[str] = mapped_column(sa.String(150), nullable=False)


class SigtapHabilitacao(Base):
    """tb_habilitacao — habilitações."""

    __tablename__ = "sigtap_habilitacoes"

    co_habilitacao: Mapped[str] = mapped_column(sa.CHAR(4), primary_key=True)
    no_habilitacao: Mapped[str] = mapped_column(sa.String(150), nullable=False)
    dt_competencia: Mapped[str] = mapped_column(sa.CHAR(6), primary_key=True)


class SigtapGrupoHabilitacao(Base):
    """tb_grupo_habilitacao — grupos de habilitação. Sem DT_COMPETENCIA — não versionado.

    Nota: NU_GRUPO_HABILITACAO chega vazio no arquivo fonte do SIGTAP — não usar para join.
    O join anti-glosa com cnes_habilitacoes usa sigtap_habilitacoes.co_habilitacao = sgruphab.
    """

    __tablename__ = "sigtap_grupos_habilitacao"

    nu_grupo_habilitacao: Mapped[str] = mapped_column(sa.CHAR(4), primary_key=True)
    no_grupo_habilitacao: Mapped[str] = mapped_column(sa.String(20), nullable=False)
    ds_grupo_habilitacao: Mapped[str | None] = mapped_column(sa.String(250))


class SigtapServico(Base):
    """tb_servico — serviços."""

    __tablename__ = "sigtap_servicos"

    co_servico: Mapped[str] = mapped_column(sa.CHAR(3), primary_key=True)
    no_servico: Mapped[str] = mapped_column(sa.String(120), nullable=False)
    dt_competencia: Mapped[str] = mapped_column(sa.CHAR(6), primary_key=True)


class SigtapServicoClassificacao(Base):
    """tb_servico_classificacao — classificações de serviço."""

    __tablename__ = "sigtap_servicos_classificacao"

    co_servico: Mapped[str] = mapped_column(sa.CHAR(3), primary_key=True)
    co_classificacao: Mapped[str] = mapped_column(sa.CHAR(3), primary_key=True)
    no_classificacao: Mapped[str] = mapped_column(sa.String(150), nullable=False)
    dt_competencia: Mapped[str] = mapped_column(sa.CHAR(6), primary_key=True)


class SigtapCid(Base):
    """tb_cid — CID-10. Sem DT_COMPETENCIA — não versionado. Apenas co_cid, no_cid, tp_sexo."""

    __tablename__ = "sigtap_cids"

    co_cid: Mapped[str] = mapped_column(sa.CHAR(4), primary_key=True)
    no_cid: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    tp_sexo: Mapped[str | None] = mapped_column(sa.CHAR(1))


class SigtapProcedimento(Base):
    """tb_procedimento — tabela central do SIGTAP.

    Campos hospitalares omitidos: QT_DIAS_PERMANENCIA, QT_TEMPO_PERMANENCIA, VL_SH.
    Valores vl_sa e vl_sp são inteiros sem decimal (dividir por 100 → R$).
    """

    __tablename__ = "sigtap_procedimentos"

    co_procedimento: Mapped[str] = mapped_column(sa.CHAR(10), primary_key=True)
    no_procedimento: Mapped[str] = mapped_column(sa.String(250), nullable=False)
    tp_complexidade: Mapped[str | None] = mapped_column(sa.CHAR(1))
    tp_sexo: Mapped[str | None] = mapped_column(sa.CHAR(1))
    qt_maxima_execucao: Mapped[int | None] = mapped_column(sa.SmallInteger)
    qt_pontos: Mapped[int | None] = mapped_column(sa.SmallInteger)
    vl_idade_minima: Mapped[int | None] = mapped_column(sa.SmallInteger)
    vl_idade_maxima: Mapped[int | None] = mapped_column(sa.SmallInteger)
    vl_sa: Mapped[int | None] = mapped_column(sa.Integer)  # centavos — dividir por 100
    vl_sp: Mapped[int | None] = mapped_column(sa.Integer)  # centavos — dividir por 100
    co_financiamento: Mapped[str | None] = mapped_column(sa.CHAR(2))
    co_rubrica: Mapped[str | None] = mapped_column(sa.CHAR(6))
    dt_competencia: Mapped[str] = mapped_column(sa.CHAR(6), primary_key=True)


class SigtapDescricao(Base):
    """tb_descricao — descrição completa dos procedimentos (até 4000 chars). Usada para embeddings."""

    __tablename__ = "sigtap_descricoes"

    co_procedimento: Mapped[str] = mapped_column(sa.CHAR(10), primary_key=True)
    ds_procedimento: Mapped[str] = mapped_column(sa.Text, nullable=False)
    dt_competencia: Mapped[str] = mapped_column(sa.CHAR(6), primary_key=True)


# ── Tabelas de relacionamento ──────────────────────────────────────────────────


class SigtapRlProcOcupacao(Base):
    """rl_procedimento_ocupacao — procedimento × CBO (anti-glosa CBO)."""

    __tablename__ = "sigtap_rl_proc_ocupacao"

    co_procedimento: Mapped[str] = mapped_column(sa.CHAR(10), primary_key=True)
    co_ocupacao: Mapped[str] = mapped_column(sa.CHAR(6), primary_key=True)
    dt_competencia: Mapped[str] = mapped_column(sa.CHAR(6), primary_key=True)

    __table_args__ = (
        sa.Index("idx_rl_proc_ocupacao_cbo", "co_ocupacao"),
    )


class SigtapRlProcRegistro(Base):
    """rl_procedimento_registro — instrumento permitido por procedimento (BPA-C/BPA-I/APAC).

    Relação N:N — um procedimento pode admitir mais de um instrumento.
    """

    __tablename__ = "sigtap_rl_proc_registro"

    co_procedimento: Mapped[str] = mapped_column(sa.CHAR(10), primary_key=True)
    co_registro: Mapped[str] = mapped_column(sa.CHAR(2), primary_key=True)
    dt_competencia: Mapped[str] = mapped_column(sa.CHAR(6), primary_key=True)


class SigtapRlProcHabilitacao(Base):
    """rl_procedimento_habilitacao — habilitação exigida por procedimento.

    Join anti-glosa: co_habilitacao = cnes_habilitacoes.sgruphab
    (nu_grupo_habilitacao chega vazio no arquivo fonte — não usar para join).
    """

    __tablename__ = "sigtap_rl_proc_habilitacao"

    co_procedimento: Mapped[str] = mapped_column(sa.CHAR(10), primary_key=True)
    co_habilitacao: Mapped[str] = mapped_column(sa.CHAR(4), primary_key=True)
    nu_grupo_habilitacao: Mapped[str] = mapped_column(sa.CHAR(4), primary_key=True)
    dt_competencia: Mapped[str] = mapped_column(sa.CHAR(6), primary_key=True)

    __table_args__ = (
        sa.Index("idx_rl_proc_habilitacao_grupo", "nu_grupo_habilitacao"),
    )


class SigtapRlProcServico(Base):
    """rl_procedimento_servico — serviço/classificação exigido por procedimento (anti-glosa CNES)."""

    __tablename__ = "sigtap_rl_proc_servico"

    co_procedimento: Mapped[str] = mapped_column(sa.CHAR(10), primary_key=True)
    co_servico: Mapped[str] = mapped_column(sa.CHAR(3), primary_key=True)
    co_classificacao: Mapped[str] = mapped_column(sa.CHAR(3), primary_key=True)
    dt_competencia: Mapped[str] = mapped_column(sa.CHAR(6), primary_key=True)

    __table_args__ = (
        sa.Index("idx_rl_proc_servico", "co_servico", "co_classificacao"),
    )


class SigtapRlProcCid(Base):
    """rl_procedimento_cid — CIDs permitidos/exigidos para o procedimento."""

    __tablename__ = "sigtap_rl_proc_cid"

    co_procedimento: Mapped[str] = mapped_column(sa.CHAR(10), primary_key=True)
    co_cid: Mapped[str] = mapped_column(sa.CHAR(4), primary_key=True)
    st_principal: Mapped[str | None] = mapped_column(sa.CHAR(1))
    dt_competencia: Mapped[str] = mapped_column(sa.CHAR(6), primary_key=True)


class SigtapRlProcCompativel(Base):
    """rl_procedimento_compativel — compatibilidade entre procedimentos na mesma competência."""

    __tablename__ = "sigtap_rl_proc_compativel"

    co_procedimento: Mapped[str] = mapped_column(sa.CHAR(10), primary_key=True)
    co_registro_principal: Mapped[str] = mapped_column(sa.CHAR(2), primary_key=True)
    co_procedimento_compativel: Mapped[str] = mapped_column(sa.CHAR(10), primary_key=True)
    co_registro_compativel: Mapped[str] = mapped_column(sa.CHAR(2), primary_key=True)
    tp_compatibilidade: Mapped[str | None] = mapped_column(sa.CHAR(1))
    qt_permitida: Mapped[int | None] = mapped_column(sa.SmallInteger)
    dt_competencia: Mapped[str] = mapped_column(sa.CHAR(6), primary_key=True)
