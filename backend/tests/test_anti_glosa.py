"""Testes de integração — serviço de validação anti-glosa.

Cada teste verifica uma das 8 regras usando dados reais do banco (competência 202603).
Requer DATABASE_URL apontando para o banco Railway.
"""

import uuid
from datetime import date, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.anti_glosa import RegistroContext, validar_registro

# ── CNES fictício do seed (não tem habilitações/serviços CNES reais) ───────────
CNES_SEM_HAB = "0000001"
COMPETENCIA = "202603"

# UUID fictício do profissional seed (ANA LUCIA — CBO 225125)
PROFISSIONAL_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


# ── Fixtures de descoberta de dados reais ─────────────────────────────────────

@pytest_asyncio.fixture
async def dados_cbo(db_session: AsyncSession):
    """Descobre um par (co_procedimento, co_ocupacao) real em sigtap_rl_proc_ocupacao."""
    row = (await db_session.execute(text("""
        SELECT co_procedimento, co_ocupacao
        FROM sigtap_rl_proc_ocupacao
        WHERE dt_competencia = :comp
        LIMIT 1
    """), {"comp": COMPETENCIA})).fetchone()
    assert row, "Nenhum registro em sigtap_rl_proc_ocupacao para competência 202603"
    return {"co_procedimento": row.co_procedimento, "co_ocupacao": row.co_ocupacao}


@pytest_asyncio.fixture
async def dados_habilitacao(db_session: AsyncSession):
    """Descobre um procedimento que exige habilitação E um CNES que a possui."""
    row = (await db_session.execute(text("""
        SELECT rph.co_procedimento, ch.cnes
        FROM sigtap_rl_proc_habilitacao rph
        JOIN cnes_habilitacoes ch
          ON ch.sgruphab = rph.co_habilitacao
        WHERE rph.dt_competencia = :comp
          AND ch.cmpt_ini <= :comp
          AND (ch.cmpt_fim IS NULL OR ch.cmpt_fim >= :comp)
        LIMIT 1
    """), {"comp": COMPETENCIA})).fetchone()
    assert row, "Nenhum par procedimento×habilitação encontrado"
    return {"co_procedimento": row.co_procedimento, "cnes": row.cnes}


@pytest_asyncio.fixture
async def dados_instrumento(db_session: AsyncSession):
    """Descobre um procedimento e seu co_registro válido."""
    row = (await db_session.execute(text("""
        SELECT co_procedimento, co_registro
        FROM sigtap_rl_proc_registro
        WHERE dt_competencia = :comp
        LIMIT 1
    """), {"comp": COMPETENCIA})).fetchone()
    assert row, "Nenhum registro em sigtap_rl_proc_registro para competência 202603"
    return {"co_procedimento": row.co_procedimento, "co_registro": row.co_registro}


@pytest_asyncio.fixture
async def proc_sem_habilitacao(db_session: AsyncSession):
    """Descobre um procedimento que NÃO tem linhas em rl_proc_habilitacao."""
    row = (await db_session.execute(text("""
        SELECT p.co_procedimento
        FROM sigtap_procedimentos p
        WHERE p.dt_competencia = :comp
          AND NOT EXISTS (
              SELECT 1 FROM sigtap_rl_proc_habilitacao rph
              WHERE rph.co_procedimento = p.co_procedimento
                AND rph.dt_competencia = p.dt_competencia
          )
        LIMIT 1
    """), {"comp": COMPETENCIA})).fetchone()
    assert row, "Não encontrado procedimento sem habilitação"
    return row.co_procedimento


@pytest_asyncio.fixture
async def proc_sem_servico(db_session: AsyncSession):
    """Descobre um procedimento que NÃO tem linhas em rl_proc_servico."""
    row = (await db_session.execute(text("""
        SELECT p.co_procedimento
        FROM sigtap_procedimentos p
        WHERE p.dt_competencia = :comp
          AND NOT EXISTS (
              SELECT 1 FROM sigtap_rl_proc_servico rps
              WHERE rps.co_procedimento = p.co_procedimento
                AND rps.dt_competencia = p.dt_competencia
          )
        LIMIT 1
    """), {"comp": COMPETENCIA})).fetchone()
    assert row, "Não encontrado procedimento sem serviço"
    return row.co_procedimento


# ── Helper para contexto padrão ────────────────────────────────────────────────

def _ctx(**kwargs) -> RegistroContext:
    defaults = dict(
        co_procedimento="0301010110",
        cnes=CNES_SEM_HAB,
        cbo="225125",
        co_registro="01",
        dt_atendimento=date(2026, 3, 15),
        competencia=COMPETENCIA,
        cns_hash="a" * 64,
        quantidade=1,
        profissional_id=PROFISSIONAL_ID,
        cns_invalido=False,
    )
    defaults.update(kwargs)
    return RegistroContext(**defaults)


# ── Testes B1 — CBO ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_cbo_compativel(db_session: AsyncSession, dados_cbo):
    """CBO autorizado para o procedimento → sem bloqueio CBO_INCOMPATIVEL."""
    ctx = _ctx(
        co_procedimento=dados_cbo["co_procedimento"],
        cbo=dados_cbo["co_ocupacao"],
    )
    resultado = await validar_registro(ctx, db_session)
    codigos = [b.codigo for b in resultado.bloqueios]
    assert "CBO_INCOMPATIVEL" not in codigos


@pytest.mark.asyncio
async def test_cbo_incompativel(db_session: AsyncSession, dados_cbo):
    """CBO não autorizado para o procedimento → bloqueio CBO_INCOMPATIVEL."""
    ctx = _ctx(
        co_procedimento=dados_cbo["co_procedimento"],
        cbo="999999",  # CBO inexistente
    )
    resultado = await validar_registro(ctx, db_session)
    codigos = [b.codigo for b in resultado.bloqueios]
    assert "CBO_INCOMPATIVEL" in codigos
    assert not resultado.aprovado


# ── Testes B2 — Habilitação ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_habilitacao_ausente(db_session: AsyncSession, dados_habilitacao):
    """CNES sem habilitação exigida → bloqueio HABILITACAO_AUSENTE."""
    ctx = _ctx(
        co_procedimento=dados_habilitacao["co_procedimento"],
        cnes=CNES_SEM_HAB,  # CNES fictício sem habilitações reais
    )
    resultado = await validar_registro(ctx, db_session)
    codigos = [b.codigo for b in resultado.bloqueios]
    assert "HABILITACAO_AUSENTE" in codigos
    assert not resultado.aprovado


@pytest.mark.asyncio
async def test_sem_restricao_habilitacao(db_session: AsyncSession, proc_sem_habilitacao):
    """Procedimento sem linhas em rl_proc_habilitacao → sem bloqueio HABILITACAO_AUSENTE."""
    ctx = _ctx(
        co_procedimento=proc_sem_habilitacao,
        cnes=CNES_SEM_HAB,
    )
    resultado = await validar_registro(ctx, db_session)
    codigos = [b.codigo for b in resultado.bloqueios]
    assert "HABILITACAO_AUSENTE" not in codigos


# ── Testes B3 — Serviço ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_sem_restricao_servico(db_session: AsyncSession, proc_sem_servico):
    """Procedimento sem linhas em rl_proc_servico → sem bloqueio SERVICO_AUSENTE."""
    ctx = _ctx(
        co_procedimento=proc_sem_servico,
        cnes=CNES_SEM_HAB,
    )
    resultado = await validar_registro(ctx, db_session)
    codigos = [b.codigo for b in resultado.bloqueios]
    assert "SERVICO_AUSENTE" not in codigos


# ── Testes B4 — Instrumento ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_instrumento_invalido(db_session: AsyncSession, dados_instrumento):
    """co_registro errado para o procedimento → bloqueio INSTRUMENTO_INVALIDO."""
    co_registro_valido = dados_instrumento["co_registro"]
    co_registro_invalido = "02" if co_registro_valido == "01" else "01"

    # Verifica se o procedimento aceita apenas 1 instrumento (senão o teste não é válido)
    rows = (await db_session.execute(text("""
        SELECT co_registro FROM sigtap_rl_proc_registro
        WHERE co_procedimento = :co AND dt_competencia = :comp
    """), {"co": dados_instrumento["co_procedimento"], "comp": COMPETENCIA})).fetchall()

    instrumentos = {r.co_registro for r in rows}
    if co_registro_invalido in instrumentos:
        pytest.skip("Procedimento aceita ambos os instrumentos — teste não aplicável")

    ctx = _ctx(
        co_procedimento=dados_instrumento["co_procedimento"],
        co_registro=co_registro_invalido,
    )
    resultado = await validar_registro(ctx, db_session)
    codigos = [b.codigo for b in resultado.bloqueios]
    assert "INSTRUMENTO_INVALIDO" in codigos
    assert not resultado.aprovado


# ── Testes B5 — Retroatividade ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_retroatividade_ok(db_session: AsyncSession, proc_sem_habilitacao):
    """Data de atendimento dentro de 3 meses atrás → sem bloqueio RETROATIVIDADE_EXCEDIDA."""
    # Competência 202603: aceita 202603, 202602, 202601, 202512
    ctx = _ctx(
        co_procedimento=proc_sem_habilitacao,
        dt_atendimento=date(2026, 1, 10),  # competência 202601 — dentro das 4 aceitas
        competencia=COMPETENCIA,
    )
    resultado = await validar_registro(ctx, db_session)
    codigos = [b.codigo for b in resultado.bloqueios]
    assert "RETROATIVIDADE_EXCEDIDA" not in codigos


@pytest.mark.asyncio
async def test_retroatividade_excedida(db_session: AsyncSession, proc_sem_habilitacao):
    """Data de atendimento com 4+ meses atrás → bloqueio RETROATIVIDADE_EXCEDIDA."""
    # Competência 202603: o limite retroativo é 202512. Novembro/2025 já excede.
    ctx = _ctx(
        co_procedimento=proc_sem_habilitacao,
        dt_atendimento=date(2025, 11, 1),  # competência 202511 — fora das 4 aceitas
        competencia=COMPETENCIA,
    )
    resultado = await validar_registro(ctx, db_session)
    codigos = [b.codigo for b in resultado.bloqueios]
    assert "RETROATIVIDADE_EXCEDIDA" in codigos
    assert not resultado.aprovado


# ── Testes A1 — Duplicidade ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_duplicidade(db_session: AsyncSession, proc_sem_habilitacao):
    """Segundo registro idêntico → alerta DUPLICIDADE_SUSPEITA."""
    cns_hash_teste = "b" * 64
    reg_id = uuid.uuid4()

    # Insere registro original
    await db_session.execute(text("""
        INSERT INTO registros_producao
            (id, cns_enc, cns_hash, co_registro, cnes, co_procedimento,
             cbo, dt_atendimento, competencia, quantidade, status, criado_por)
        VALUES
            (:id, NULL, :cns_hash, '01', :cnes, :co_proc,
             '225125', '2026-03-15', :comp, 1, 'confirmado', :prof_id)
    """), {
        "id": reg_id,
        "cns_hash": cns_hash_teste,
        "cnes": CNES_SEM_HAB,
        "co_proc": proc_sem_habilitacao,
        "comp": COMPETENCIA,
        "prof_id": PROFISSIONAL_ID,
    })
    await db_session.commit()

    try:
        ctx = _ctx(
            co_procedimento=proc_sem_habilitacao,
            cns_hash=cns_hash_teste,
            cbo="225125",
            dt_atendimento=date(2026, 3, 15),
        )
        resultado = await validar_registro(ctx, db_session)
        codigos_alerta = [a.codigo for a in resultado.alertas]
        assert "DUPLICIDADE_SUSPEITA" in codigos_alerta
    finally:
        # Limpeza
        await db_session.execute(
            text("DELETE FROM registros_producao WHERE id = :id"),
            {"id": reg_id},
        )
        await db_session.commit()


# ── Testes A2 — FPO ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_fpo_excedido(db_session: AsyncSession, proc_sem_habilitacao):
    """Quantidade acima do teto programado → alerta FPO_EXCEDIDO."""
    fpo_id = uuid.uuid4()

    # Insere teto de 1 unidade
    await db_session.execute(text("""
        INSERT INTO fpo_programacao (id, cnes, co_procedimento, competencia, qt_aprovada)
        VALUES (:id, :cnes, :co_proc, :comp, 1)
        ON CONFLICT (cnes, co_procedimento, competencia) DO NOTHING
    """), {
        "id": fpo_id,
        "cnes": CNES_SEM_HAB,
        "co_proc": proc_sem_habilitacao,
        "comp": COMPETENCIA,
    })
    await db_session.commit()

    try:
        ctx = _ctx(
            co_procedimento=proc_sem_habilitacao,
            quantidade=2,  # excede o teto de 1
        )
        resultado = await validar_registro(ctx, db_session)
        codigos_alerta = [a.codigo for a in resultado.alertas]
        assert "FPO_EXCEDIDO" in codigos_alerta
    finally:
        # Limpeza
        await db_session.execute(text("""
            DELETE FROM fpo_programacao
            WHERE cnes = :cnes AND co_procedimento = :co_proc AND competencia = :comp
        """), {
            "cnes": CNES_SEM_HAB,
            "co_proc": proc_sem_habilitacao,
            "comp": COMPETENCIA,
        })
        await db_session.commit()
