"""Ingestão do pacote BDSIA (SIGTAP/DATASUS) nas tabelas sigtap_*.

Uso:
    cd backend
    PYTHONPATH=. python -m app.ingest.sigtap <pasta_bdsia> <competencia>

Exemplo:
    PYTHONPATH=. python -m app.ingest.sigtap /tmp/bdsia_202603 202603

O script lê os arquivos .txt em layout posicional (ISO-8859-1) e faz UPSERT
em todas as 20 tabelas sigtap_*. Idempotente — rodar duas vezes não duplica dados.
Arquivos ausentes geram aviso e são ignorados (o script não aborta).
"""

import asyncio
import os
import sys
from pathlib import Path

from sqlalchemy import text

from app.db import async_session


# ── Helpers ────────────────────────────────────────────────────────────────────

def _parse_int(s: str) -> int | None:
    """Converte string com zero-fill para int. Retorna None se vazio ou zero."""
    v = s.strip()
    if not v:
        return None
    n = int(v)
    return n if n != 0 else None


def _open_txt(folder: str, filename: str):
    """Abre arquivo .txt do pacote BDSIA em ISO-8859-1.

    Retorna o objeto de arquivo aberto, ou None se o arquivo não existir
    (com aviso no stderr).
    """
    path = Path(folder) / filename
    if not path.exists():
        print(f"  [AVISO] Arquivo não encontrado: {path} — tabela ignorada", file=sys.stderr)
        return None
    return open(path, encoding="iso-8859-1", newline="")


async def _executemany_batched(session, sql: str, rows: list[dict], table: str) -> int:
    """Executa UPSERT em lotes de 500. Retorna total de linhas processadas."""
    batch_size = 500
    total = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        await session.execute(text(sql), batch)
        total += len(batch)
    print(f"  {table}: {total} linhas inseridas/atualizadas")
    return total


# ── Tabelas de domínio ─────────────────────────────────────────────────────────

async def _ingest_financiamento(folder: str, competencia: str, session) -> None:
    f = _open_txt(folder, "tb_financiamento.txt")
    if f is None:
        return
    rows = []
    with f:
        for line in f:
            line = line.rstrip("\r\n")
            if len(line) < 108:
                continue
            rows.append({
                "co_financiamento": line[0:2],
                "no_financiamento": line[2:102].strip(),
                "dt_competencia": line[102:108],
            })
    sql = """
        INSERT INTO sigtap_financiamentos (co_financiamento, no_financiamento, dt_competencia)
        VALUES (:co_financiamento, :no_financiamento, :dt_competencia)
        ON CONFLICT (co_financiamento, dt_competencia)
        DO UPDATE SET no_financiamento = EXCLUDED.no_financiamento
    """
    await _executemany_batched(session, sql, rows, "sigtap_financiamentos")


async def _ingest_rubrica(folder: str, competencia: str, session) -> None:
    f = _open_txt(folder, "tb_rubrica.txt")
    if f is None:
        return
    rows = []
    with f:
        for line in f:
            line = line.rstrip("\r\n")
            if len(line) < 112:
                continue
            rows.append({
                "co_rubrica": line[0:6],
                "no_rubrica": line[6:106].strip(),
                "dt_competencia": line[106:112],
            })
    sql = """
        INSERT INTO sigtap_rubricas (co_rubrica, no_rubrica, dt_competencia)
        VALUES (:co_rubrica, :no_rubrica, :dt_competencia)
        ON CONFLICT (co_rubrica, dt_competencia)
        DO UPDATE SET no_rubrica = EXCLUDED.no_rubrica
    """
    await _executemany_batched(session, sql, rows, "sigtap_rubricas")


async def _ingest_registro(folder: str, competencia: str, session) -> None:
    f = _open_txt(folder, "tb_registro.txt")
    if f is None:
        return
    rows = []
    with f:
        for line in f:
            line = line.rstrip("\r\n")
            if len(line) < 58:
                continue
            rows.append({
                "co_registro": line[0:2],
                "no_registro": line[2:52].strip(),
                "dt_competencia": line[52:58],
            })
    sql = """
        INSERT INTO sigtap_registros (co_registro, no_registro, dt_competencia)
        VALUES (:co_registro, :no_registro, :dt_competencia)
        ON CONFLICT (co_registro, dt_competencia)
        DO UPDATE SET no_registro = EXCLUDED.no_registro
    """
    await _executemany_batched(session, sql, rows, "sigtap_registros")


async def _ingest_grupo(folder: str, competencia: str, session) -> None:
    f = _open_txt(folder, "tb_grupo.txt")
    if f is None:
        return
    rows = []
    with f:
        for line in f:
            line = line.rstrip("\r\n")
            if len(line) < 108:
                continue
            rows.append({
                "co_grupo": line[0:2],
                "no_grupo": line[2:102].strip(),
                "dt_competencia": line[102:108],
            })
    sql = """
        INSERT INTO sigtap_grupos (co_grupo, no_grupo, dt_competencia)
        VALUES (:co_grupo, :no_grupo, :dt_competencia)
        ON CONFLICT (co_grupo, dt_competencia)
        DO UPDATE SET no_grupo = EXCLUDED.no_grupo
    """
    await _executemany_batched(session, sql, rows, "sigtap_grupos")


async def _ingest_subgrupo(folder: str, competencia: str, session) -> None:
    f = _open_txt(folder, "tb_sub_grupo.txt")
    if f is None:
        return
    rows = []
    with f:
        for line in f:
            line = line.rstrip("\r\n")
            if len(line) < 110:
                continue
            rows.append({
                "co_grupo": line[0:2],
                "co_sub_grupo": line[2:4],
                "no_sub_grupo": line[4:104].strip(),
                "dt_competencia": line[104:110],
            })
    sql = """
        INSERT INTO sigtap_subgrupos (co_sub_grupo, co_grupo, no_sub_grupo, dt_competencia)
        VALUES (:co_sub_grupo, :co_grupo, :no_sub_grupo, :dt_competencia)
        ON CONFLICT (co_sub_grupo, dt_competencia)
        DO UPDATE SET co_grupo = EXCLUDED.co_grupo,
                      no_sub_grupo = EXCLUDED.no_sub_grupo
    """
    await _executemany_batched(session, sql, rows, "sigtap_subgrupos")


async def _ingest_forma_organizacao(folder: str, competencia: str, session) -> None:
    f = _open_txt(folder, "tb_forma_organizacao.txt")
    if f is None:
        return
    rows = []
    with f:
        for line in f:
            line = line.rstrip("\r\n")
            if len(line) < 112:
                continue
            rows.append({
                "co_grupo": line[0:2],
                "co_sub_grupo": line[2:4],
                "co_forma_organizacao": line[4:6],
                "no_forma_organizacao": line[6:106].strip(),
                "dt_competencia": line[106:112],
            })
    sql = """
        INSERT INTO sigtap_formas_organizacao
            (co_forma_organizacao, co_grupo, co_sub_grupo, no_forma_organizacao, dt_competencia)
        VALUES
            (:co_forma_organizacao, :co_grupo, :co_sub_grupo, :no_forma_organizacao, :dt_competencia)
        ON CONFLICT (co_forma_organizacao, dt_competencia)
        DO UPDATE SET co_grupo = EXCLUDED.co_grupo,
                      co_sub_grupo = EXCLUDED.co_sub_grupo,
                      no_forma_organizacao = EXCLUDED.no_forma_organizacao
    """
    await _executemany_batched(session, sql, rows, "sigtap_formas_organizacao")


async def _ingest_ocupacao(folder: str, session) -> None:
    """tb_ocupacao — sem DT_COMPETENCIA. PK única: co_ocupacao."""
    f = _open_txt(folder, "tb_ocupacao.txt")
    if f is None:
        return
    rows = []
    with f:
        for line in f:
            line = line.rstrip("\r\n")
            if len(line) < 156:
                continue
            rows.append({
                "co_ocupacao": line[0:6],
                "no_ocupacao": line[6:156].strip(),
            })
    sql = """
        INSERT INTO sigtap_ocupacoes (co_ocupacao, no_ocupacao)
        VALUES (:co_ocupacao, :no_ocupacao)
        ON CONFLICT (co_ocupacao)
        DO UPDATE SET no_ocupacao = EXCLUDED.no_ocupacao
    """
    await _executemany_batched(session, sql, rows, "sigtap_ocupacoes")


async def _ingest_habilitacao(folder: str, competencia: str, session) -> None:
    f = _open_txt(folder, "tb_habilitacao.txt")
    if f is None:
        return
    rows = []
    with f:
        for line in f:
            line = line.rstrip("\r\n")
            if len(line) < 160:
                continue
            rows.append({
                "co_habilitacao": line[0:4],
                "no_habilitacao": line[4:154].strip(),
                "dt_competencia": line[154:160],
            })
    sql = """
        INSERT INTO sigtap_habilitacoes (co_habilitacao, no_habilitacao, dt_competencia)
        VALUES (:co_habilitacao, :no_habilitacao, :dt_competencia)
        ON CONFLICT (co_habilitacao, dt_competencia)
        DO UPDATE SET no_habilitacao = EXCLUDED.no_habilitacao
    """
    await _executemany_batched(session, sql, rows, "sigtap_habilitacoes")


async def _ingest_grupo_habilitacao(folder: str, session) -> None:
    """tb_grupo_habilitacao — sem DT_COMPETENCIA. PK única: nu_grupo_habilitacao."""
    f = _open_txt(folder, "tb_grupo_habilitacao.txt")
    if f is None:
        return
    rows = []
    with f:
        for line in f:
            line = line.rstrip("\r\n")
            if len(line) < 4:
                continue
            ds = line[24:274].strip() if len(line) >= 274 else line[24:].strip()
            rows.append({
                "nu_grupo_habilitacao": line[0:4],
                "no_grupo_habilitacao": line[4:24].strip() if len(line) >= 24 else line[4:].strip(),
                "ds_grupo_habilitacao": ds or None,
            })
    sql = """
        INSERT INTO sigtap_grupos_habilitacao
            (nu_grupo_habilitacao, no_grupo_habilitacao, ds_grupo_habilitacao)
        VALUES
            (:nu_grupo_habilitacao, :no_grupo_habilitacao, :ds_grupo_habilitacao)
        ON CONFLICT (nu_grupo_habilitacao)
        DO UPDATE SET no_grupo_habilitacao = EXCLUDED.no_grupo_habilitacao,
                      ds_grupo_habilitacao = EXCLUDED.ds_grupo_habilitacao
    """
    await _executemany_batched(session, sql, rows, "sigtap_grupos_habilitacao")


async def _ingest_servico(folder: str, competencia: str, session) -> None:
    f = _open_txt(folder, "tb_servico.txt")
    if f is None:
        return
    rows = []
    with f:
        for line in f:
            line = line.rstrip("\r\n")
            if len(line) < 129:
                continue
            rows.append({
                "co_servico": line[0:3],
                "no_servico": line[3:123].strip(),
                "dt_competencia": line[123:129],
            })
    sql = """
        INSERT INTO sigtap_servicos (co_servico, no_servico, dt_competencia)
        VALUES (:co_servico, :no_servico, :dt_competencia)
        ON CONFLICT (co_servico, dt_competencia)
        DO UPDATE SET no_servico = EXCLUDED.no_servico
    """
    await _executemany_batched(session, sql, rows, "sigtap_servicos")


async def _ingest_servico_classificacao(folder: str, competencia: str, session) -> None:
    f = _open_txt(folder, "tb_servico_classificacao.txt")
    if f is None:
        return
    rows = []
    with f:
        for line in f:
            line = line.rstrip("\r\n")
            if len(line) < 162:
                continue
            rows.append({
                "co_servico": line[0:3],
                "co_classificacao": line[3:6],
                "no_classificacao": line[6:156].strip(),
                "dt_competencia": line[156:162],
            })
    sql = """
        INSERT INTO sigtap_servicos_classificacao
            (co_servico, co_classificacao, no_classificacao, dt_competencia)
        VALUES
            (:co_servico, :co_classificacao, :no_classificacao, :dt_competencia)
        ON CONFLICT (co_servico, co_classificacao, dt_competencia)
        DO UPDATE SET no_classificacao = EXCLUDED.no_classificacao
    """
    await _executemany_batched(session, sql, rows, "sigtap_servicos_classificacao")


async def _ingest_cid(folder: str, session) -> None:
    """tb_cid — sem DT_COMPETENCIA. PK única: co_cid. Persiste apenas co_cid, no_cid, tp_sexo."""
    f = _open_txt(folder, "tb_cid.txt")
    if f is None:
        return
    rows = []
    with f:
        for line in f:
            line = line.rstrip("\r\n")
            if len(line) < 4:
                continue
            tp_sexo = line[105:106].strip() if len(line) >= 106 else None
            rows.append({
                "co_cid": line[0:4],
                "no_cid": line[4:104].strip() if len(line) >= 104 else line[4:].strip(),
                "tp_sexo": tp_sexo or None,
            })
    sql = """
        INSERT INTO sigtap_cids (co_cid, no_cid, tp_sexo)
        VALUES (:co_cid, :no_cid, :tp_sexo)
        ON CONFLICT (co_cid)
        DO UPDATE SET no_cid = EXCLUDED.no_cid,
                      tp_sexo = EXCLUDED.tp_sexo
    """
    await _executemany_batched(session, sql, rows, "sigtap_cids")


async def _ingest_procedimento(folder: str, competencia: str, session) -> None:
    """tb_procedimento — tabela central. Campos hospitalares omitidos (VL_SH, QT_DIAS_PERMANENCIA,
    QT_TEMPO_PERMANENCIA). Valores vl_sa e vl_sp armazenados em centavos (inteiro bruto).

    Layout real (336 chars/linha — VL_* são 12 chars cada, não 10):
      [0:10]   CO_PROCEDIMENTO
      [10:260] NO_PROCEDIMENTO
      [260]    TP_COMPLEXIDADE
      [261]    TP_SEXO
      [262:266] QT_MAXIMA_EXECUCAO
      [266:270] QT_DIAS_PERMANENCIA  — ignorado
      [270:274] QT_PONTOS
      [274:278] VL_IDADE_MINIMA
      [278:282] VL_IDADE_MAXIMA
      [282:294] VL_SH  — ignorado
      [294:306] VL_SA
      [306:318] VL_SP
      [318:320] CO_FINANCIAMENTO
      [320:326] CO_RUBRICA
      [326:330] QT_TEMPO_PERMANENCIA — ignorado
      [330:336] DT_COMPETENCIA
    """
    f = _open_txt(folder, "tb_procedimento.txt")
    if f is None:
        return
    rows = []
    with f:
        for line in f:
            line = line.rstrip("\r\n")
            if len(line) < 336:
                continue
            rows.append({
                "co_procedimento": line[0:10],
                "no_procedimento": line[10:260].strip(),
                "tp_complexidade": line[260:261].strip() or None,
                "tp_sexo": line[261:262].strip() or None,
                "qt_maxima_execucao": _parse_int(line[262:266]),
                # [266:270] = QT_DIAS_PERMANENCIA — ignorado
                "qt_pontos": _parse_int(line[270:274]),
                "vl_idade_minima": _parse_int(line[274:278]),
                "vl_idade_maxima": _parse_int(line[278:282]),
                # [282:294] = VL_SH (12 chars) — ignorado
                "vl_sa": _parse_int(line[294:306]),
                "vl_sp": _parse_int(line[306:318]),
                "co_financiamento": line[318:320].strip() or None,
                "co_rubrica": line[320:326].strip() or None,
                # [326:330] = QT_TEMPO_PERMANENCIA — ignorado
                "dt_competencia": line[330:336],
            })
    sql = """
        INSERT INTO sigtap_procedimentos (
            co_procedimento, no_procedimento, tp_complexidade, tp_sexo,
            qt_maxima_execucao, qt_pontos, vl_idade_minima, vl_idade_maxima,
            vl_sa, vl_sp, co_financiamento, co_rubrica, dt_competencia
        )
        VALUES (
            :co_procedimento, :no_procedimento, :tp_complexidade, :tp_sexo,
            :qt_maxima_execucao, :qt_pontos, :vl_idade_minima, :vl_idade_maxima,
            :vl_sa, :vl_sp, :co_financiamento, :co_rubrica, :dt_competencia
        )
        ON CONFLICT (co_procedimento, dt_competencia)
        DO UPDATE SET
            no_procedimento   = EXCLUDED.no_procedimento,
            tp_complexidade   = EXCLUDED.tp_complexidade,
            tp_sexo           = EXCLUDED.tp_sexo,
            qt_maxima_execucao = EXCLUDED.qt_maxima_execucao,
            qt_pontos         = EXCLUDED.qt_pontos,
            vl_idade_minima   = EXCLUDED.vl_idade_minima,
            vl_idade_maxima   = EXCLUDED.vl_idade_maxima,
            vl_sa             = EXCLUDED.vl_sa,
            vl_sp             = EXCLUDED.vl_sp,
            co_financiamento  = EXCLUDED.co_financiamento,
            co_rubrica        = EXCLUDED.co_rubrica
    """
    await _executemany_batched(session, sql, rows, "sigtap_procedimentos")


async def _ingest_descricao(folder: str, competencia: str, session) -> None:
    f = _open_txt(folder, "tb_descricao.txt")
    if f is None:
        return
    rows = []
    with f:
        for line in f:
            line = line.rstrip("\r\n")
            if len(line) < 4016:
                continue
            rows.append({
                "co_procedimento": line[0:10],
                "ds_procedimento": line[10:4010].strip(),
                "dt_competencia": line[4010:4016],
            })
    sql = """
        INSERT INTO sigtap_descricoes (co_procedimento, ds_procedimento, dt_competencia)
        VALUES (:co_procedimento, :ds_procedimento, :dt_competencia)
        ON CONFLICT (co_procedimento, dt_competencia)
        DO UPDATE SET ds_procedimento = EXCLUDED.ds_procedimento
    """
    await _executemany_batched(session, sql, rows, "sigtap_descricoes")


# ── Tabelas de relacionamento ──────────────────────────────────────────────────

async def _ingest_rl_proc_ocupacao(folder: str, competencia: str, session) -> None:
    f = _open_txt(folder, "rl_procedimento_ocupacao.txt")
    if f is None:
        return
    rows = []
    with f:
        for line in f:
            line = line.rstrip("\r\n")
            if len(line) < 22:
                continue
            rows.append({
                "co_procedimento": line[0:10],
                "co_ocupacao": line[10:16],
                "dt_competencia": line[16:22],
            })
    sql = """
        INSERT INTO sigtap_rl_proc_ocupacao (co_procedimento, co_ocupacao, dt_competencia)
        VALUES (:co_procedimento, :co_ocupacao, :dt_competencia)
        ON CONFLICT (co_procedimento, co_ocupacao, dt_competencia)
        DO NOTHING
    """
    await _executemany_batched(session, sql, rows, "sigtap_rl_proc_ocupacao")


async def _ingest_rl_proc_registro(folder: str, competencia: str, session) -> None:
    f = _open_txt(folder, "rl_procedimento_registro.txt")
    if f is None:
        return
    rows = []
    with f:
        for line in f:
            line = line.rstrip("\r\n")
            if len(line) < 18:
                continue
            rows.append({
                "co_procedimento": line[0:10],
                "co_registro": line[10:12],
                "dt_competencia": line[12:18],
            })
    sql = """
        INSERT INTO sigtap_rl_proc_registro (co_procedimento, co_registro, dt_competencia)
        VALUES (:co_procedimento, :co_registro, :dt_competencia)
        ON CONFLICT (co_procedimento, co_registro, dt_competencia)
        DO NOTHING
    """
    await _executemany_batched(session, sql, rows, "sigtap_rl_proc_registro")


async def _ingest_rl_proc_habilitacao(folder: str, competencia: str, session) -> None:
    f = _open_txt(folder, "rl_procedimento_habilitacao.txt")
    if f is None:
        return
    rows = []
    with f:
        for line in f:
            line = line.rstrip("\r\n")
            if len(line) < 24:
                continue
            rows.append({
                "co_procedimento": line[0:10],
                "co_habilitacao": line[10:14],
                "nu_grupo_habilitacao": line[14:18],
                "dt_competencia": line[18:24],
            })
    sql = """
        INSERT INTO sigtap_rl_proc_habilitacao
            (co_procedimento, co_habilitacao, nu_grupo_habilitacao, dt_competencia)
        VALUES
            (:co_procedimento, :co_habilitacao, :nu_grupo_habilitacao, :dt_competencia)
        ON CONFLICT (co_procedimento, co_habilitacao, nu_grupo_habilitacao, dt_competencia)
        DO NOTHING
    """
    await _executemany_batched(session, sql, rows, "sigtap_rl_proc_habilitacao")


async def _ingest_rl_proc_servico(folder: str, competencia: str, session) -> None:
    f = _open_txt(folder, "rl_procedimento_servico.txt")
    if f is None:
        return
    rows = []
    with f:
        for line in f:
            line = line.rstrip("\r\n")
            if len(line) < 22:
                continue
            rows.append({
                "co_procedimento": line[0:10],
                "co_servico": line[10:13],
                "co_classificacao": line[13:16],
                "dt_competencia": line[16:22],
            })
    sql = """
        INSERT INTO sigtap_rl_proc_servico
            (co_procedimento, co_servico, co_classificacao, dt_competencia)
        VALUES
            (:co_procedimento, :co_servico, :co_classificacao, :dt_competencia)
        ON CONFLICT (co_procedimento, co_servico, co_classificacao, dt_competencia)
        DO NOTHING
    """
    await _executemany_batched(session, sql, rows, "sigtap_rl_proc_servico")


async def _ingest_rl_proc_cid(folder: str, competencia: str, session) -> None:
    f = _open_txt(folder, "rl_procedimento_cid.txt")
    if f is None:
        return
    rows = []
    with f:
        for line in f:
            line = line.rstrip("\r\n")
            if len(line) < 21:
                continue
            rows.append({
                "co_procedimento": line[0:10],
                "co_cid": line[10:14],
                "st_principal": line[14:15].strip() or None,
                "dt_competencia": line[15:21],
            })
    sql = """
        INSERT INTO sigtap_rl_proc_cid (co_procedimento, co_cid, st_principal, dt_competencia)
        VALUES (:co_procedimento, :co_cid, :st_principal, :dt_competencia)
        ON CONFLICT (co_procedimento, co_cid, dt_competencia)
        DO UPDATE SET st_principal = EXCLUDED.st_principal
    """
    await _executemany_batched(session, sql, rows, "sigtap_rl_proc_cid")


async def _ingest_rl_proc_compativel(folder: str, competencia: str, session) -> None:
    f = _open_txt(folder, "rl_procedimento_compativel.txt")
    if f is None:
        return
    rows = []
    with f:
        for line in f:
            line = line.rstrip("\r\n")
            if len(line) < 35:
                continue
            rows.append({
                "co_procedimento": line[0:10],
                "co_registro_principal": line[10:12],
                "co_procedimento_compativel": line[12:22],
                "co_registro_compativel": line[22:24],
                "tp_compatibilidade": line[24:25].strip() or None,
                "qt_permitida": _parse_int(line[25:29]),
                "dt_competencia": line[29:35],
            })
    sql = """
        INSERT INTO sigtap_rl_proc_compativel (
            co_procedimento, co_registro_principal, co_procedimento_compativel,
            co_registro_compativel, tp_compatibilidade, qt_permitida, dt_competencia
        )
        VALUES (
            :co_procedimento, :co_registro_principal, :co_procedimento_compativel,
            :co_registro_compativel, :tp_compatibilidade, :qt_permitida, :dt_competencia
        )
        ON CONFLICT (
            co_procedimento, co_registro_principal,
            co_procedimento_compativel, co_registro_compativel, dt_competencia
        )
        DO UPDATE SET
            tp_compatibilidade = EXCLUDED.tp_compatibilidade,
            qt_permitida       = EXCLUDED.qt_permitida
    """
    await _executemany_batched(session, sql, rows, "sigtap_rl_proc_compativel")


# ── Entry point ────────────────────────────────────────────────────────────────

async def main(folder: str, competencia: str) -> None:
    """Ingere todas as tabelas SIGTAP na ordem FK-safe."""
    print(f"Iniciando ingestão BDSIA — pasta: {folder!r}, competência: {competencia}")

    async with async_session() as session:
        async with session.begin():
            # Domínio — sem dependências entre si (exceto hierarquia)
            await _ingest_financiamento(folder, competencia, session)
            await _ingest_rubrica(folder, competencia, session)
            await _ingest_registro(folder, competencia, session)
            await _ingest_grupo(folder, competencia, session)
            await _ingest_subgrupo(folder, competencia, session)
            await _ingest_forma_organizacao(folder, competencia, session)
            await _ingest_ocupacao(folder, session)
            await _ingest_habilitacao(folder, competencia, session)
            await _ingest_grupo_habilitacao(folder, session)
            await _ingest_servico(folder, competencia, session)
            await _ingest_servico_classificacao(folder, competencia, session)
            await _ingest_cid(folder, session)

            # Tabela central — depende de financiamento e rubrica
            await _ingest_procedimento(folder, competencia, session)
            await _ingest_descricao(folder, competencia, session)

            # Relacionamentos — dependem de procedimento e das tabelas de domínio
            await _ingest_rl_proc_ocupacao(folder, competencia, session)
            await _ingest_rl_proc_registro(folder, competencia, session)
            await _ingest_rl_proc_habilitacao(folder, competencia, session)
            await _ingest_rl_proc_servico(folder, competencia, session)
            await _ingest_rl_proc_cid(folder, competencia, session)
            await _ingest_rl_proc_compativel(folder, competencia, session)

    print("Ingestão concluída.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: PYTHONPATH=. python -m app.ingest.sigtap <pasta_bdsia> <competencia>")
        print("Exemplo: PYTHONPATH=. python -m app.ingest.sigtap /tmp/bdsia 202603")
        sys.exit(1)

    asyncio.run(main(sys.argv[1], sys.argv[2]))
