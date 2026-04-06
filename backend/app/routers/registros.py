"""Router POST /registros — persiste produção ambulatorial após validação anti-glosa."""

import hashlib
import uuid
from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.services.anti_glosa import GlosaItem, RegistroContext, validar_registro

router = APIRouter(tags=["registros"])


# ── Schemas ────────────────────────────────────────────────────────────────────

class RegistroInput(BaseModel):
    co_procedimento: str
    cnes: str
    cbo: str
    co_registro: str        # '01'=BPA-I, '02'=BPA-C
    dt_atendimento: date
    competencia: str        # AAAAMM
    cns: str                # CNS em texto plano — hash gerado aqui
    quantidade: int = 1
    profissional_id: UUID


class GlosaItemSchema(BaseModel):
    codigo: str
    mensagem: str
    detalhe: str


class RegistroResponse(BaseModel):
    aprovado: bool
    registro_id: Optional[UUID] = None
    bloqueios: list[GlosaItemSchema]
    alertas: list[GlosaItemSchema]


# ── Validação CNS ──────────────────────────────────────────────────────────────

def _validar_cns(cns: str) -> bool:
    """Valida o dígito verificador do CNS conforme algoritmo DATASUS.

    CNS definitivos: prefixo 1 ou 2 (gerados a partir do PIS/PASEP).
    CNS provisórios: prefixo 7, 8 ou 9 (gerados a partir do CPF ou dados cadastrais).
    """
    cns = cns.replace(" ", "").replace(".", "").replace("-", "")
    if len(cns) != 15 or not cns.isdigit():
        return False

    if cns[0] in ("1", "2"):
        # CNS definitivo — validação por PIS/PASEP
        pis = cns[:11]
        soma = sum(int(pis[i]) * (15 - i) for i in range(11))
        resto = soma % 11
        dsc = 0 if resto == 0 else 11 - resto

        if dsc == 0:
            resultado = f"{pis}0001"
        elif dsc == 1:
            soma2 = soma + 2
            resto2 = soma2 % 11
            dsc2 = 0 if resto2 == 0 else 11 - resto2
            resultado = f"{pis}1{dsc2:03d}"
        else:
            resultado = f"{pis}{dsc:04d}"

        return resultado == cns

    if cns[0] in ("7", "8", "9"):
        # CNS provisório — soma ponderada de 15 dígitos deve ser múltiplo de 11
        soma = sum(int(cns[i]) * (15 - i) for i in range(15))
        return soma % 11 == 0

    return False


# ── Endpoint ───────────────────────────────────────────────────────────────────

@router.post("/registros", response_model=RegistroResponse, status_code=201)
async def criar_registro(
    body: RegistroInput,
    session: AsyncSession = Depends(get_session),
) -> RegistroResponse:
    """Valida e persiste um registro de produção ambulatorial.

    Fluxo:
    1. Valida dígito verificador do CNS
    2. Gera cns_hash (SHA-256)
    3. Executa as 8 verificações anti-glosa em paralelo
    4. Se bloqueado → HTTP 422 (não persiste)
    5. Se aprovado → persiste em registros_producao e retorna HTTP 201
    """
    # 1. Valida CNS
    cns_limpo = body.cns.replace(" ", "")
    cns_invalido = not _validar_cns(cns_limpo)

    # 2. Gera hash SHA-256
    cns_hash = hashlib.sha256(cns_limpo.encode()).hexdigest()

    # 3. Monta contexto e executa validação
    ctx = RegistroContext(
        co_procedimento=body.co_procedimento,
        cnes=body.cnes,
        cbo=body.cbo,
        co_registro=body.co_registro,
        dt_atendimento=body.dt_atendimento,
        competencia=body.competencia,
        cns_hash=cns_hash,
        quantidade=body.quantidade,
        profissional_id=body.profissional_id,
        cns_invalido=cns_invalido,
    )

    resultado = await validar_registro(ctx, session)

    # Converter para schema de resposta
    def _to_schema(items: list[GlosaItem]) -> list[GlosaItemSchema]:
        return [GlosaItemSchema(codigo=g.codigo, mensagem=g.mensagem, detalhe=g.detalhe) for g in items]

    # 4. Bloqueado — retorna 422 sem persistir
    if not resultado.aprovado:
        raise HTTPException(
            status_code=422,
            detail=RegistroResponse(
                aprovado=False,
                registro_id=None,
                bloqueios=_to_schema(resultado.bloqueios),
                alertas=_to_schema(resultado.alertas),
            ).model_dump(),
        )

    # 5. Aprovado — persiste
    status = "pendente" if resultado.alertas else "confirmado"
    novo_id = uuid.uuid4()

    insert_sql = text("""
        INSERT INTO registros_producao
            (id, cns_enc, cns_hash, co_registro, cnes, co_procedimento,
             cbo, dt_atendimento, competencia, quantidade, status, criado_por)
        VALUES
            (:id, NULL, :cns_hash, :co_registro, :cnes, :co_procedimento,
             :cbo, :dt_atendimento, :competencia, :quantidade, :status, :criado_por)
    """)

    try:
        await session.execute(insert_sql, {
            "id": novo_id,
            "cns_hash": cns_hash,
            "co_registro": body.co_registro,
            "cnes": body.cnes,
            "co_procedimento": body.co_procedimento,
            "cbo": body.cbo,
            "dt_atendimento": body.dt_atendimento,
            "competencia": body.competencia,
            "quantidade": body.quantidade,
            "status": status,
            "criado_por": body.profissional_id,
        })
        await session.commit()
    except Exception as exc:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao persistir registro: {exc}") from exc

    return RegistroResponse(
        aprovado=True,
        registro_id=novo_id,
        bloqueios=[],
        alertas=_to_schema(resultado.alertas),
    )
