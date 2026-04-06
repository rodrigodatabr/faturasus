"""Serviço de validação anti-glosa — verifica 8 regras antes de persistir um registro.

Bloqueios (B1–B5): impedem a persistência.
Alertas  (A1–A3): persistem, mas marcam o registro para revisão.
"""

import asyncio
import logging
from datetime import date
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("faturasus")


# ── Schemas ────────────────────────────────────────────────────────────────────

class GlosaItem(BaseModel):
    codigo: str
    mensagem: str
    detalhe: str


class RegistroContext(BaseModel):
    co_procedimento: str    # 10 dígitos
    cnes: str               # 7 dígitos
    cbo: str                # 6 dígitos (do profissional logado)
    co_registro: str        # '01'=BPA-I, '02'=BPA-C
    dt_atendimento: date
    competencia: str        # AAAAMM — competência de apresentação
    cns_hash: str           # SHA-256 do CNS do paciente (para dedup)
    quantidade: int
    profissional_id: UUID
    cns_invalido: bool = False


class ResultadoValidacao(BaseModel):
    aprovado: bool
    bloqueios: list[GlosaItem]
    alertas: list[GlosaItem]


# ── Helpers ────────────────────────────────────────────────────────────────────

def competencias_aceitas(competencia: str) -> list[str]:
    """Retorna [competencia, competencia-1, competencia-2, competencia-3]."""
    ano, mes = int(competencia[:4]), int(competencia[4:])
    result = []
    for i in range(4):
        m = mes - i
        a = ano
        while m <= 0:
            m += 12
            a -= 1
        result.append(f"{a:04d}{m:02d}")
    return result


# ── Verificações de bloqueio ───────────────────────────────────────────────────

async def _check_b1_cbo(ctx: RegistroContext, session: AsyncSession) -> list[GlosaItem]:
    """B1 — CBO × Procedimento."""
    # Conta quantos CBOs o procedimento exige
    count_sql = text("""
        SELECT COUNT(*) AS total
        FROM sigtap_rl_proc_ocupacao
        WHERE co_procedimento = :co_procedimento
          AND dt_competencia = :competencia
    """)
    row = (await session.execute(count_sql, {
        "co_procedimento": ctx.co_procedimento,
        "competencia": ctx.competencia,
    })).fetchone()
    total_cbos = row.total if row else 0

    if total_cbos == 0:
        # Procedimento sem restrição de CBO — qualquer CBO aceito
        return []

    match_sql = text("""
        SELECT 1 FROM sigtap_rl_proc_ocupacao
        WHERE co_procedimento = :co_procedimento
          AND co_ocupacao = :cbo
          AND dt_competencia = :competencia
        LIMIT 1
    """)
    match = (await session.execute(match_sql, {
        "co_procedimento": ctx.co_procedimento,
        "cbo": ctx.cbo,
        "competencia": ctx.competencia,
    })).fetchone()

    if match:
        return []
    return [GlosaItem(
        codigo="CBO_INCOMPATIVEL",
        mensagem="CBO do profissional não autorizado para este procedimento.",
        detalhe=f"CBO {ctx.cbo} não consta em sigtap_rl_proc_ocupacao para o procedimento {ctx.co_procedimento} (competência {ctx.competencia}).",
    )]


async def _check_b2_habilitacao(ctx: RegistroContext, session: AsyncSession) -> list[GlosaItem]:
    """B2 — Habilitação CNES."""
    # Verifica se o procedimento exige habilitação
    exige_sql = text("""
        SELECT 1 FROM sigtap_rl_proc_habilitacao
        WHERE co_procedimento = :co_procedimento
          AND dt_competencia = :competencia
        LIMIT 1
    """)
    exige = (await session.execute(exige_sql, {
        "co_procedimento": ctx.co_procedimento,
        "competencia": ctx.competencia,
    })).fetchone()

    if not exige:
        return []

    # O procedimento exige habilitação — verifica se o CNES a possui
    join_sql = text("""
        SELECT 1
        FROM sigtap_rl_proc_habilitacao rph
        JOIN cnes_habilitacoes ch
          ON ch.sgruphab = rph.co_habilitacao
        WHERE rph.co_procedimento = :co_procedimento
          AND rph.dt_competencia = :competencia
          AND ch.cnes = :cnes
          AND ch.cmpt_ini <= :competencia
          AND (ch.cmpt_fim IS NULL OR ch.cmpt_fim >= :competencia)
        LIMIT 1
    """)
    match = (await session.execute(join_sql, {
        "co_procedimento": ctx.co_procedimento,
        "competencia": ctx.competencia,
        "cnes": ctx.cnes,
    })).fetchone()

    if match:
        return []
    return [GlosaItem(
        codigo="HABILITACAO_AUSENTE",
        mensagem="Estabelecimento não possui a habilitação exigida para este procedimento.",
        detalhe=f"CNES {ctx.cnes} sem habilitação vigente para o procedimento {ctx.co_procedimento} (competência {ctx.competencia}).",
    )]


async def _check_b3_servico(ctx: RegistroContext, session: AsyncSession) -> list[GlosaItem]:
    """B3 — Serviço/Classificação CNES."""
    exige_sql = text("""
        SELECT 1 FROM sigtap_rl_proc_servico
        WHERE co_procedimento = :co_procedimento
          AND dt_competencia = :competencia
        LIMIT 1
    """)
    exige = (await session.execute(exige_sql, {
        "co_procedimento": ctx.co_procedimento,
        "competencia": ctx.competencia,
    })).fetchone()

    if not exige:
        return []

    join_sql = text("""
        SELECT 1
        FROM sigtap_rl_proc_servico rps
        JOIN cnes_servicos cs
          ON cs.serv_esp = rps.co_servico
         AND cs.class_sr = rps.co_classificacao
        WHERE rps.co_procedimento = :co_procedimento
          AND rps.dt_competencia = :competencia
          AND cs.cnes = :cnes
          AND cs.competen = :competencia
        LIMIT 1
    """)
    match = (await session.execute(join_sql, {
        "co_procedimento": ctx.co_procedimento,
        "competencia": ctx.competencia,
        "cnes": ctx.cnes,
    })).fetchone()

    if match:
        return []
    return [GlosaItem(
        codigo="SERVICO_AUSENTE",
        mensagem="Estabelecimento não possui o serviço/classificação exigido para este procedimento.",
        detalhe=f"CNES {ctx.cnes} sem serviço compatível para o procedimento {ctx.co_procedimento} (competência {ctx.competencia}).",
    )]


async def _check_b4_instrumento(ctx: RegistroContext, session: AsyncSession) -> list[GlosaItem]:
    """B4 — Instrumento correto (BPA-C vs BPA-I)."""
    registros_sql = text("""
        SELECT co_registro FROM sigtap_rl_proc_registro
        WHERE co_procedimento = :co_procedimento
          AND dt_competencia = :competencia
    """)
    rows = (await session.execute(registros_sql, {
        "co_procedimento": ctx.co_procedimento,
        "competencia": ctx.competencia,
    })).fetchall()

    instrumentos_validos = {r.co_registro for r in rows}

    if instrumentos_validos and ctx.co_registro not in instrumentos_validos:
        return [GlosaItem(
            codigo="INSTRUMENTO_INVALIDO",
            mensagem="Instrumento de registro informado não é válido para este procedimento.",
            detalhe=f"co_registro='{ctx.co_registro}' inválido para o procedimento {ctx.co_procedimento}. Instrumentos aceitos: {sorted(instrumentos_validos)}.",
        )]

    # B4b: se proc admite ambos os instrumentos, verifica mistura na competência
    if "01" in instrumentos_validos and "02" in instrumentos_validos:
        misto_sql = text("""
            SELECT 1 FROM registros_producao
            WHERE co_procedimento = :co_procedimento
              AND cnes = :cnes
              AND competencia = :competencia
              AND co_registro != :co_registro
            LIMIT 1
        """)
        misto = (await session.execute(misto_sql, {
            "co_procedimento": ctx.co_procedimento,
            "cnes": ctx.cnes,
            "competencia": ctx.competencia,
            "co_registro": ctx.co_registro,
        })).fetchone()

        if misto:
            outro = "02" if ctx.co_registro == "01" else "01"
            return [GlosaItem(
                codigo="INSTRUMENTO_MISTO",
                mensagem="Já existem registros deste procedimento com instrumento diferente na mesma competência.",
                detalhe=f"Procedimento {ctx.co_procedimento} no CNES {ctx.cnes} já tem registros com co_registro='{outro}' na competência {ctx.competencia}.",
            )]

    return []


async def _check_b5_retroatividade(ctx: RegistroContext, _session: AsyncSession) -> list[GlosaItem]:
    """B5 — Retroatividade (puro Python, sem DB)."""
    comp_atendimento = ctx.dt_atendimento.strftime("%Y%m")
    aceitas = competencias_aceitas(ctx.competencia)
    if comp_atendimento not in aceitas:
        return [GlosaItem(
            codigo="RETROATIVIDADE_EXCEDIDA",
            mensagem="Data de atendimento fora do período de retroatividade permitido (4 competências).",
            detalhe=f"Atendimento em {ctx.dt_atendimento} (competência {comp_atendimento}) não está entre as competências aceitas {aceitas} para apresentação {ctx.competencia}.",
        )]
    return []


# ── Verificações de alerta ─────────────────────────────────────────────────────

async def _check_a1_duplicidade(ctx: RegistroContext, session: AsyncSession) -> list[GlosaItem]:
    """A1 — Duplicidade suspeita."""
    dup_sql = text("""
        SELECT 1 FROM registros_producao
        WHERE cnes = :cnes
          AND co_procedimento = :co_procedimento
          AND cns_hash = :cns_hash
          AND cbo = :cbo
          AND dt_atendimento = :dt_atendimento
          AND competencia = :competencia
        LIMIT 1
    """)
    dup = (await session.execute(dup_sql, {
        "cnes": ctx.cnes,
        "co_procedimento": ctx.co_procedimento,
        "cns_hash": ctx.cns_hash,
        "cbo": ctx.cbo,
        "dt_atendimento": ctx.dt_atendimento,
        "competencia": ctx.competencia,
    })).fetchone()

    if dup:
        return [GlosaItem(
            codigo="DUPLICIDADE_SUSPEITA",
            mensagem="Possível registro duplicado encontrado para este paciente/procedimento/data.",
            detalhe=f"Já existe registro para o procedimento {ctx.co_procedimento}, CNES {ctx.cnes}, CBO {ctx.cbo}, data {ctx.dt_atendimento}, competência {ctx.competencia}.",
        )]
    return []


async def _check_a2_fpo(ctx: RegistroContext, session: AsyncSession) -> list[GlosaItem]:
    """A2 — FPO (teto MAC)."""
    fpo_sql = text("""
        SELECT fpo.qt_aprovada,
               COALESCE(SUM(rp.quantidade), 0) AS qt_registrada
        FROM fpo_programacao fpo
        LEFT JOIN registros_producao rp
          ON rp.co_procedimento = fpo.co_procedimento
         AND rp.cnes = fpo.cnes
         AND rp.competencia = fpo.competencia
        WHERE fpo.cnes = :cnes
          AND fpo.co_procedimento = :co_procedimento
          AND fpo.competencia = :competencia
        GROUP BY fpo.qt_aprovada
    """)
    row = (await session.execute(fpo_sql, {
        "cnes": ctx.cnes,
        "co_procedimento": ctx.co_procedimento,
        "competencia": ctx.competencia,
    })).fetchone()

    if not row:
        # Sem teto cadastrado — sem alerta
        return []

    qt_aprovada = row.qt_aprovada
    qt_registrada = row.qt_registrada
    if qt_registrada + ctx.quantidade > qt_aprovada:
        saldo = qt_aprovada - qt_registrada
        return [GlosaItem(
            codigo="FPO_EXCEDIDO",
            mensagem="Quantidade solicitada excede o teto programado (FPO/MAC) para este procedimento.",
            detalhe=f"Teto aprovado: {qt_aprovada} | Já registrado: {qt_registrada} | Saldo: {saldo} | Solicitado: {ctx.quantidade}.",
        )]
    return []


async def _check_a3_cns(ctx: RegistroContext, _session: AsyncSession) -> list[GlosaItem]:
    """A3 — CNS com dígito verificador inválido."""
    if ctx.cns_invalido:
        return [GlosaItem(
            codigo="CNS_INVALIDO",
            mensagem="CNS do paciente não passou na validação do dígito verificador.",
            detalhe="O CNS informado pode estar incorreto. Verifique o cartão do paciente.",
        )]
    return []


# ── Função principal ───────────────────────────────────────────────────────────

async def validar_registro(ctx: RegistroContext, session: AsyncSession) -> ResultadoValidacao:
    """Executa as 8 verificações anti-glosa em paralelo.

    Bloqueios e alertas são disparados simultaneamente via asyncio.gather.
    Retorna ResultadoValidacao com aprovado=False se houver qualquer bloqueio.
    """
    # B1–B4 consultam tabelas SIGTAP filtradas por dt_competencia. Se a competência
    # do registro (ex: 202604) ainda não foi ingerida, as queries retornam vazio e
    # todas as regras passam silenciosamente. Usa-se a competência mais recente
    # disponível no SIGTAP — igual ao padrão adotado no classificador (DEC-014/DEC-015).
    row = await session.execute(
        text("SELECT MAX(dt_competencia) FROM sigtap_rl_proc_ocupacao")
    )
    comp_sigtap = row.scalar() or ctx.competencia
    if comp_sigtap != ctx.competencia:
        logger.info(
            "anti_glosa: competência do registro %s sem dados SIGTAP — usando %s para B1–B4",
            ctx.competencia, comp_sigtap,
        )
    ctx_sigtap = ctx.model_copy(update={"competencia": comp_sigtap})

    bloqueio_tasks = [
        _check_b1_cbo(ctx_sigtap, session),
        _check_b2_habilitacao(ctx_sigtap, session),
        _check_b3_servico(ctx_sigtap, session),
        _check_b4_instrumento(ctx_sigtap, session),
        _check_b5_retroatividade(ctx, session),   # usa competência real
    ]
    alerta_tasks = [
        _check_a1_duplicidade(ctx, session),
        _check_a2_fpo(ctx, session),
        _check_a3_cns(ctx, session),
    ]

    bloqueios_lists, alertas_lists = await asyncio.gather(
        asyncio.gather(*bloqueio_tasks),
        asyncio.gather(*alerta_tasks),
    )

    bloqueios = [item for sub in bloqueios_lists for item in sub]
    alertas   = [item for sub in alertas_lists   for item in sub]

    logger.info(
        "anti_glosa | proc=%s cnes=%s cbo=%s | bloqueios=%d alertas=%d",
        ctx.co_procedimento, ctx.cnes, ctx.cbo, len(bloqueios), len(alertas),
    )

    return ResultadoValidacao(
        aprovado=len(bloqueios) == 0,
        bloqueios=bloqueios,
        alertas=alertas,
    )
