"""Models SQLAlchemy para tabelas do SCNES (Cadastro Nacional de Estabelecimentos de Saúde).

Fontes (ZIP nacional BASE_DE_DADOS_CNES_{AAMM}.ZIP — CSV ';', Latin-1):
  tbEstabelecimento           → cnes_estabelecimentos
  tbCargaHorariaSus           → cnes_profissionais  (JOIN tbDadosProfissionalSus para obter CO_CNS)
  rlEstabServClass            → cnes_servicos

Fonte alternativa (obrigatória para habilitações — .dbc por UF):
  HB{UF}{AAMM}.dbc            → cnes_habilitacoes   (ftp://.../CNES/200508_/Dados/HB/)
  Leitura: dbc-to-dbf (puro Python) + dbfread/pandas

Notas:
  - CNES sempre CHAR(7) com zero à esquerda — nunca converter para inteiro.
  - COMPETEN formato AAAAMM — string, comparação lexicográfica funciona.
  - Filtro SUS em tbCargaHorariaSus: upper(TP_SUS_NAO_SUS) == 'S' (não PROF_SUS).
  - CO_UNIDADE (31 chars) em tbCargaHorariaSus — extrair CNES dos últimos 7 chars
    ou fazer join com tbEstabelecimento via CO_UNIDADE → CO_CNES.
  - CO_PROFISSIONAL_SUS é hash hex 16 chars; CNS real (CO_CNS) obtido via join
    com tbDadosProfissionalSus (7,6M linhas — indexar em dict hash→CNS na ingestão).
"""

import sqlalchemy as sa
from sqlalchemy.orm import mapped_column, Mapped

from app.db import Base


class CnesEstabelecimento(Base):
    """ST — estabelecimentos de saúde.

    Apenas colunas relevantes para faturamento ambulatorial BPA.
    """

    __tablename__ = "cnes_estabelecimentos"

    cnes: Mapped[str] = mapped_column(sa.CHAR(7), primary_key=True)
    codufmun: Mapped[str] = mapped_column(sa.CHAR(6), nullable=False)
    cpf_cnpj: Mapped[str | None] = mapped_column(sa.String(14))
    vinc_sus: Mapped[str | None] = mapped_column(sa.CHAR(1))
    tp_unid: Mapped[str | None] = mapped_column(sa.CHAR(2))
    niv_hier: Mapped[str | None] = mapped_column(sa.CHAR(2))
    tp_prest: Mapped[str | None] = mapped_column(sa.CHAR(2))
    atendamb: Mapped[str | None] = mapped_column(sa.CHAR(1))
    nivate_a: Mapped[str | None] = mapped_column(sa.CHAR(1))
    competen: Mapped[str] = mapped_column(sa.CHAR(6), primary_key=True)


class CnesProfissional(Base):
    """PF — profissionais vinculados a estabelecimentos. Importar apenas PROF_SUS='S'.

    CBO pode ter 5 ou 6 dígitos nas competências mais antigas; normalizar para 6 (pad left '0')
    antes de cruzar com sigtap_rl_proc_ocupacao.
    """

    __tablename__ = "cnes_profissionais"

    cnes: Mapped[str] = mapped_column(sa.CHAR(7), primary_key=True)
    cns_prof: Mapped[str] = mapped_column(sa.CHAR(15), primary_key=True)
    cbo: Mapped[str] = mapped_column(sa.CHAR(6), primary_key=True)
    nomeprof: Mapped[str | None] = mapped_column(sa.String(60))
    prof_sus: Mapped[str] = mapped_column(sa.CHAR(1), nullable=False, server_default="S")
    hora_amb: Mapped[int | None] = mapped_column(sa.SmallInteger)
    vinculac: Mapped[str | None] = mapped_column(sa.CHAR(6))
    conselho: Mapped[str | None] = mapped_column(sa.CHAR(2))
    registro: Mapped[str | None] = mapped_column(sa.String(13))  # NU_REGISTRO — obrigatório BPA-I
    competen: Mapped[str] = mapped_column(sa.CHAR(6), primary_key=True)

    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["cnes", "competen"],
            ["cnes_estabelecimentos.cnes", "cnes_estabelecimentos.competen"],
        ),
        sa.Index("idx_cnes_prof_cns", "cns_prof"),
        sa.Index("idx_cnes_prof_cbo", "cbo"),
    )


class CnesHabilitacao(Base):
    """HB — habilitações do estabelecimento.

    sgruphab é o código de join com sigtap_rl_proc_habilitacao.nu_grupo_habilitacao
    (não co_habilitacao). Validar vigência: cmpt_ini <= competencia_atual <= cmpt_fim.
    """

    __tablename__ = "cnes_habilitacoes"

    cnes: Mapped[str] = mapped_column(sa.CHAR(7), primary_key=True)
    sgruphab: Mapped[str] = mapped_column(sa.CHAR(4), primary_key=True)
    cmpt_ini: Mapped[str | None] = mapped_column(sa.CHAR(6))
    cmpt_fim: Mapped[str | None] = mapped_column(sa.CHAR(6))
    portaria: Mapped[str | None] = mapped_column(sa.String(20))
    competen: Mapped[str] = mapped_column(sa.CHAR(6), primary_key=True)

    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["cnes", "competen"],
            ["cnes_estabelecimentos.cnes", "cnes_estabelecimentos.competen"],
        ),
        sa.Index("idx_cnes_hab_vigencia", "cnes", "sgruphab", "cmpt_ini", "cmpt_fim"),
    )


class CnesServico(Base):
    """SR — serviços do estabelecimento. Importar apenas AMBUL='S'.

    serv_esp = CO_SERVICO no SIGTAP.
    class_sr = CO_CLASSIFICACAO no SIGTAP.
    Join anti-glosa: cnes_servicos JOIN sigtap_rl_proc_servico ON
        serv_esp = co_servico AND class_sr = co_classificacao.
    """

    __tablename__ = "cnes_servicos"

    cnes: Mapped[str] = mapped_column(sa.CHAR(7), primary_key=True)
    serv_esp: Mapped[str] = mapped_column(sa.CHAR(3), primary_key=True)
    class_sr: Mapped[str] = mapped_column(sa.CHAR(3), primary_key=True)
    ambul: Mapped[str | None] = mapped_column(sa.CHAR(1))
    competen: Mapped[str] = mapped_column(sa.CHAR(6), primary_key=True)

    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["cnes", "competen"],
            ["cnes_estabelecimentos.cnes", "cnes_estabelecimentos.competen"],
        ),
        sa.Index("idx_cnes_srv_servico", "cnes", "serv_esp", "class_sr"),
    )
