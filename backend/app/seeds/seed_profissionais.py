"""Seed: profissional demo para apresentação a secretários de saúde.

Cenário: técnica de enfermagem (CBO 322205) vinculada ao PSF Vila Nova,
Três Pontas-MG (CNES 2139200) — estabelecimento real do banco SCNES.

O CNES fictício 0000001 é inserido apenas para dar suporte aos testes de
integração de anti-glosa (CNES_SEM_HAB sem habilitações reais).

Idempotente: usa INSERT ... ON CONFLICT DO NOTHING.

Execução:
    cd backend
    python -m app.seeds.seed_profissionais
"""

import asyncio
import uuid

from sqlalchemy import text

from app.db import async_session

# ── CNES real (PSF Vila Nova — Três Pontas/MG) ────────────────────────────────
# Dados reais provenientes da ingestão SCNES competência 202602.
# ON CONFLICT DO NOTHING: se a ingestão já inseriu o registro, não sobrescreve.

COMPETENCIA_CNES = "202602"   # competência da ingestão SCNES

ESTABELECIMENTO_DEMO = {
    "cnes": "2139200",
    "codufmun": "316940",       # Três Pontas-MG (código IBGE 6 dígitos)
    "cpf_cnpj": "25268012000122",
    "vinc_sus": None,
    "tp_unid": "05",            # PSF/Centro de Saúde
    "niv_hier": "1 ",
    "tp_prest": "M ",
    "atendamb": None,
    "nivate_a": None,
    "competen": COMPETENCIA_CNES,
}

PROFISSIONAL_CNES_DEMO = {
    "cnes": "2139200",
    "cns_prof": "709005854322518",   # CNS real do banco SCNES
    "nomeprof": "VANESSA APARECIDA GONCALVES",
    "cbo": "322205",                 # Técnico em Enfermagem
    "prof_sus": "S",
    "hora_amb": 0,
    "vinculac": None,
    "conselho": "06",                # COREN
    "competen": COMPETENCIA_CNES,
}

PROFISSIONAL_SISTEMA_DEMO = {
    "id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
    "cns": "709005854322518",
    "cbo": "322205",
    "cnes": "2139200",
    "competen": COMPETENCIA_CNES,
    "ativo": True,
}

# ── CNES fictício para testes de anti-glosa ───────────────────────────────────
# Não possui habilitações reais → testes de HABILITACAO_AUSENTE funcionam.
# Sem profissionais vinculados (testes usam cnes diretamente no contexto).

COMPETENCIA_FICTICIA = "202603"

ESTABELECIMENTO_TESTE = {
    "cnes": "0000001",
    "codufmun": "431780",
    "cpf_cnpj": "00000000000191",
    "vinc_sus": "S",
    "tp_unid": "01",
    "niv_hier": "01",
    "tp_prest": "10",
    "atendamb": "S",
    "nivate_a": "1",
    "competen": COMPETENCIA_FICTICIA,
}


async def seed() -> None:
    """Insere dados de demo e de teste de forma idempotente."""
    async with async_session() as session:
        async with session.begin():
            # 1. Estabelecimento real (PSF Três Pontas)
            await session.execute(
                text("""
                    INSERT INTO cnes_estabelecimentos
                        (cnes, codufmun, cpf_cnpj, vinc_sus, tp_unid, niv_hier,
                         tp_prest, atendamb, nivate_a, competen)
                    VALUES
                        (:cnes, :codufmun, :cpf_cnpj, :vinc_sus, :tp_unid, :niv_hier,
                         :tp_prest, :atendamb, :nivate_a, :competen)
                    ON CONFLICT (cnes, competen) DO NOTHING
                """),
                ESTABELECIMENTO_DEMO,
            )

            # 2. Estabelecimento fictício para testes
            await session.execute(
                text("""
                    INSERT INTO cnes_estabelecimentos
                        (cnes, codufmun, cpf_cnpj, vinc_sus, tp_unid, niv_hier,
                         tp_prest, atendamb, nivate_a, competen)
                    VALUES
                        (:cnes, :codufmun, :cpf_cnpj, :vinc_sus, :tp_unid, :niv_hier,
                         :tp_prest, :atendamb, :nivate_a, :competen)
                    ON CONFLICT (cnes, competen) DO NOTHING
                """),
                ESTABELECIMENTO_TESTE,
            )

            # 3. Profissional real no SCNES
            await session.execute(
                text("""
                    INSERT INTO cnes_profissionais
                        (cnes, cns_prof, cbo, nomeprof, prof_sus, hora_amb,
                         vinculac, conselho, competen)
                    VALUES
                        (:cnes, :cns_prof, :cbo, :nomeprof, :prof_sus, :hora_amb,
                         :vinculac, :conselho, :competen)
                    ON CONFLICT (cnes, cns_prof, cbo, competen) DO NOTHING
                """),
                PROFISSIONAL_CNES_DEMO,
            )

            # 4. Profissional no sistema operacional (UUID fixo para testes e frontend)
            # ON CONFLICT (id): atualiza o registro se o UUID já existe com dados antigos
            await session.execute(
                text("""
                    INSERT INTO profissionais (id, cns, cbo, cnes, competen, ativo)
                    VALUES (:id, :cns, :cbo, :cnes, :competen, :ativo)
                    ON CONFLICT (id) DO UPDATE
                      SET cns = EXCLUDED.cns,
                          cbo = EXCLUDED.cbo,
                          cnes = EXCLUDED.cnes,
                          competen = EXCLUDED.competen,
                          ativo = EXCLUDED.ativo
                """),
                PROFISSIONAL_SISTEMA_DEMO,
            )

            # 5. Remover profissionais fictícios excedentes (IDs 2–5) caso existam
            await session.execute(text("""
                DELETE FROM profissionais
                WHERE id IN (
                    '00000000-0000-0000-0000-000000000002'::uuid,
                    '00000000-0000-0000-0000-000000000003'::uuid,
                    '00000000-0000-0000-0000-000000000004'::uuid,
                    '00000000-0000-0000-0000-000000000005'::uuid
                )
            """))

        print("Seed concluído:")
        print("  - CNES 2139200 (PSF Vila Nova, Três Pontas-MG) inserido/já existente")
        print("  - CNES 0000001 (fictício para testes) inserido/já existente")
        print("  - Profissional Vanessa Gonçalves (CBO 322205) — UUID ...0001")
        print("  - Profissionais fictícios excedentes (IDs 2–5) removidos")


if __name__ == "__main__":
    asyncio.run(seed())
