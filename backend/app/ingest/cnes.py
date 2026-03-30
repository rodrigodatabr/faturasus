"""Ingestão do SCNES nas tabelas cnes_*.

Uso:
    cd backend
    PYTHONPATH=. python -m app.ingest.cnes \\
        --data-dir data/cnes/BASE_DE_DADOS_CNES_202602 \\
        --competencia 202602 \\
        --hb-dir data/cnes/HB \\
        --municipios 500570 316940 430770   # Naviraí-MS, Três Pontas-MG, Esteio-RS

Fontes:
  ST: tbEstabelecimento{AAMM}.csv      → cnes_estabelecimentos
  PF: tbCargaHorariaSus{AAMM}.csv      → cnes_profissionais
      + tbDadosProfissionalSus{AAMM}.csv (JOIN em memória para CNS + nome)
  SR: rlEstabServClass{AAMM}.csv       → cnes_servicos
  HB: HB{UF}{AA}{MM}.dbc por UF       → cnes_habilitacoes

--municipios filtra por CO_MUNICIPIO_GESTOR (IBGE 6 dígitos, sem dígito verificador).
Omitir --municipios ingere o Brasil inteiro (lento — ~15M registros PF).

Idempotente — ON CONFLICT DO UPDATE. Pode ser executado N vezes sem duplicar dados.
"""

import asyncio
import csv
import re
import sys
import tempfile
from pathlib import Path

from sqlalchemy import text

from app.db import async_session


# ── Helpers ────────────────────────────────────────────────────────────────────

def _cnes7(value: str) -> str:
    """Zero-fill p/ 7 chars. CNES nunca deve ser convertido para int."""
    return value.strip().zfill(7)


def _cnes_from_unidade(co_unidade: str) -> str:
    """Extrai CNES dos últimos 7 chars de CO_UNIDADE (31 chars)."""
    return co_unidade.strip()[-7:].zfill(7)


def _str_or_none(value: str, max_len: int | None = None) -> str | None:
    v = value.strip()
    if not v:
        return None
    if max_len:
        v = v[:max_len]
    return v


def _int_or_none(value: str) -> int | None:
    v = value.strip()
    if not v:
        return None
    try:
        return int(v)
    except ValueError:
        return None


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


# ── ST — Estabelecimentos ──────────────────────────────────────────────────────

async def _ingest_st(data_dir: str, competencia: str, municipios: set[str], session) -> None:
    """tbEstabelecimento{AAMM}.csv → cnes_estabelecimentos.

    Nota: o ZIP CSV tem schema diferente do .dbc por UF. Colunas como VINC_SUS,
    NIV_HIER, TP_PREST, ATENDAMB, NIVATE_A não existem — ficam NULL.
    Proxies usados: CO_MUNICIPIO_GESTOR→codufmun, TP_UNIDADE→tp_unid,
    TP_GESTAO→tp_prest, NIVEL_DEP→niv_hier.
    """
    path = Path(data_dir) / f"tbEstabelecimento{competencia}.csv"
    if not path.exists():
        print(f"  [AVISO] {path} não encontrado — cnes_estabelecimentos ignorado", file=sys.stderr)
        return

    rows = []
    with open(path, encoding="latin-1", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            codufmun = row.get("CO_MUNICIPIO_GESTOR", "").strip()
            if municipios and codufmun not in municipios:
                continue
            cnes = _cnes7(row.get("CO_CNES", ""))
            if not cnes.strip("0"):
                continue
            cpf_cnpj = _str_or_none(row.get("NU_CNPJ", ""), 14) or _str_or_none(row.get("NU_CPF", ""), 14)
            rows.append({
                "cnes": cnes,
                "codufmun": _str_or_none(codufmun, 6),
                "cpf_cnpj": cpf_cnpj,
                "vinc_sus": None,   # ausente no ZIP CSV
                "tp_unid": _str_or_none(row.get("TP_UNIDADE", ""), 2),
                "niv_hier": _str_or_none(row.get("NIVEL_DEP", ""), 2),
                "tp_prest": _str_or_none(row.get("TP_GESTAO", ""), 2),
                "atendamb": None,   # ausente no ZIP CSV
                "nivate_a": None,   # ausente no ZIP CSV
                "competen": competencia,
            })

    sql = """
        INSERT INTO cnes_estabelecimentos
            (cnes, codufmun, cpf_cnpj, vinc_sus, tp_unid, niv_hier, tp_prest,
             atendamb, nivate_a, competen)
        VALUES
            (:cnes, :codufmun, :cpf_cnpj, :vinc_sus, :tp_unid, :niv_hier, :tp_prest,
             :atendamb, :nivate_a, :competen)
        ON CONFLICT (cnes, competen)
        DO UPDATE SET
            codufmun  = EXCLUDED.codufmun,
            cpf_cnpj  = EXCLUDED.cpf_cnpj,
            vinc_sus  = EXCLUDED.vinc_sus,
            tp_unid   = EXCLUDED.tp_unid,
            niv_hier  = EXCLUDED.niv_hier,
            tp_prest  = EXCLUDED.tp_prest,
            atendamb  = EXCLUDED.atendamb,
            nivate_a  = EXCLUDED.nivate_a
    """
    await _executemany_batched(session, sql, rows, "cnes_estabelecimentos")


# ── PF — Profissionais ─────────────────────────────────────────────────────────

async def _ingest_pf(data_dir: str, competencia: str, session) -> None:
    """tbCargaHorariaSus + tbDadosProfissionalSus → cnes_profissionais.

    Filtro por município já aplicado via FK: só CNES presentes em cnes_estabelecimentos
    (que foram filtrados por município na etapa ST) são aceitos.
    Filtro SUS: upper(TP_SUS_NAO_SUS) == 'S'.
    """
    # Carregar CNES válidos (já filtrados por município na etapa ST)
    result = await session.execute(
        text("SELECT cnes FROM cnes_estabelecimentos WHERE competen = :c"),
        {"c": competencia},
    )
    cnes_validos: set[str] = {row[0] for row in result}
    print(f"  CNES válidos para PF: {len(cnes_validos)}")

    # Construir dict lookup CNS + nome via tbDadosProfissionalSus
    prof_path = Path(data_dir) / f"tbDadosProfissionalSus{competencia}.csv"
    if not prof_path.exists():
        print(f"  [AVISO] {prof_path} não encontrado — cnes_profissionais ignorado", file=sys.stderr)
        return

    print(f"  Carregando tbDadosProfissionalSus em memória...")
    prof_lookup: dict[str, tuple[str, str | None]] = {}
    with open(prof_path, encoding="latin-1", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            key = row.get("CO_PROFISSIONAL_SUS", "").strip()
            cns = _str_or_none(row.get("CO_CNS", ""), 15)
            nome = _str_or_none(row.get("NO_PROFISSIONAL", ""), 60)
            if key and cns:
                prof_lookup[key] = (cns, nome)
    print(f"  tbDadosProfissionalSus: {len(prof_lookup)} profissionais indexados")

    carga_path = Path(data_dir) / f"tbCargaHorariaSus{competencia}.csv"
    if not carga_path.exists():
        print(f"  [AVISO] {carga_path} não encontrado — cnes_profissionais ignorado", file=sys.stderr)
        return

    rows = []
    descartados = 0
    with open(carga_path, encoding="latin-1", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            if row.get("TP_SUS_NAO_SUS", "").strip().upper() != "S":
                continue
            cnes = _cnes_from_unidade(row.get("CO_UNIDADE", ""))
            if cnes not in cnes_validos:
                descartados += 1
                continue
            hash_prof = row.get("CO_PROFISSIONAL_SUS", "").strip()
            lookup = prof_lookup.get(hash_prof)
            if lookup is None:
                descartados += 1
                continue
            cns_prof, nomeprof = lookup
            rows.append({
                "cnes": cnes,
                "cns_prof": cns_prof,
                "cbo": row.get("CO_CBO", "").strip().zfill(6),
                "nomeprof": nomeprof,
                "prof_sus": "S",
                "hora_amb": _int_or_none(row.get("QT_CARGA_HORARIA_AMBULATORIAL", "")),
                "vinculac": _str_or_none(row.get("IND_VINCULACAO", ""), 6),
                "conselho": _str_or_none(row.get("CO_CONSELHO_CLASSE", ""), 2),
                "registro": _str_or_none(row.get("NU_REGISTRO", ""), 13),
                "competen": competencia,
            })

    if descartados:
        print(f"  [AVISO] {descartados} registros PF descartados (CNES fora do filtro ou sem CNS)", file=sys.stderr)

    sql = """
        INSERT INTO cnes_profissionais
            (cnes, cns_prof, cbo, nomeprof, prof_sus, hora_amb, vinculac, conselho, registro, competen)
        VALUES
            (:cnes, :cns_prof, :cbo, :nomeprof, :prof_sus, :hora_amb, :vinculac, :conselho, :registro, :competen)
        ON CONFLICT (cnes, cns_prof, cbo, competen)
        DO UPDATE SET
            nomeprof  = EXCLUDED.nomeprof,
            prof_sus  = EXCLUDED.prof_sus,
            hora_amb  = EXCLUDED.hora_amb,
            vinculac  = EXCLUDED.vinculac,
            conselho  = EXCLUDED.conselho,
            registro  = EXCLUDED.registro
    """
    await _executemany_batched(session, sql, rows, "cnes_profissionais")


# ── SR — Serviços ──────────────────────────────────────────────────────────────

async def _ingest_sr(data_dir: str, competencia: str, session) -> None:
    """rlEstabServClass{AAMM}.csv → cnes_servicos. Filtro: CO_AMBULATORIAL_SUS == '1'.

    Filtro por município via FK: só CNES presentes em cnes_estabelecimentos são aceitos.
    """
    path = Path(data_dir) / f"rlEstabServClass{competencia}.csv"
    if not path.exists():
        print(f"  [AVISO] {path} não encontrado — cnes_servicos ignorado", file=sys.stderr)
        return

    result = await session.execute(
        text("SELECT cnes FROM cnes_estabelecimentos WHERE competen = :c"),
        {"c": competencia},
    )
    cnes_validos: set[str] = {row[0] for row in result}

    rows = []
    descartados = 0
    with open(path, encoding="latin-1", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            if row.get("CO_AMBULATORIAL_SUS", "").strip() != "1":
                continue
            cnes = _cnes_from_unidade(row.get("CO_UNIDADE", ""))
            if cnes not in cnes_validos:
                descartados += 1
                continue
            rows.append({
                "cnes": cnes,
                "serv_esp": _str_or_none(row.get("CO_SERVICO", ""), 3),
                "class_sr": _str_or_none(row.get("CO_CLASSIFICACAO", ""), 3),
                "ambul": "S",
                "competen": competencia,
            })

    if descartados:
        print(f"  [AVISO] {descartados} registros SR com CNES fora do filtro — descartados", file=sys.stderr)

    sql = """
        INSERT INTO cnes_servicos (cnes, serv_esp, class_sr, ambul, competen)
        VALUES (:cnes, :serv_esp, :class_sr, :ambul, :competen)
        ON CONFLICT (cnes, serv_esp, class_sr, competen)
        DO UPDATE SET ambul = EXCLUDED.ambul
    """
    await _executemany_batched(session, sql, rows, "cnes_servicos")


# ── HB — Habilitações ──────────────────────────────────────────────────────────

_HB_PATTERN = re.compile(r"^HB[A-Z]{2}\d{4}\.dbc$", re.IGNORECASE)


async def _ingest_hb(hb_dir: str, session) -> None:
    """HB{UF}{AA}{MM}.dbc (todos na pasta) → cnes_habilitacoes.

    Pipeline: dbctodbf.DBCDecompress → arquivo .dbf temporário → dbfread.
    Filtro por município via FK: só CNES presentes em cnes_estabelecimentos são aceitos.
    """
    try:
        from dbctodbf import DBCDecompress
        from dbfread import DBF
    except ImportError as e:
        print(f"  [ERRO] Dependência ausente: {e}. Instale: pip install dbc-to-dbf dbfread", file=sys.stderr)
        sys.exit(1)

    hb_path = Path(hb_dir)
    dbc_files = sorted(p for p in hb_path.iterdir() if _HB_PATTERN.match(p.name))

    if not dbc_files:
        print(f"  [ERRO] Nenhum arquivo HB*.dbc encontrado em {hb_dir}", file=sys.stderr)
        sys.exit(1)

    # CNES válidos já filtrados por município (via ST)
    result = await session.execute(text("SELECT cnes FROM cnes_estabelecimentos"))
    cnes_validos: set[str] = {row[0] for row in result}

    total_rows = []
    descartados_hb = 0
    decompressor = DBCDecompress()

    for dbc_file in dbc_files:
        uf = dbc_file.name[2:4].upper()
        try:
            with tempfile.NamedTemporaryFile(suffix=".dbf", delete=False) as tmp:
                tmp_path = tmp.name
            decompressor.decompressFile(str(dbc_file), tmp_path)
            table = DBF(tmp_path, encoding="latin-1", ignore_missing_memofile=True)
            for record in table:
                cnes = str(record.get("CNES", "") or "").strip().zfill(7)
                sgruphab = str(record.get("SGRUPHAB", "") or "").strip()
                competen = str(record.get("COMPETEN", "") or "").strip()
                if not cnes.strip("0") or not sgruphab or not competen:
                    continue
                if cnes not in cnes_validos:
                    descartados_hb += 1
                    continue
                total_rows.append({
                    "cnes": cnes,
                    "sgruphab": sgruphab[:4],
                    "cmpt_ini": _str_or_none(str(record.get("CMPT_INI", "") or ""), 6),
                    "cmpt_fim": _str_or_none(str(record.get("CMPT_FIM", "") or ""), 6),
                    "portaria": _str_or_none(str(record.get("PORTARIA", "") or ""), 20),
                    "competen": competen[:6],
                })
            Path(tmp_path).unlink(missing_ok=True)
            print(f"  HB {uf}: ok ({len(total_rows)} acumulados)", end="\r")
        except Exception as exc:
            print(f"\n  [AVISO] Falha ao processar {dbc_file.name}: {exc}", file=sys.stderr)

    print()
    if descartados_hb:
        print(f"  [AVISO] {descartados_hb} registros HB com CNES fora do filtro — descartados", file=sys.stderr)

    sql = """
        INSERT INTO cnes_habilitacoes (cnes, sgruphab, cmpt_ini, cmpt_fim, portaria, competen)
        VALUES (:cnes, :sgruphab, :cmpt_ini, :cmpt_fim, :portaria, :competen)
        ON CONFLICT (cnes, sgruphab, competen)
        DO UPDATE SET
            cmpt_ini = EXCLUDED.cmpt_ini,
            cmpt_fim = EXCLUDED.cmpt_fim,
            portaria = EXCLUDED.portaria
    """
    await _executemany_batched(session, sql, total_rows, "cnes_habilitacoes")


# ── Entry point ────────────────────────────────────────────────────────────────

async def main(data_dir: str, competencia: str, hb_dir: str, municipios: set[str]) -> None:
    """Ingere 4 tabelas CNES na ordem FK-safe: ST → PF → SR → HB."""
    print(f"Iniciando ingestão SCNES — competência: {competencia}")
    print(f"  ZIP dir    : {data_dir}")
    print(f"  HB  dir    : {hb_dir}")
    if municipios:
        print(f"  Municípios : {', '.join(sorted(municipios))}")
    else:
        print(f"  Municípios : TODOS (nacional)")

    async with async_session() as session:
        async with session.begin():
            await _ingest_st(data_dir, competencia, municipios, session)
            await _ingest_pf(data_dir, competencia, session)
            await _ingest_sr(data_dir, competencia, session)
            await _ingest_hb(hb_dir, session)

    print("Ingestão SCNES concluída.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ingestão SCNES nas tabelas cnes_*")
    parser.add_argument("--data-dir", required=True, help="Pasta com CSVs do ZIP nacional CNES")
    parser.add_argument("--competencia", required=True, help="Competência AAAAMM (ex: 202602)")
    parser.add_argument("--hb-dir", required=True, help="Pasta com arquivos HB*.dbc por UF")
    parser.add_argument(
        "--municipios", nargs="+", default=[],
        help="Códigos IBGE 6 dígitos dos municípios a ingerir (ex: 500570 316940 430770). "
             "Omitir = Brasil inteiro.",
    )
    args = parser.parse_args()

    asyncio.run(main(args.data_dir, args.competencia, args.hb_dir, set(args.municipios)))
