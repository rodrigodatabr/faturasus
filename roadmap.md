# Roadmap de Implementação — FaturaSUS

**Backend FastAPI:** Railway, serviço `faturasus` — `faturasus.up.railway.app`. FastAPI serve `frontend/dist/` via StaticFiles (Dockerfile multistage na raiz). Ver DEC-010.
**Domínio legado:** `faturasus-production.up.railway.app` serve o frontend estático antigo desconexo do backend — ignorar.

Estratégia: construir o núcleo técnico com dados mockados até ter um protótipo demonstrável de ponta a ponta. Esse protótipo é o argumento para obter o acordo de cooperação técnica com a SMS e viabilizar a integração real com o CADSUS.

**Estratégia de demo (pré-acordo SMS):** paciente hardcoded (Maria Aparecida da Silva) é suficiente — o scan de cartão SUS e a integração CADSUS real dependem de autorização formal da SMS. O app abre diretamente no step 1 (paciente já identificado), demonstrando o fluxo de valor sem expor a limitação. O scan de cartão aparece apenas como "adicionar próximo paciente" após a confirmação do registro — ponto em que o cliente já passou pelo anti-glosa e se encantou. Mock de CADSUS isolado entra junto com o primeiro usuário real ou com o acordo SMS. O protótipo funcional dos passos 0–5 é o argumento central para obter a adesão ao acordo.

---

## Escopo atual

### Concluído

- ✅ **0a.1 — Análise do layout SIGTAP (BDSIA)** — `docs/layout_sigtap.md`: 41 tabelas mapeadas, 22 relevantes para BPA
- ✅ **0a.2 — Análise do layout SCNES (PF, HB, ST)** — `docs/layout_scnes.md`: layouts PF, HB, ST mapeados
- ✅ **0b — FastAPI scaffold** — `backend/` criado: health check, CORS, Alembic, deploy config
- ✅ **0c — Revisão de estratégia (anti-glosa + busca semântica)** — `docs/revisao_estrategia.md`: cruzamentos validados; PRD e layout_scnes corrigidos (join habilitação, SCNES SER, CNS AES-256-GCM)
- ✅ **0d — Schema PostgreSQL + migration** — 28 tabelas (SIGTAP + CNES + operacional) em `backend/app/models/`; migration em `alembic/versions/0001_schema_inicial.py`; seed em `app/seeds/seed_profissionais.py`. Banco Railway: migration aplicada, pgvector ativo.
- ✅ **1a — Ingestão manual SIGTAP** — 20 tabelas sigtap_* populadas no Railway (competência 202603): 4980 procedimentos, 194720 rl_proc_ocupacao, 2719 ocupações, 14242 CIDs, 7 financiamentos. Script idempotente (ON CONFLICT).
- ✅ **1b.0 — Revisão do modelo CNES vs. ZIP nacional** — Decisões: (1) ZIP usa CSV `;` Latin-1 — `pandas.read_csv`; (2) PF: JOIN `tbDadosProfissionalSus` para obter CNS real (hash `CO_PROFISSIONAL_SUS` descartado); (3) filtro SUS: `upper(TP_SUS_NAO_SUS)='S'`; (4) HB **ausente do ZIP** — obrigatório `.dbc` por UF via `dbc-to-dbf` (sem PySUS); (5) `registro VARCHAR(13)` adicionado ao modelo + migration `b676997e0213` aplicada no Railway. `layout_scnes.md` atualizado com mapeamento real.
- ✅ **1b — Ingestão manual SCNES (PF + HB + SR)** — `backend/app/ingest/cnes.py`: script idempotente com filtro `--municipios` (IBGE 6 dígitos). Ingerido para Naviraí-MS (500570), Três Pontas-MG (316940), Esteio-RS (430770): 903 estabelecimentos, 5.399 profissionais, 878 serviços, 39 habilitações. HB via `.dbc` local (27 UFs). Join serviço validado (17.431). **Join habilitação retorna 0 — bug pendente (ver 1c).**
- ✅ **1c — Validação de joins anti-glosa com dados reais** — Join habilitação: `sgruphab = co_habilitacao` → 888 linhas. `nu_grupo_habilitacao` chega vazio no arquivo fonte do SIGTAP — não usar. Join serviço: 17.431 linhas. Comentários corrigidos em `models/sigtap.py`; `layout_scnes.md` e `DECISIONS.md` atualizados.
- ✅ **2 — Embeddings + busca semântica (pgvector)** — 4.980 procedimentos indexados no Railway (competência 202603). Migration `0002_ivfflat_embeddings` aplicada (`head`). `GET /busca/procedimentos` funcionando e consumido pelo frontend (`resultados[0]`). Backend exposto em `faturasus.up.railway.app`; frontend servido via StaticFiles (Dockerfile multistage). Ver DEC-010.
- ✅ **3 — Transcrição com Whisper** — `POST /transcricao` funcionando. Frontend grava áudio real, envia para o backend, exibe transcrição. Integrado no mesmo fluxo que o pgvector.
- ✅ **4 — Pipeline de classificação com Claude Haiku** — `POST /classificar`: query expansion (Haiku) → embedding → pgvector top-15 → Haiku classifica. Frontend substituiu `GET /busca/procedimentos` + `resultados[0]` por `POST /classificar`. Fix: `_extrair_json()` remove markdown fence da resposta do Haiku. Ver DEC-004.
- ✅ **5 — Refinamentos de frontend para demo** — App abre no step 1 (paciente hardcoded já identificado). Botão "Escanear cartão" substituído por "Adicionar próximo paciente" no dashboard pós-confirmação (com label explicando que é integração futura). Desambiguação baseada no procedimento classificado pelo Haiku (não hardcoded). Data dinâmica. Input de texto do rodapé removido (não funcional).
- ✅ **5b — Revisão da estratégia de retrieval SIGTAP** — 8/8 (100%) no golden set (competência 202603). TOP_K 15→30; hybrid search (pgvector + substring fallback com RRF); prompts revisados (query expansion + orientação terapêutico vs. diagnóstico por imagem em `_SYSTEM_CLASSIFY`). Caso resolvido: "nebulizacao" → INALAÇÃO/NEBULIZAÇÃO. Ver DEC-011, `docs/evals_classificacao.md`.
- ✅ **5b.1 — Ajuste do classificador: procedimento vs. medicamento/insumo** *(dep: 5b)* — Testes em produção revelaram 2 erros persistentes: (1) "Nebulização" → TOBRAMICINA (medicamento) em vez de INALAÇÃO/NEBULIZAÇÃO (procedimento); (2) "Injeção no joelho" → RETIRADA DE CORPO ESTRANHO em vez de INFILTRAÇÃO ARTICULAR. Raiz: `_SYSTEM_CLASSIFY` não distingue procedimento clínico de medicamento/insumo. Também adicionar glicemia capilar ao golden set (resultado discutível: retornou curva glicêmica em vez de glicemia pontual). Ver prompt no fim deste arquivo.
- ✅ **6 — Validação anti-glosa** *(dep: 1a, 1b, 1c, 5b.1)* — CBO, habilitação, serviço CNES, instrumento, compatibilidade, FPO, duplicidade. `POST /registros` com 8 verificações. Ver `docs/prompt_passo6_anti_glosa.md` e `docs/anti_glosa_fontes_normativas.md`.
- ✅ **6b — Preparação da demo anti-glosa** *(dep: 6)* — Cenário curado com dados reais do banco: Vanessa Gonçalves (CBO 322205, técnica de enfermagem) no PSF Vila Nova — Três Pontas/MG (CNES 2139200). Seed simplificado para 1 profissional. Frontend atualizado. Roteiro documentado em `docs/roteiro_demo_anti_glosa.md`: aferição de PA, glicemia capilar e coleta de material passam; consulta médica (CBO incompatível) e biópsia de corpo vertebral (habilitação ausente) bloqueiam.
- ✅ **7a — Mapeamento MAC/FAEC no banco** *(independente do fluxo principal — prospecção/ROI)* — View `vw_procedimentos_financiamento` criada via migration `0003_financiamento_view`. Join direto em `sigtap_procedimentos.co_financiamento` (não existe tabela `sigtap_rl_proc_financiamento`). Resultado: 4.980 procedimentos — MAC (06): 3.681 | FAEC (04): 495 | AB (01): 191 | Farmácia (02): 359 | Incentivo MAC (05): 57 | Vigilância (07): 185 | Gestão (08): 12. `vl_unitario_sigtap = (vl_sa + vl_sp) / 100.0`. Ver `docs/prompt_diagnostico_subregistro.md`. **Atenção:** campos reais no arquivo PA do DATASUS são `PA_MUNPCN` (não `PA_MUNRES`) e `PA_TPFIN` (não `PA_FINANC`) — confirmado por inspeção do PAMS2301.dbc.

### A fazer


- **7b — Ingestão temporária da produção PA** *(dep: 7a)* — Script `sia_producao.py`: baixa 24 arquivos `.dbc` do FTP DATASUS, filtra por município e financiamento, agrega por procedimento/ano e persiste em tabela temporária. Ver `docs/prompt_diagnostico_subregistro.md`.
- **7c — Consolidação e relatório de subregistro** *(dep: 7b)* — Aplica lógica de subregistro (queda > 50%, ratio = 0 sinalizado separadamente), usa valor unitário SIGTAP para gap estimado, gera CSV + sumário no stdout separando MAC e FAEC. Ver `docs/prompt_diagnostico_subregistro.md`.
- **7d — Frontend de solicitação de diagnóstico (site DataBrasil)** *(dep: 7c)* — Página pública no site da DataBrasil com formulário (município, UF, ano de referência, email). Dispara `POST /diagnostico/subregistro` no backend FaturaSUS (Railway) via API HTTP — o banco nunca é exposto diretamente. Job roda em background (estimativa: 3–10 min, limitado pela velocidade do FTP DATASUS). Quando concluído, envia o relatório CSV por email com link de download. Serve como gerador de leads para o FaturaSUS — qualquer secretário acessa sem cadastro ou contrato. Ver `docs/prompt_diagnostico_subregistro.md`.
- **8 — Desambiguação** *(dep: 5, 5b.1)* — **8a — ambiguidade semântica (top-3):** backend retorna top-3 candidatos quando score de confiança estiver abaixo de threshold (definir). Frontend exibe quick-reply buttons — padrão já existe no protótipo mockado. Ex: colonoscopia com/sem biópsia. **8b — detalhe faltante:** Haiku detecta quando o texto não tem informação suficiente para classificar (lateralidade, quantidade, complexidade de curativo) e devolve uma pergunta. Frontend exibe como mensagem do bot; profissional responde; backend reclassifica com contexto completo.
- **9 — Bundle de procedimentos complementares** *(dep: 4, 5b.1)* — Ao classificar o procedimento principal, o Haiku sugere proativamente os procedimentos que tipicamente acompanham aquele tipo de atendimento (ex: pré-natal → PA, peso, altura uterina). O profissional confirma o bundle em vez de lembrar item a item. Será necessário pesquisa profunda para entendimento de quais procedimentos são complementares. Aproveita a infraestrutura do classificador com prompt específico de bundling.
- **10 — Geração e validação do arquivo BPA** *(dep: 6, 8, 9)* — Layout magnético DATASUS, separação PAB/MAC
- **11 — Ambiente e-SUS local (Docker)** *(dep: 10)* — Subir instância local via https://github.com/filiperochalopes/esus-pec-docker. Quando o BPA standalone estiver válido, o custo marginal de gerar o mesmo BPA a partir do PostgreSQL do PEC local é baixo — e o protótipo passa a cobrir os dois mercados. Mapeamento do schema PostgreSQL do PEC é pré-requisito (ver Investigações pendentes).
- **11b — Extensão Chrome — assistente de preenchimento** *(dep: 11)* — Painel lateral que abre automaticamente na tela de procedimentos do PEC. Lê contexto do atendimento (CID, CBO, perfil do paciente) via API GraphQL interna do PEC (local) e entrega os diferenciais do FaturaSUS sem tirar o profissional do sistema.
- **12 — Dashboard + drill-down** *(dep: 10)* — KPIs, correção inline pelo faturista
- **13 — Exportação e histórico** *(dep: 10, 12)* — Consulta e reenvio de lotes
- **14 — Múltiplos procedimentos em um único áudio** *(dep: 3, 4)* — O backend segmenta um único áudio em múltiplos procedimentos, classifica cada um separadamente e retorna para confirmação individual. Comportamento testado em campo: profissionais naturalmente descrevem mais de um procedimento no mesmo registro de voz. Otimização UX — implementar após BPA estável.
- **15 — Cron SIGTAP diário** *(dep: 10)* — Só faz sentido automatizar após BPA validado

---

## v2 — pós-protótipo (infraestrutura)

- **v2.1 — Separar frontend em serviço dedicado** *(dep: passo 13)* — Mover React para Vercel/Cloudflare Pages; remover StaticFiles do FastAPI. Ver DEC-010.

---

## Fora do escopo atual (depende de acordo SMS)

- **16 — Auth JWT + RBAC multi-tenant** *(dep: 0–15)* — Entra com o primeiro usuário real ou junto com CADSUS real
- **16b — Onboarding de municípios clientes** *(dep: 16)* — Endpoint `POST /admin/tenants` + CLI `onboard_municipio` — persiste município no banco e dispara ingestão CNES (`cnes.py --municipios`) em background. Ver prompt deixado no fim da sessão 1b.
- **17 — CADSUS mock isolado** *(dep: acordo SMS próximo)* — Módulo com interface idêntica ao real, retornando dados fictícios. Só faz sentido criar quando houver usuário real ou acordo SMS próximo — para demo, o paciente hardcoded basta.
- **18 — CADSUS v5 real** *(dep: acordo SMS + 0–15)* — Substitui o mock cirurgicamente
- **19 — RBAC — escopo de acesso por perfil de CBO** *(dep: 16, 18)* — O escopo de procedimentos visualizáveis e registráveis varia por categoria profissional (auxiliar de enfermagem, técnico, enfermeiro, médico). Depende da integração com CADSUS real (passo 18), que fornece o CNS e o CBO do profissional logado. Requisito legal — implementar junto com o onboarding do primeiro município com CADSUS ativo.

---

## Etapa B (e-SUS) — extensão e exportação via PEC

Contexto: municípios com e-SUS ainda geram o arquivo BPA manualmente — o e-SUS não tem API de saída oficial. A arquitetura do PEC (React + GraphQL + PostgreSQL local) viabiliza dois mecanismos complementares sem depender de integração oficial com o Ministério da Saúde. O ambiente local (passo 10) é pré-requisito para ambos.

- **v3-3 — Job de exportação BPA via PostgreSQL** *(dep: 10, 10b)* — Serviço agendado no servidor municipal. Acessa o banco PostgreSQL do PEC diretamente, lê a produção consolidada e gera o arquivo BPA pronto para envio ao SIA. Elimina a etapa de digitação manual do faturista. Serve também como fallback para 10b caso atualizações do PEC alterem as queries GraphQL.

Questões em aberto antes de iniciar v3-3:
- Processo de autorização de acesso ao servidor municipal (referência: IntegraBPA/SES-ES)
- Fragilidade da extensão a atualizações do frontend React do PEC

---

## Investigações pendentes (resolver antes do passo indicado)

- **Antes do passo 8 — Latência do pipeline:** perfilar com logs de tempo por etapa (query expansion, embedding, pgvector, classificação). Latência atual: 2–7s (meta: <5s). Candidatos a otimização: paralelizar query expansion + embedding (hoje encadeados); prompt caching em `_SYSTEM_CLASSIFY`; avaliar se fallback substring ativa desnecessariamente. Só otimizar após ter dados reais.
- **Antes do passo 11 — Schema do PEC:** mapear schema do banco PostgreSQL do PEC contra instância Docker local (validar joins necessários para gerar BPA).
- **Antes do passo 16 — Modelo de deploy:** definir SaaS multi-tenant (coluna `tenant_id` em tabelas operacionais) vs. instância dedicada por prefeitura (schemas separados). Impacto direto no schema do banco. Ver DEC-008.
- **Antes do passo 17 — Hash do CNS:** definir SHA-256 vs. AES-256-GCM: SHA-256 é irreversível (não permite re-consultar o CADSUS depois); AES-256-GCM exige gestão de chave mas mantém o CNS recuperável. Ver DEC-009.
