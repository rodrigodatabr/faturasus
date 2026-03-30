# Decisões de Produto e Arquitetura — FaturaSUS

Registro das decisões não óbvias tomadas durante o desenvolvimento. Cada entrada explica **o que** foi decidido, **por quê**, e **o que não fazer** para não contradizer a decisão.

Antes de mudar qualquer coisa coberta aqui, leia a justificativa — ela pode mudar a abordagem.

---

## DEC-001 — Pacientes mockados em vez de dados reais do CADSUS

**O que:** o protótipo usa cinco pacientes fictícios fixos no lugar de consulta real ao CADSUS v5.

**Por quê:** o acesso real ao CADSUS exige autorização formal da unidade de saúde, que por sua vez exige contrato ou acordo de cooperação técnica com a SMS (Secretaria Municipal de Saúde). Esse acordo ainda não existe. A estratégia de go-to-market é mostrar o protótipo funcional com anti-glosa rodando para convencer a SMS a assinar o acordo — ou seja, o protótipo precisa existir *antes* da autorização.

**O que não fazer:** integrar o CADSUS real antes do acordo formal com a SMS. O módulo mock (passo 4 do roadmap) deve permanecer isolado para que a substituição seja cirúrgica quando o acordo vier.

**Referência:** `backend/app/seeds/seed_profissionais.py`, `roadmap.md` § "Decisão sobre o CADSUS".

---

## DEC-002 — Escopo inclui Atenção Básica/PAB além do MAC

**O que:** o sistema cobre toda a produção ambulatorial (BPA-C e BPA-I), incluindo MAC e Atenção Básica/PAB. A exportação separa automaticamente por financiamento.

**Por quê:** o ROI central está no MAC — produção ambulatorial não declarada impede o uso e a ampliação do teto MAC da unidade. Mesmo assim, não faz sentido entregar um sistema que cobre só metade da produção: a equipe de faturamento trabalharia em dois sistemas paralelos, e a proposta de valor seria menor. Cobrir o PAB tem custo marginal baixo (o pipeline é idêntico; a separação é na exportação) e aumenta a adoção.

**O que não fazer:** tratar PAB como cidadão de segunda classe no pipeline ou na UI. O profissional não precisa saber de qual financiamento é o procedimento — isso é responsabilidade do sistema na exportação.

**Referência:** `prd_faturasus.md` § 1, `CLAUDE.md` § Stack.

---

## DEC-003 — Ingestão SCNES: ZIP nacional para ST/PF/SR; .dbc por UF para HB

**O que:** os dados SCNES são ingeridos de duas fontes distintas por tipo de arquivo:
- **ST, PF, SR** — ZIP nacional (`BASE_DE_DADOS_CNES_{AAMM}.ZIP`): CSV com separador `;`, encoding Latin-1. Profissionais: JOIN obrigatório entre `tbCargaHorariaSus` (carga horária, CBO, vínculo) e `tbDadosProfissionalSus` (CNS real, nome) via `CO_PROFISSIONAL_SUS` (hash hex 16 chars). Serviços: `rlEstabServClass`.
- **HB** — `.dbc` por UF (`ftp://.../CNES/200508_/Dados/HB/HB{UF}{AAMM}.dbc`): o ZIP nacional **não contém** vínculos estabelecimento×habilitação. Leitura via `dbc-to-dbf` (Python puro) + `dbfread`, sem PySUS.

**Por quê:** o dry-run do ZIP 202602 (108 arquivos CSV) revelou que não existe nenhum arquivo de habilitações por estabelecimento. Apenas `tbSubGruposHabilitacao` (domínio de nomes, 560 linhas) está no ZIP. HB é obrigatório para anti-glosa de procedimentos MAC. PySUS foi descartado por ser projeto acadêmico comunitário com histórico de quebra por mudanças no FTP — risco inaceitável para atualização mensal em produção.

**O que não fazer:** tentar obter HB do ZIP nacional (não existe). Usar PySUS como dependência de produção. Persistir o hash `CO_PROFISSIONAL_SUS` no banco — o CNS real deve ser resolvido via join na ingestão e o hash descartado.

**Aprendizados da implementação (sessão 1b):**
- O ZIP CSV de `tbEstabelecimento` tem schema completamente diferente do `.dbc` por UF: colunas como `VINC_SUS`, `NIV_HIER`, `TP_PREST`, `ATENDAMB`, `NIVATE_A` **não existem no CSV** — ficam NULL no banco. Os dados completos do estabelecimento só estão no `.dbc` por UF.
- Filtrar por município (`--municipios`, código IBGE 6 dígitos = `CO_MUNICIPIO_GESTOR`) reduz PF de ~15M para ~5.400 registros e o tempo de ~45min para ~2min. Ingestão nacional não é viável em produção mensal.
- O join anti-glosa de habilitações é `cnes_habilitacoes.sgruphab = sigtap_rl_proc_habilitacao.co_habilitacao` — retorna 888 linhas com os dados do passo 1b. O campo `nu_grupo_habilitacao` chega vazio (`'    '`) em todos os registros do arquivo fonte do SIGTAP e não serve para join. **Resolvido no passo 1c.**

**Referência:** `docs/layout_scnes.md` § 1 (mapeamento completo), `backend/app/models/cnes.py`, `backend/app/ingest/cnes.py`, `backend/requirements.txt`.

---

## DEC-004 — Pipeline de classificação SIGTAP em duas etapas: pgvector → Claude Haiku

**O que:** a classificação de procedimentos usa duas etapas — pgvector retorna os top-15 candidatos por similaridade semântica; Claude Haiku recebe esses 15 + contexto (CBO, CNES) e classifica o procedimento final.

**Por quê:** enviar os 4.980+ procedimentos SIGTAP por requisição ao LLM seria proibitivamente caro e lento. O vetor filtra o espaço de busca para um conjunto gerenciável antes de acionar o LLM. O número 15 foi uma estimativa inicial — a hipótese é que o procedimento correto sempre estará nos top-15 candidatos semânticos, mas isso precisa ser validado empiricamente quando o pipeline for implementado.

**Investigação pendente (implementação do passo 5):** medir recall@15 com casos reais (percentual de vezes em que o procedimento correto está nos top-15). Se o recall for insatisfatório, aumentar para top-20 ou top-30 antes de ajustar o prompt do Haiku.

**O que não fazer:** mandar todos os procedimentos para o LLM por requisição. Fixar o threshold de 15 sem medir o recall.

**Referência:** `prd_faturasus.md` § 2 "Embeddings + LLM (duas etapas)", `roadmap.md` passo 2 e 5.

---

## DEC-005 — Railway como plataforma de deploy (não AWS/GCP/Azure)

**O que:** backend e banco de dados rodam na Railway, não em cloud enterprise.

**Por quê:** a Railway já é usada no produto principal da DataBrasil (familiaridade operacional, sem curva de onboarding). Oferece até 1 TB em bancos de dados sem a complexidade de billing e configuração das big clouds. Posiciona-se explicitamente como plataforma ideal para startups — deploys simples via git push, sem necessidade de configurar VPCs, IAM roles, ou load balancers para um MVP.

**O que não fazer:** migrar para cloud enterprise antes que a escala exija. A decisão pode ser reavaliada quando o número de clientes/tenants demandar SLAs que a Railway não suporte.

---

## DEC-006 — Fora de escopo: AIH (internação) e APAC

**O que:** o FaturaSUS cobre apenas BPA-C e BPA-I (produção ambulatorial). AIH (internações) e APAC ficam explicitamente fora do escopo.

**Por quê:** internações são um jogo diferente — envolvem prontuário eletrônico, cruzamentos de CID complexos, laudos, e um pipeline de validação completamente distinto do ambulatorial. O mercado de sistemas hospitalares para AIH é disputado por players estabelecidos e consolidados (MV, Philips Tasy, etc.), com ciclos de venda longos e implantações custosas. Não é o segmento que o FaturaSUS ataca. APAC foi excluída pelo mesmo princípio: envolve procedimentos de alta complexidade com laudo médico e autorização prévia, um fluxo distinto do BPA.

**O que não fazer:** aceitar demanda de cliente para cobrir internações sem uma decisão estratégica explícita — seria mudar o produto, não adicionar uma feature.

---

## DEC-007 — Áudio retido em memória do browser até confirmação; descartado após

**O que:** o áudio gravado pelo profissional nunca é enviado ao backend nem persistido em disco. Fica em memória no browser até o profissional confirmar o registro. Após confirmação, apenas a transcrição (texto) segue para o pipeline. Se o profissional fechar o app antes de confirmar, o áudio é perdido — o profissional grava novamente.

**Por quê:** LGPD. Áudio de voz é dado biométrico sensível. Manter o áudio no browser e descartá-lo após a transcrição elimina o risco de exposição em trânsito ou em repouso. A perda do áudio por fechamento do app é aceitável — o impacto é apenas gravar novamente, não perder o registro.

**O que não fazer:** enviar o blob de áudio ao backend. Persistir áudio em banco ou storage. Criar mecanismo de "recuperação de áudio perdido".

**Referência:** `prd_faturasus.md` § 2 Pipeline de Registro, § 4 LGPD.

---

## DEC-010 — Deploy: monorepo + serviço único no protótipo; separar frontend/backend na v2

**O que:** no protótipo, frontend (React/Vite) e backend (FastAPI) vivem no mesmo repo e são servidos pelo mesmo serviço Railway. O FastAPI serve `frontend/dist/` via StaticFiles. O build é feito por um Dockerfile multistage na raiz: stage Node 22 builda o frontend, stage Python 3.12 instala as dependências e copia o dist.

**Por quê:** reduz overhead operacional na fase de protótipo (um serviço, um domínio, um deploy). O Railway não suporta builds multi-linguagem nativamente via Railpack sem configuração manual que se mostrou não-confiável (railpack.json ignorado quando Root Directory aponta para `backend/`). O Dockerfile é determinístico e imune a mudanças de versão do Railpack.

**Quando separar:** quando o produto tiver usuários reais ou deploys frequentes do frontend independentes do backend. Mover o frontend para Vercel ou Cloudflare Pages (CDN global, grátis) e remover o bloco StaticFiles do `main.py`. A arquitetura atual já suporta isso cirurgicamente.

**O que não fazer:** tentar configurar build multi-linguagem via railpack.json/railway.json na raiz — foi tentado e não funciona com Root Directory diferente da raiz do repo.

**Referência:** `Dockerfile`, `backend/app/main.py` (bloco StaticFiles), `roadmap.md` passo 2.

---

## DEC-008 — Modelo multi-tenant hierárquico: profissional → unidade → prefeitura

**O que:** cada profissional de saúde terá uma conta vinculada ao seu CNS. A unidade de saúde (CNES) terá acesso ao dashboard de produção total da unidade, com capacidade de edição. A prefeitura/SMS visualizará a produção consolidada de todas as unidades antes de fechar e enviar o arquivo BPA ao Ministério da Saúde.

**Por quê:** esse é o fluxo real de faturamento SUS: o profissional registra, a unidade confere e corrige, a secretaria consolida e envia. O sistema deve refletir essa hierarquia de responsabilidade.

**Em aberto:** o modelo de deploy (uma instância SaaS compartilhada com isolamento por tenant vs. deploy dedicado por prefeitura) ainda não foi definido. Isso tem implicações no schema do banco (coluna `tenant_id` em todas as tabelas operacionais vs. schemas separados por tenant) e no modelo comercial. **Investigar antes de implementar o passo 11 (Auth JWT + RBAC).**

**Referência:** `roadmap.md` passo 11, `prd_faturasus.md` § 3 Usuários.

---

## DEC-009 — CNS: hash SHA-256 vs. criptografia AES-256-GCM (em aberto)

**O que:** a decisão atual é armazenar o CNS como hash SHA-256 (irreversível) por exigência da LGPD. Em algum momento surgiu uma referência a AES-256-GCM (reversível) — possivelmente ao analisar o layout SIGTAP.

**Por quê do SHA-256:** LGPD — o CNS é dado pessoal e seu armazenamento como hash elimina a possibilidade de identificação direta a partir do banco.

**O problema:** SHA-256 é irreversível, o que inviabiliza consultas futuras ao CADSUS após o armazenamento (para atualizar dados do paciente, por exemplo). AES-256-GCM permitiria reverter o CNS quando necessário para consultar o CADSUS, mas exige gestão de chave de criptografia.

**Investigação pendente:** definir se o sistema precisará reverter o CNS após o armazenamento. Se sim, AES-256-GCM com chave gerenciada pela Railway é a abordagem correta. Se não (o CNS é usado apenas como identificador de deduplicação), SHA-256 é suficiente. **Resolver antes de implementar o passo 12 (CADSUS real).**

**Referência:** `docs/revisao_estrategia.md`, `prd_faturasus.md` § 4 LGPD.
