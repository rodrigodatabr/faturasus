# PRD — FaturaSUS
**Assistente Inteligente de Faturamento Ambulatorial SUS**

> Decisões de produto e arquitetura não deriváveis deste documento: ver [`DECISIONS.md`](DECISIONS.md).

| Campo | Valor |
|---|---|
| Produto | FaturaSUS |
| Empresa | DataBrasil Inteligência de Dados LTDA (CNPJ 53.929.951/0001-06) |
| Versão | 1.1 — Março/2026 |
| Responsável | Rodrigo Alves — Gerente Executivo |

---

## 1. O Produto

O FaturaSUS é um assistente PWA de captura e faturamento de produção ambulatorial MAC (Média e Alta Complexidade). O profissional registra um procedimento em ~15 segundos via aplicativo: escaneia o cartão SUS do paciente e grava um áudio descrevendo o procedimento. O sistema identifica o paciente via CADSUS, classifica o código SIGTAP por busca semântica + LLM, valida contra o perfil da unidade e do profissional, e armazena o registro. No fechamento mensal, o faturista revisa, corrige e exporta o arquivo BPA no layout oficial para o SIA/SUS.

**Escopo:** toda a produção ambulatorial (BPA-C e BPA-I), abrangendo tanto MAC quanto Atenção Básica/PAB. O sistema separa automaticamente por financiamento na exportação. Fora de escopo: internações (AIH) e APAC.

### Usuários

| Perfil | Papel | Canal |
|---|---|---|
| Profissional de saúde (médico, enfermeiro, técnico) | Registra procedimentos no ponto de cuidado | Aplicativo PWA |
| Responsável pelo faturamento | Revisa, corrige e exporta o BPA mensal | Dashboard Web |
| Gestor / Secretário de Saúde | Acompanha produção e resultados | Dashboard Web |
| Administrador da unidade | Cadastra profissionais e configura permissões | Dashboard Web |

---

## 2. Arquitetura Técnica

### Stack

| Camada | Tecnologia |
|---|---|
| Backend | Python FastAPI — Railway |
| Banco de dados | PostgreSQL — Railway |
| Busca semântica | pgvector (extensão Postgres) + embeddings OpenAI `text-embedding-3-small` |
| Transcrição de áudio | OpenAI Whisper API |
| Classificação SIGTAP | Claude Haiku via Anthropic API |
| Identificação de paciente | API CADSUS v5 (SOAP via barramento RNDS) |
| Frontend | PWA React |
| Canal de entrada | Aplicativo PWA (principal) — WhatsApp como fallback v2 |

### Pipeline de Registro

```
[Scan código de barras CNS]
  → [CADSUS v5: retorna nome, sexo, data nasc., município]
  → [Profissional grava áudio do procedimento]
  → [Whisper: transcrição PT-BR → áudio retido em memória do browser até confirmação]
  → [pgvector: top-15 candidatos SIGTAP por similaridade semântica]
  → [Claude Haiku: classificação final + preenchimento dos campos BPA]
  → [Validação anti-glosa: CBO × CNES × instrumento × FPO × duplicidade]
  → [Armazenamento + hash SHA-256 do CNS]
  → [Fila para revisão do faturista]
```

**Embeddings + LLM (duas etapas):**
pgvector retorna os 15 candidatos mais próximos semanticamente. Claude recebe esses 15 + contexto (CBO, CNES) e classifica. ~10× mais barato e mais preciso que enviar os 4.600+ procedimentos por requisição.

### Atualização do SIGTAP — Cron Job Diário

Cron job diário às 3h (Brasília):

1. Baixa pacote BDSIA de `datasus.gov.br/sigtap`
2. Compara hash MD5 com o da última ingestão
3. Se diferente: parseia `.txt` em layout fixo, faz UPSERT em `sigtap_procedimentos`
4. Gera log de alterações (adicionados / alterados / removidos)
5. Recalcula embeddings **apenas** dos procedimentos alterados

---

## 3. Módulos

### 3.1 Captura — Aplicativo PWA

**Fluxo principal:**

1. **Scan:** profissional aponta câmera para o código de barras do Cartão SUS. App lê o CNS e consulta CADSUS v5. Exibe: *"Maria da Silva, F, 45 anos, Gravataí-RS"*. Profissional confirma.
2. **Áudio:** profissional pressiona botão e descreve o procedimento em linguagem natural. Whisper transcreve. Áudio permanece em memória volátil do browser (nunca enviado ao servidor ou persistido em disco) para permitir regravação caso a transcrição esteja incorreta.
3. **Confirmação:** app exibe código SIGTAP identificado + descrição. Se houver ambiguidade, apresenta opções com botões de resposta rápida. Profissional confirma ou corrige. **Áudio é descartado (buffer liberado) ao confirmar** — apenas o texto estruturado é armazenado.
4. **Alternativas:** captura por texto (digitação livre) e leitura de código de barras SIGTAP via câmera.

> O profissional NÃO precisa saber o código SIGTAP. Descreve em linguagem natural — ex: *"fiz curativo complexo em dois pacientes"* — e o sistema resolve.

**Preenchimento automático dos campos BPA-I:**

| Campo | Fonte |
|---|---|
| CNS do paciente | Código de barras do Cartão SUS |
| Nome, sexo, data nasc., município | API CADSUS v5 (automático) |
| CNES do estabelecimento | Perfil do profissional cadastrado |
| CNS e CBO do profissional | Perfil do profissional cadastrado |
| Competência | Data do sistema |
| Código SIGTAP | Classificação por LLM |
| CID principal | Extraído do áudio ou perguntado pelo bot |
| Autorização (condicional) | Perguntado pelo bot quando obrigatório |

---

### 3.2 Ingestão em Lote — Laboratório e Imagem

Laboratórios e serviços de imagem representam ~50–60% do volume total de BPA (majoritariamente BPA-C). Esses procedimentos já têm o código SIGTAP mapeado na origem, via LIS ou GAL, e não passam pelo fluxo de áudio. O módulo de ingestão em lote permitirá upload de CSV/XLS com aplicação de tabela de-para configurada por unidade (nome do exame local → SIGTAP), seguida das mesmas validações anti-glosa. Planejado para v2 — no piloto, labs continuam com o workflow existente (GAL ou BPA Magnético).

---

### 3.3 Validação Anti-Glosa

#### Tabelas necessárias no banco

| Tabela | Origem | Conteúdo |
|---|---|---|
| `sigtap_procedimentos` | DATASUS — pacote BDSIA (cron diário com hash diff) | Procedimentos, valores, atributos (sexo, idade, qtd máxima) |
| `sigtap_rl_proc_ocupacao` | DATASUS — pacote BDSIA (incluso no cron) | Compatibilidade CBO × procedimento |
| `sigtap_rl_proc_registro` | DATASUS — pacote BDSIA (incluso no cron) | Instrumento permitido por procedimento (BPA-C/BPA-I — tabela separada, N:N) |
| `sigtap_rl_proc_habilitacao` | DATASUS — pacote BDSIA (incluso no cron) | Habilitação exigida por procedimento (`NU_GRUPO_HABILITACAO`) |
| `sigtap_rl_proc_servico` | DATASUS — pacote BDSIA (incluso no cron) | Serviço/classificação exigido por procedimento |
| `cnes_habilitacoes` | SCNES — HB*.dbf (importação mensal) | Habilitações por CNES (`SGRUPHAB` = `CO_HABILITACAO` de `sigtap_rl_proc_habilitacao`) |
| `cnes_servicos` | SCNES — SR*.dbf (importação mensal, mesmo upload) | Serviços/classificações do estabelecimento — cruzamento com `sigtap_rl_proc_servico` |
| `profissionais` | SCNES — PF*.dbf (importação mensal, mesmo upload) | Profissionais vinculados ao CNES. Admin vincula login ao CNS |
| `fpo_programacao` | Inserção manual pelo faturista | Teto físico-orçamentário por procedimento/CNES/competência |
| `pacientes_sessao` | Volátil (memória da sessão) | Dados CADSUS do turno atual — descartados ao encerrar sessão |
| `registros_producao` | Gerado pelo sistema | Procedimentos registrados na competência |

> **CADSUS:** o acesso exige credenciamento do estabelecimento no Portal de Serviços do DATASUS (`servicos-datasus.saude.gov.br`). Protocolo SOAP via barramento RNDS. Em caso de indisponibilidade: fallback manual — profissional digita CPF ou CNS e dados são validados na próxima consulta CADSUS disponível.

#### Cruzamentos de validação (executados antes de persistir)

| Verificação | Por quê | Tabelas | Ação |
|---|---|---|---|
| Procedimento × CBO do profissional | Cada procedimento SIGTAP lista quais CBOs podem realizá-lo — ex: enfermeiro não fatura procedimento exclusivo de médico. SIA rejeita | `sigtap_cbo_procedimento` + `profissionais` | **Bloqueio** |
| Procedimento × Habilitação do CNES | Cada procedimento SIGTAP exige habilitações específicas do estabelecimento — ex: unidade sem habilitação em oncologia não pode faturar quimioterapia. SIA rejeita | `cnes_habilitacoes` + `sigtap_rl_proc_habilitacao` (join via `CO_HABILITACAO = sgruphab` — `NU_GRUPO_HABILITACAO` chega vazio no arquivo fonte) | **Bloqueio** |
| Procedimento × Serviço do CNES | Cada procedimento SIGTAP pode exigir serviço/classificação cadastrado no CNES — ex: estabelecimento sem serviço de fisioterapia não pode faturar procedimento que o exige. SIA rejeita | `cnes_servicos` + `sigtap_rl_proc_servico` | **Bloqueio** |
| Instrumento correto (BPA-C vs BPA-I vs APAC) | Cada procedimento SIGTAP define em qual instrumento deve ser registrado — ex: procedimento individualizado lançado em BPA-C (consolidado) é rejeitado pelo SIA. Relação N:N em tabela própria — um procedimento pode admitir mais de um instrumento | `sigtap_rl_proc_registro` | **Bloqueio** |
| Mesmo procedimento em BPA-C e BPA-I na mesma competência | Alguns procedimentos SIGTAP têm instrumento 03 (ambos permitidos). O SIA aceita nos dois, mas não cruza BPA-C com BPA-I (consolidado não tem CNS) — risco real de dupla cobrança e flag de auditoria. Sistema deve exigir um único instrumento por procedimento/CNES | `registros_producao` + `sigtap_procedimentos` | **Bloqueio** |
| Data do atendimento dentro da competência (máx. 3 competências retroativas) | O SIA aceita produção retroativa de até 3 competências — ex: atendimento de janeiro pode ser faturado até a competência de abril. Fora disso, rejeitado | Regra fixa | **Bloqueio** |
| Quantidade × Teto FPO do mês | Cada CNES tem um teto mensal aprovado por procedimento (FPO) — produção acima do teto não é paga, mas produção excedente registrada serve para justificar aumento do teto | `fpo_programacao` + `registros_producao` | **Alerta** — marca para revisão |
| Duplicidade (proc + profissional + paciente + data) | Mesma combinação indica possível duplicação — mas há casos legítimos (ex: dois curativos no mesmo paciente no mesmo dia) | `registros_producao` | **Alerta** |
| Formato do CNS (dígito verificador) | CNS com dígito verificador inválido é rejeitado na importação do BPA pelo SIA. Registro permitido (não trava o profissional), exportação bloqueada | Algoritmo local | **Alerta** — bloqueia exportação |

---

### 3.4 Fontes de Dados Externas

Três fontes alimentam o sistema. Cada uma exige um dicionário de dados para definir o schema:

| Fonte | Arquivos | Frequência | Ação do admin | Dicionário de referência |
|---|---|---|---|---|
| **SIGTAP** (BDSIA) | `.txt` layout fixo | Cron diário com hash diff | Nenhuma (automático) | Layout BDSIA — disponível em `sigtap.datasus.gov.br` |
| **SCNES** | ZIP nacional CSV `;` (ST, PF via `tbCargaHorariaSus`+join, SR via `rlEstabServClass`) + `HB{UF}.dbc` por UF (habilitações — **ausente do ZIP**) | Upload mensal único | Importar pacote + vincular login ao CNS | `docs/layout_scnes.md` |
| **FPO** | — | Inserção manual | Faturista cadastra tetos por procedimento/CNES | Definir schema interno com base no fluxo do faturista |

**Filtros na importação SCNES:** apenas profissionais com `upper(TP_SUS_NAO_SUS) = 'S'` (campo real em `tbCargaHorariaSus`); serviços com `CO_AMBULATORIAL_SUS = '1'`.

RBAC: Profissional registra / Faturista revisa e exporta / Gestor visualiza / Admin configura

---

### 3.5 Dashboard Gerencial

**KPIs:** procedimentos registrados no mês, valor estimado de faturamento, alertas de glosa pendentes, % do teto MAC utilizado.

**Visualizações:**
- Gráfico de barras: produção por unidade / profissional / grupo de procedimento — com **drill-down por clique**
- Linha do tempo diária (dias sem registro = alerta)
- Tabela com filtros: data, profissional, procedimento, status (confirmado / pendente / corrigido / bloqueado)

**Ações:**
- Correção inline de qualquer registro antes da exportação
- Log de auditoria: todas as alterações rastreadas (quem, quando, o quê)

---

### 3.6 Geração do BPA

- Seleção de competência e CNES
- Exportação bloqueada se houver erros críticos pendentes
- Geração do arquivo `.PA` no layout magnético oficial DATASUS
- Separação automática por financiamento: PAB e MAC/FAEC em arquivos distintos
- Relatório de conferência PDF antes do envio
- Histórico de exportações: data, competência, usuário, hash do arquivo

---

### 3.7 Proteção de Dados (LGPD)

- **Áudio:** mantido apenas em memória volátil do browser até confirmação do profissional; descartado (buffer liberado) ao confirmar. Nunca enviado ao servidor nem persistido em disco.
- **CNS do paciente:** armazenado em dois campos distintos:
  - `cns_enc` — AES-256-GCM com chave derivada por tenant (`HKDF(railway_secret, tenant_id)`). Reversível — usado para gerar o arquivo BPA na exportação.
  - `cns_hash` — SHA-256 do CNS. Irreversível — usado exclusivamente para deduplicação e auditoria sem expor o dado original.
  O CNS em texto plano nunca é persistido em banco.
- **Nome do paciente:** nunca armazenado em banco — presente apenas no cache volátil de sessão
- **CNS original para o BPA:** descriptografado em memória na exportação a partir de `cns_enc` com a chave do tenant; descartado após geração do arquivo
- Autenticação JWT, RBAC, logs de auditoria em todas as operações sobre dados sensíveis
- Multi-tenant: dados de cada município completamente isolados
- Criptografia em trânsito (TLS 1.3) e em repouso (pgcrypto)
- Servidor no Brasil (Railway, região São Paulo)
- Base legal: execução de políticas públicas — art. 7º, III e art. 11, II, "b" da LGPD
- Retenção: 5 anos; após rescisão, eliminação em até 30 dias

---

## 4. APIs do DATASUS

Acesso via barramento RNDS. Requer credenciamento do estabelecimento em `servicos-datasus.saude.gov.br`.

| API | Função | Protocolo |
|---|---|---|
| CADSUS v5 | Dado o CNS, retorna nome, sexo, data nasc., município, nome da mãe | SOAP (RNDS) |
| SIGTAP | Valida código, compatibilidade CBO, instrumento, valores | SOAP (RNDS) |
| CNES | Valida habilitações do estabelecimento e vínculos de profissionais | SOAP (RNDS) |

---

## 5. Escopo — MVP vs. v2

| Funcionalidade | Versão |
|---|---|
| Scan do Cartão SUS + integração CADSUS v5 | ✅ MVP |
| Captura por voz (Whisper) + descarte do áudio após confirmação | ✅ MVP |
| Captura por texto e leitura de código de barras SIGTAP | ✅ MVP |
| Ingestão em lote via CSV (laboratório e imagem) com wizard de mapeamento e de-para SIGTAP | v2 |
| Cache de sessão CADSUS (volátil, descartado ao encerrar turno) | ✅ MVP |
| Busca semântica SIGTAP (pgvector) | ✅ MVP |
| Classificação por Claude Haiku | ✅ MVP |
| Validação anti-glosa completa (6 cruzamentos) | ✅ MVP |
| Cron job diário SIGTAP com diff de hash | ✅ MVP |
| Importação SCNES (ZIP CSV + HB.dbc por UF): profissionais, habilitações, serviços + vinculação de login + RBAC | ✅ MVP |
| Dashboard gerencial com drill-down | ✅ MVP |
| Correção inline pelo faturista | ✅ MVP |
| Geração do arquivo BPA (layout DATASUS) com separação automática PAB/MAC | ✅ MVP |
| Relatório PDF pré-exportação | ✅ MVP |
| Anonimização SHA-256 + criptografia em repouso | ✅ MVP |
| Canal WhatsApp como fallback | v2 |

| Validação de CID × procedimento | v2 |
| Relatório técnico automatizado para aumento do teto MAC | v2 |
| Integração CMD via RNDS (quando fase 3 obrigatória) | v2 |
| Módulo APAC (alta complexidade) | v2 |
| OCR de fichas de atendimento por foto | v2 |
| BI com benchmarking intermunicipal | v2 |

---

## 6. Requisitos Não-Funcionais

| Requisito | Especificação |
|---|---|
| Latência ponta a ponta | < 5s do envio do áudio até a confirmação |
| Disponibilidade | 99,5% de uptime mensal |
| Precisão SIGTAP | > 90% de classificação correta sem intervenção humana (meta piloto) |
| Auditabilidade | 100% das operações sobre dados sensíveis rastreadas |
| Multi-tenancy | Dados de cada município completamente isolados |
| Exportação BPA | 100% de conformidade com layout DATASUS — aceito sem rejeição no SIA |
| Conformidade | LGPD, Resolução CFM 2.217/2018, Portaria MS 2.073/2011 |

---

## 7. Tratamento de Erros e Casos de Borda

| Situação | Tratamento |
|---|---|
| API CADSUS indisponível | Fallback manual: profissional digita CPF ou CNS; dados validados na próxima consulta CADSUS disponível |
| Áudio com ruído excessivo | Exibir transcrição com baixa confiança; solicitar confirmação textual ou nova gravação |
| Procedimento ambíguo (ex: colonoscopia com/sem biópsia) | Fluxo de desambiguação com botões de resposta rápida antes de persistir |
| Classificação SIGTAP com baixa confiança | Apresentar top-3 opções para o profissional escolher |
| CNES sem habilitação cadastrada | Bloquear registro + orientar admin a importar CSV do SCNES |
| Teto MAC estourado | Alertar faturista; não bloquear registro (pode ser produção para justificar aumento do teto) |

---

## 8. Custos Estimados por Município

Baseado em produção real de município de ~40 mil habitantes (2025): ~520 mil procedimentos/ano, dos quais ~95% são ambulatoriais (BPA) — ~41 mil procedimentos BPA/mês. Desses, ~15 mil encontros clínicos passam pelo fluxo de áudio e ~27 mil chamadas de classificação SIGTAP são realizadas no total.

| Item | Volume mensal | Custo mensal |
|---|---|---|
| Whisper STT | ~15.000 áudios × 15s ≈ 3.750 min | R$ 120–150 |
| Claude Haiku (classificação SIGTAP) | ~27.000 classificações | R$ 450–700 |
| APIs DATASUS (CADSUS, SIGTAP, CNES) | — | Gratuito |
| Railway (Postgres + backend + PWA) | — | R$ 100–180 |
| **Total de custo** | | **R$ 670–1.030** |

> ~R$ 0,025/procedimento BPA ou ~R$ 0,07/encontro com áudio.

---

## 9. Questões em Aberto

| Questão | Próximo passo |
|---|---|
| Credenciamento CADSUS: o piloto consegue acesso ao barramento RNDS? | Validar com secretaria de saúde do município-piloto antes de iniciar dev |
| Dicionários de dados: BDSIA (SIGTAP) e SCNES (PF/HB) mapeados para schema do banco? | Mapear campos dos layouts oficiais antes de implementar as tabelas |
| Whisper API vs faster-whisper local? | Testar latência e custo nos dois |
| O Ministério aceita BPA de sistema de terceiros? | Sim — formato aberto. Validar com SMS antes do primeiro envio real |

---

*FaturaSUS — DataBrasil Inteligência de Dados LTDA | v1.1 | Março/2026 | Confidencial*
