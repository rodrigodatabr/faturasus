"""Dry-run do parser SIGTAP — sem banco, sem rede.

Lê os arquivos .txt e valida posicionamento de campos sem fazer UPSERT.
Útil para confirmar que o parser está correto antes de rodar contra o Railway.

Uso:
    cd backend
    PYTHONPATH=. python -m app.ingest.test_sigtap_dry_run <pasta_bdsia>

Exemplo:
    PYTHONPATH=. python -m app.ingest.test_sigtap_dry_run data/sigtap/TabelaUnificada_202603_v2603111027
"""

import sys
from pathlib import Path


def _parse_int(s: str) -> int | None:
    v = s.strip()
    if not v:
        return None
    n = int(v)
    return n if n != 0 else None


PARSERS = {
    "tb_financiamento.txt": (108, lambda l: {
        "co_financiamento": l[0:2],
        "no_financiamento": l[2:102].strip(),
        "dt_competencia": l[102:108],
    }),
    "tb_rubrica.txt": (112, lambda l: {
        "co_rubrica": l[0:6],
        "no_rubrica": l[6:106].strip(),
        "dt_competencia": l[106:112],
    }),
    "tb_registro.txt": (58, lambda l: {
        "co_registro": l[0:2],
        "no_registro": l[2:52].strip(),
        "dt_competencia": l[52:58],
    }),
    "tb_grupo.txt": (108, lambda l: {
        "co_grupo": l[0:2],
        "no_grupo": l[2:102].strip(),
        "dt_competencia": l[102:108],
    }),
    "tb_sub_grupo.txt": (110, lambda l: {
        "co_grupo": l[0:2],
        "co_sub_grupo": l[2:4],
        "no_sub_grupo": l[4:104].strip(),
        "dt_competencia": l[104:110],
    }),
    "tb_forma_organizacao.txt": (112, lambda l: {
        "co_grupo": l[0:2],
        "co_sub_grupo": l[2:4],
        "co_forma_organizacao": l[4:6],
        "no_forma_organizacao": l[6:106].strip(),
        "dt_competencia": l[106:112],
    }),
    "tb_ocupacao.txt": (156, lambda l: {
        "co_ocupacao": l[0:6],
        "no_ocupacao": l[6:156].strip(),
    }),
    "tb_habilitacao.txt": (160, lambda l: {
        "co_habilitacao": l[0:4],
        "no_habilitacao": l[4:154].strip(),
        "dt_competencia": l[154:160],
    }),
    "tb_grupo_habilitacao.txt": (274, lambda l: {
        "nu_grupo_habilitacao": l[0:4],
        "no_grupo_habilitacao": l[4:24].strip(),
        "ds_grupo_habilitacao": l[24:274].strip() or None,
    }),
    "tb_servico.txt": (129, lambda l: {
        "co_servico": l[0:3],
        "no_servico": l[3:123].strip(),
        "dt_competencia": l[123:129],
    }),
    "tb_servico_classificacao.txt": (162, lambda l: {
        "co_servico": l[0:3],
        "co_classificacao": l[3:6],
        "no_classificacao": l[6:156].strip(),
        "dt_competencia": l[156:162],
    }),
    "tb_cid.txt": (111, lambda l: {
        "co_cid": l[0:4],
        "no_cid": l[4:104].strip(),
        "tp_sexo": l[105:106].strip() or None,
    }),
    "tb_procedimento.txt": (336, lambda l: {
        "co_procedimento": l[0:10],
        "no_procedimento": l[10:260].strip(),
        "tp_complexidade": l[260:261].strip() or None,
        "tp_sexo": l[261:262].strip() or None,
        "qt_maxima_execucao": _parse_int(l[262:266]),
        "qt_pontos": _parse_int(l[270:274]),
        "vl_idade_minima": _parse_int(l[274:278]),
        "vl_idade_maxima": _parse_int(l[278:282]),
        "vl_sa": _parse_int(l[294:306]),
        "vl_sp": _parse_int(l[306:318]),
        "co_financiamento": l[318:320].strip() or None,
        "co_rubrica": l[320:326].strip() or None,
        "dt_competencia": l[330:336],
    }),
    "tb_descricao.txt": (4016, lambda l: {
        "co_procedimento": l[0:10],
        "ds_procedimento": l[10:4010].strip(),
        "dt_competencia": l[4010:4016],
    }),
    "rl_procedimento_ocupacao.txt": (22, lambda l: {
        "co_procedimento": l[0:10],
        "co_ocupacao": l[10:16],
        "dt_competencia": l[16:22],
    }),
    "rl_procedimento_registro.txt": (18, lambda l: {
        "co_procedimento": l[0:10],
        "co_registro": l[10:12],
        "dt_competencia": l[12:18],
    }),
    "rl_procedimento_habilitacao.txt": (24, lambda l: {
        "co_procedimento": l[0:10],
        "co_habilitacao": l[10:14],
        "nu_grupo_habilitacao": l[14:18],
        "dt_competencia": l[18:24],
    }),
    "rl_procedimento_servico.txt": (22, lambda l: {
        "co_procedimento": l[0:10],
        "co_servico": l[10:13],
        "co_classificacao": l[13:16],
        "dt_competencia": l[16:22],
    }),
    "rl_procedimento_cid.txt": (21, lambda l: {
        "co_procedimento": l[0:10],
        "co_cid": l[10:14],
        "st_principal": l[14:15].strip() or None,
        "dt_competencia": l[15:21],
    }),
    "rl_procedimento_compativel.txt": (35, lambda l: {
        "co_procedimento": l[0:10],
        "co_registro_principal": l[10:12],
        "co_procedimento_compativel": l[12:22],
        "co_registro_compativel": l[22:24],
        "tp_compatibilidade": l[24:25].strip() or None,
        "qt_permitida": _parse_int(l[25:29]),
        "dt_competencia": l[29:35],
    }),
}


def run(folder: str) -> None:
    errors = 0
    for fname, (min_len, parser) in PARSERS.items():
        path = Path(folder) / fname
        if not path.exists():
            print(f"  AUSENTE  {fname}")
            errors += 1
            continue

        with open(path, encoding="iso-8859-1", newline="") as f:
            lines = [l.rstrip("\r\n") for l in f if l.strip()]

        short = [i for i, l in enumerate(lines, 1) if len(l) < min_len]
        if short:
            print(f"  ERRO     {fname}: {len(short)} linhas curtas (esperado >= {min_len} chars), ex: linha {short[0]}")
            errors += 1
            continue

        # testa parser nas primeiras 3 linhas
        parse_error = None
        for i, line in enumerate(lines[:3], 1):
            try:
                row = parser(line)
                # verifica que dt_competencia (quando presente) é numérica
                if "dt_competencia" in row:
                    assert row["dt_competencia"].isdigit(), f"dt_competencia inválida: {row['dt_competencia']!r}"
            except Exception as e:
                parse_error = f"linha {i}: {e}"
                break

        if parse_error:
            print(f"  ERRO     {fname}: {parse_error}")
            errors += 1
        else:
            sample = parser(lines[0])
            first_key = next(iter(sample))
            print(f"  OK       {fname} ({len(lines)} linhas) — ex: {first_key}={sample[first_key]!r}")

    print()
    if errors:
        print(f"RESULTADO: {errors} erro(s) — corrigir antes de rodar a ingestão completa.")
        sys.exit(1)
    else:
        print("RESULTADO: todos os arquivos OK — pronto para ingestão.")
        print()
        print("Para ingerir no banco:")
        print(f"  cd backend && PYTHONPATH=. python -m app.ingest.sigtap {folder!r} 202603")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: PYTHONPATH=. python -m app.ingest.test_sigtap_dry_run <pasta_bdsia>")
        sys.exit(1)
    run(sys.argv[1])
