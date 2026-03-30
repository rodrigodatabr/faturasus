"""Seed: 5 profissionais fictícios vinculados a 1 CNES fictício.

Dados completamente inventados — sem CPF/CNS reais.
Idempotente: usa INSERT ... ON CONFLICT DO NOTHING.

Execução:
    cd backend
    python -m app.seeds.seed_profissionais
"""

import asyncio
import uuid

from sqlalchemy import text

from app.db import async_session
from app.models.cnes import CnesEstabelecimento, CnesProfissional
from app.models.operacional import Profissional

# ── Dados fictícios ────────────────────────────────────────────────────────────

COMPETENCIA = "202603"

ESTABELECIMENTO = {
    "cnes": "0000001",
    "codufmun": "431780",  # Porto Alegre - RS (código IBGE 6 dígitos)
    "cpf_cnpj": "00000000000191",
    "vinc_sus": "S",
    "tp_unid": "01",
    "niv_hier": "01",
    "tp_prest": "10",
    "atendamb": "S",
    "nivate_a": "1",
    "competen": COMPETENCIA,
}

# CNS com prefixo 7 (provisório) — sem validação real de dígito verificador
PROFISSIONAIS_CNES = [
    {
        "cnes": "0000001",
        "cns_prof": "700000000000001",
        "nomeprof": "ANA LUCIA FERREIRA",
        "cbo": "225125",  # Médico clínico
        "prof_sus": "S",
        "hora_amb": 20,
        "vinculac": "310105",
        "conselho": "05",  # CRM
        "competen": COMPETENCIA,
    },
    {
        "cnes": "0000001",
        "cns_prof": "700000000000002",
        "nomeprof": "CARLOS EDUARDO SOUZA",
        "cbo": "223505",  # Enfermeiro
        "prof_sus": "S",
        "hora_amb": 40,
        "vinculac": "310105",
        "conselho": "06",  # COREN
        "competen": COMPETENCIA,
    },
    {
        "cnes": "0000001",
        "cns_prof": "700000000000003",
        "nomeprof": "MARIANA COSTA LIMA",
        "cbo": "322230",  # Técnico em enfermagem
        "prof_sus": "S",
        "hora_amb": 40,
        "vinculac": "310105",
        "conselho": "06",  # COREN
        "competen": COMPETENCIA,
    },
    {
        "cnes": "0000001",
        "cns_prof": "700000000000004",
        "nomeprof": "ROBERTO ALVES NUNES",
        "cbo": "223605",  # Fisioterapeuta
        "prof_sus": "S",
        "hora_amb": 30,
        "vinculac": "310105",
        "conselho": "15",  # CREFITO
        "competen": COMPETENCIA,
    },
    {
        "cnes": "0000001",
        "cns_prof": "700000000000005",
        "nomeprof": "PATRICIA MELO SANTOS",
        "cbo": "251510",  # Psicólogo clínico
        "prof_sus": "S",
        "hora_amb": 20,
        "vinculac": "310105",
        "conselho": "07",  # CRP
        "competen": COMPETENCIA,
    },
]

# Tabela operacional profissionais — vincula CNS ao sistema
PROFISSIONAIS_SISTEMA = [
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
        "cns": "700000000000001",
        "cbo": "225125",
        "cnes": "0000001",
        "competen": COMPETENCIA,
        "ativo": True,
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000002"),
        "cns": "700000000000002",
        "cbo": "223505",
        "cnes": "0000001",
        "competen": COMPETENCIA,
        "ativo": True,
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000003"),
        "cns": "700000000000003",
        "cbo": "322230",
        "cnes": "0000001",
        "competen": COMPETENCIA,
        "ativo": True,
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000004"),
        "cns": "700000000000004",
        "cbo": "223605",
        "cnes": "0000001",
        "competen": COMPETENCIA,
        "ativo": True,
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000005"),
        "cns": "700000000000005",
        "cbo": "251510",
        "cnes": "0000001",
        "competen": COMPETENCIA,
        "ativo": True,
    },
]


async def seed() -> None:
    """Insere dados fictícios de forma idempotente."""
    async with async_session() as session:
        async with session.begin():
            # 1. Estabelecimento
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
                ESTABELECIMENTO,
            )

            # 2. Profissionais no SCNES
            for prof in PROFISSIONAIS_CNES:
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
                    prof,
                )

            # 3. Profissionais no sistema operacional
            for prof in PROFISSIONAIS_SISTEMA:
                await session.execute(
                    text("""
                        INSERT INTO profissionais (id, cns, cbo, cnes, competen, ativo)
                        VALUES (:id, :cns, :cbo, :cnes, :competen, :ativo)
                        ON CONFLICT (cns, cnes, cbo) DO NOTHING
                    """),
                    prof,
                )

        print(f"Seed concluído: 1 estabelecimento + {len(PROFISSIONAIS_CNES)} profissionais inseridos.")


if __name__ == "__main__":
    asyncio.run(seed())
