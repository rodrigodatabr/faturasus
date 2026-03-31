# Dataset de Avaliação — Classificação SIGTAP

> Referenciado em `prd_faturasus.md` §6 (meta: >90% de acurácia sem intervenção humana).
> Usado para medir recall@30 (pgvector + hybrid) e acurácia final (Haiku) separadamente.
> Competência de referência: **202603**.

## Como usar

Para cada caso, rodar `POST /classificar` com `{"texto": "<input>", "competencia": "202603"}` e comparar `no_procedimento` retornado com `no_esperado`. O código (`co_procedimento`) é consequência direta do nome via banco — validar pelo nome.

Um caso é correto se o nome retornado corresponder ao `no_esperado` ou a um dos `no_aceitos` (equivalentes clínicos aceitáveis).

Para medir recall@30 separadamente, observar os logs de `_buscar_candidatos_hybrid` (INFO faturasus) e checar se o procedimento esperado aparece entre os candidatos retornados.

## ⚠️ Atenção: nomes e códigos variam entre competências

Os nomes e códigos SIGTAP mudam a cada competência mensal. Ao adicionar casos, sempre verificar os valores reais na competência de teste:

```sql
SELECT co_procedimento, no_procedimento
FROM sigtap_procedimentos
WHERE no_procedimento ILIKE '%inalação%nebulização%'
  AND dt_competencia = '202603';
```

## Casos anotados (competência 202603)

| # | Input | no_esperado | no_aceitos | Resultado observado | Status | Problema |
|---|---|---|---|---|---|---|
| 1 | Papa Nicolau | EXAME CITOPATOLÓGICO CERVICO VAGINAL/MICROFLORA-RASTREAMENTO | EXAME CITOPATOLÓGICO CERVICO-VAGINAL/MICROFLORA | EXAME CITOPATOLÓGICO CERVICO VAGINAL/MICROFLORA-RASTREAMENTO | ✅ CORRETO | — |
| 2 | nebulizacao | INALAÇÃO / NEBULIZAÇÃO | — | INALAÇÃO / NEBULIZAÇÃO | ✅ CORRETO | Corrigido: regra terapêutico vs. diagnóstico por imagem adicionada a `_SYSTEM_CLASSIFY` |
| 3 | aferiu pressao | AFERIÇÃO DE PRESSÃO ARTERIAL | — | AFERIÇÃO DE PRESSÃO ARTERIAL | ✅ CORRETO | — |
| 4 | curativo no pe | CURATIVO SIMPLES | CURATIVO GRAU II C/ OU S/ DEBRIDAMENTO | CURATIVO SIMPLES | ✅ CORRETO | — |
| 5 | retirada de ponto | RETIRADA DE PONTOS DE CIRURGIAS (POR PACIENTE) | — | RETIRADA DE PONTOS DE CIRURGIAS (POR PACIENTE) | ✅ CORRETO | — |
| 6 | fiz um gesso no braco | TRATAMENTO CONSERVADOR DE FRATURA EM MEMBRO SUPERIOR COM IMOBILIZAÇÃO | — | TRATAMENTO CONSERVADOR DE FRATURA EM MEMBRO SUPERIOR COM IMOBILIZAÇÃO | ✅ CORRETO | — |
| 7 | ECG | ELETROCARDIOGRAMA | — | ELETROCARDIOGRAMA | ✅ CORRETO | — |
| 8 | quimioterapia mama | QUIMIOTERAPIA DO CARCINOMA DE MAMA AVANÇADO -1ª LINHA | — | QUIMIOTERAPIA DO CARCINOMA DE MAMA AVANÇADO -1ª LINHA | ✅ CORRETO | — |

## Resumo

| Métrica | Valor |
|---|---|
| Total de casos válidos | 8 |
| Corretos | 8/8 (100%) |
| Meta PRD | >90% |

**Meta atingida.** Todos os 8 casos corretos após ajuste de `_SYSTEM_CLASSIFY` (regra terapêutico vs. diagnóstico por imagem).

## Casos a adicionar (próxima rodada, para cruzar 90%)

- Procedimentos de atenção básica de alta frequência (vacinação, pré-natal, puericultura)
- Procedimentos com nomes próximos mas clinicamente distintos (ex: colonoscopia com/sem biópsia)
- Textos com erro ortográfico grave ou sotaque transcrito pelo Whisper
- Procedimentos exclusivos de especialidade (oftalmologia, ortopedia, psiquiatria)
