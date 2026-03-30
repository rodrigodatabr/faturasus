# Roadmap de Implementação — FaturaSUS

**Backend FastAPI:** Railway, serviço `faturasus` — `faturasus.up.railway.app`. FastAPI serve `frontend/dist/` via StaticFiles (Dockerfile multistage na raiz). Ver DEC-010.
**Domínio legado:** `faturasus-production.up.railway.app` serve o frontend estático antigo desconexo do backend — ignorar.

Estratégia: construir o núcleo técnico com dados mockados até ter um protótipo demonstrável de ponta a ponta. Esse protótipo é o argumento para obter o acordo de cooperação técnica com a SMS e viabilizar a integração real com o CADSUS.

## Escopo atual

| # | Módulo | Dependências | Obs |
|---|---|---|---|
| ~~0a.1~~ | ~~Análise do layout SIGTAP (BDSIA)~~ | — | ✅ `docs/layout_sigtap.md` — 41 tabelas mapeadas, 22 relevantes para BPA |
| ~~0a.2~~ | ~~Análise do layout SCNES (PF, HB, ST)~~ | — | ✅ `docs/layout_scnes.md` — layouts PF, HB, ST mapeados |
| ~~0b~~ | ~~FastAPI scaffold~~ | — | ✅ `backend/` criado — health check, CORS, Alembic, deploy config |
| ~~0c~~ | ~~Revisão de estratégia (anti-glosa + busca semântica)~~ | 0a, 0b | ✅ `docs/revisao_estrategia.md` — cruzamentos validados; PRD e layout_scnes corrigidos (join habilitação, SCNES SER, CNS AES-256-GCM) |
| ~~0d~~ | ~~Schema PostgreSQL + migration~~ | 0c | ✅ 28 tabelas (SIGTAP + CNES + operacional) em `backend/app/models/`; migration em `alembic/versions/0001_schema_inicial.py`; seed em `app/seeds/seed_profissionais.py`. Banco Railway: migration aplicada, pgvector ativo, 5 profissionais inseridos. |
| ~~1a~~ | ~~Ingestão manual SIGTAP~~ | 0c | ✅ 20 tabelas sigtap_* populadas no Railway (competência 202603): 4980 procedimentos, 194720 rl_proc_ocupacao, 2719 ocupações, 14242 CIDs, 7 financiamentos. Script idempotente (ON CONFLICT). |
| ~~1b.0~~ | ~~Revisão do modelo CNES vs. ZIP nacional~~ | 0c | ✅ Decisões: (1) ZIP usa CSV `;` Latin-1 — `pandas.read_csv`; (2) PF: JOIN `tbDadosProfissionalSus` para obter CNS real (hash `CO_PROFISSIONAL_SUS` descartado); (3) filtro SUS: `upper(TP_SUS_NAO_SUS)='S'`; (4) HB **ausente do ZIP** — obrigatório `.dbc` por UF via `dbc-to-dbf` (sem PySUS); (5) `registro VARCHAR(13)` adicionado ao modelo + migration `b676997e0213` aplicada no Railway. `layout_scnes.md` atualizado com mapeamento real. |
| ~~1b~~ | ~~Ingestão manual SCNES (PF + HB + SR)~~ | 1b.0 | ✅ `backend/app/ingest/cnes.py` — script idempotente com filtro `--municipios` (IBGE 6 dígitos). Ingerido para Naviraí-MS (500570), Três Pontas-MG (316940), Esteio-RS (430770): 903 estabelecimentos, 5.399 profissionais, 878 serviços, 39 habilitações. HB via `.dbc` local (27 UFs). Join serviço validado (17.431). **Join habilitação retorna 0 — bug pendente (ver 1c).** |
| ~~1c~~ | ~~Validação de joins anti-glosa com dados reais~~ | 1a, 1b | ✅ Join habilitação: `sgruphab = co_habilitacao` → 888 linhas. `nu_grupo_habilitacao` chega vazio no arquivo fonte do SIGTAP — não usar. Join serviço: 17.431 linhas. Comentários corrigidos em `models/sigtap.py`; `layout_scnes.md` e `DECISIONS.md` atualizados. |
| ~~2~~ | ~~Embeddings + busca semântica (pgvector)~~ | 1a, 1c | ✅ 4.980 procedimentos indexados no Railway (competência 202603). Migration `0002_ivfflat_embeddings` aplicada (`head`). `GET /busca/procedimentos` funcionando e consumido pelo frontend (`resultados[0]`). Backend exposto em `faturasus.up.railway.app`; frontend servido via StaticFiles (Dockerfile multistage). Ver DEC-010. |
| ~~3~~ | ~~Transcrição com Whisper~~ | 0b | ✅ `POST /transcricao` funcionando. Frontend grava áudio real, envia para o backend, exibe transcrição. Integrado no mesmo fluxo que o pgvector. |
| 4 | Pipeline de classificação com Claude Haiku | 2, 3 | Transcrição → pgvector top-15 → Haiku escolhe procedimento final. Hoje o frontend usa `resultados[0]` direto — substituir por chamada ao Haiku. Ver DEC-004. |
| 5 | CADSUS mock | 0b | Módulo isolado retornando dados fictícios; substituição cirúrgica depois. Não desbloqueia nem é desbloqueado pelo passo 4. |
| 6 | Validação anti-glosa | 1a, 1b, 1c, 5 | CBO, habilitação, serviço CNES, instrumento, compatibilidade, FPO, duplicidade |
| 7 | Geração e validação do arquivo BPA | 6 | Layout magnético DATASUS, separação PAB/MAC |
| 8 | Dashboard + drill-down | 7 | KPIs, correção inline pelo faturista |
| 9 | Exportação e histórico | 7, 8 | Consulta e reenvio de lotes |
| 10 | Cron SIGTAP diário | 7 | Só faz sentido automatizar após BPA validado |

## v2 — pós-protótipo (infraestrutura)

| # | Módulo | Dependências | Obs |
|---|---|---|---|
| v2.1 | Separar frontend em serviço dedicado | passo 9 | Mover React para Vercel/Cloudflare Pages; remover StaticFiles do FastAPI. Ver DEC-010. |

## Fora do escopo atual (depende de acordo SMS)

| # | Módulo | Dependências | Obs |
|---|---|---|---|
| 11 | Auth JWT + RBAC multi-tenant | 0–9 | Entra com o primeiro usuário real ou junto com CADSUS real |
| 11b | Onboarding de municípios clientes | 11 | Endpoint `POST /admin/tenants` + CLI `onboard_municipio` — persiste município no banco e dispara ingestão CNES (`cnes.py --municipios`) em background. Ver prompt deixado no fim da sessão 1b. |
| 12 | CADSUS v5 real | acordo SMS + 0–9 | Substitui o mock do passo 4 cirurgicamente |

## Decisão sobre o CADSUS

A integração real exige autorização formal da SMS. O mock (passo 4) deve ser isolado em um módulo dedicado para que a substituição seja cirúrgica. O protótipo funcional dos passos 0–10 é o argumento central para obter a adesão ao acordo.

## Investigações pendentes (resolver antes do passo indicado)

| Passo | Antes de... | Investigar |
|---|---|---|
| 5 | Calibrar prompt do Haiku | Medir recall@15 com casos reais: percentual de vezes em que o procedimento correto está nos top-15 do pgvector. Se insuficiente, aumentar para 20–30. Ver DEC-004. |
| 11 | Implementar Auth JWT + RBAC | Definir modelo de deploy: SaaS multi-tenant (coluna `tenant_id` em tabelas operacionais) vs. instância dedicada por prefeitura (schemas separados). Impacto direto no schema do banco. Ver DEC-008. |
| 12 | Integrar CADSUS real | Definir SHA-256 vs. AES-256-GCM para o CNS: SHA-256 é irreversível (não permite re-consultar o CADSUS depois); AES-256-GCM exige gestão de chave mas mantém o CNS recuperável. Ver DEC-009. |
