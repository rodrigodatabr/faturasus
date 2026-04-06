# Fontes Normativas — Validação Anti-Glosa BPA/SIA

Documento de referência para o passo 6 do roadmap. Mapeia cada cruzamento de validação ao arcabouço normativo que o fundamenta.

> **Nota metodológica:** nenhuma portaria única enuncia "as regras de glosa do BPA" em um documento só. O arcabouço é estratificado: a norma-raiz define os atributos de cada procedimento (CBO, habilitação, serviço, instrumento); normas complementares disciplinam o instrumento de registro e a retroatividade; o Manual Técnico Operacional SIA documenta a lógica de processamento.

---

## Regra 1 — CBO × Procedimento

**O quê:** cada procedimento SIGTAP possui lista de CBOs autorizados a realizá-lo. O SIA rejeita o BPA-I quando o CBO informado não consta nessa lista — salvo procedimentos com atributo "021 – Não Exige CBO".

**Ação no sistema:** **bloqueio** antes de persistir o registro.

**Tabelas envolvidas:**
- `sigtap_rl_proc_ocupacao` (co_procedimento × co_ocupacao × dt_competencia)
- `profissionais.cbo`

**Fontes:**

| Documento | Ano | Trecho relevante |
|---|---|---|
| **Portaria GM/MS nº 321, de 08/02/2007** | 2007 | Institui o SIGTAP. Anexo define CBO como atributo obrigatório: "especialidades habilitadas a realizar o procedimento." |
| **Portaria de Consolidação GM/MS nº 1, de 28/09/2017** | 2017 | Revoga a GM 321 e incorpora SIGTAP. Arts. 324–335 e **Anexo XVII**: atributo CBO permanece como requisito de validação. URL: https://bvsms.saude.gov.br/bvs/saudelegis/gm/2017/prc0001_03_10_2017.html |
| **Portaria de Consolidação SAES/MS nº 1, de 22/02/2022** | 2022 | Art. 412 e **Anexo LVIII**: atributos gerais e complementares dos procedimentos (revoga SAS/MS 436/2010). Mantém CBO como atributo geral. |
| **Manual Técnico Operacional SIA/SUS** (DATASUS/MS) | Ed. 2010 | "O processamento do SIA rejeitará os atendimentos realizados por profissionais que não têm o CBO informado cadastrado no CNES." URL: http://www1.saude.rs.gov.br/dados/1273242960988Manual_Operacional_SIA2010.pdf |

**Onde vive o dado:** `rl_proc_ocupacao` no pacote BDSIA — a norma-mãe (Portaria GM 321/2007, consolidada em 2017) determina que o atributo existe; o conteúdo vive no SIGTAP atualizado mensalmente.

---

## Regra 2 — Habilitação do CNES × Procedimento

**O quê:** procedimentos que exigem habilitação específica (ex.: oncologia, hemodiálise, UTI neonatal) só podem ser faturados se o CNES possuir a habilitação correspondente vigente na competência.

**Ação no sistema:** **bloqueio** antes de persistir o registro.

**Tabelas envolvidas:**
- `sigtap_rl_proc_habilitacao` (co_procedimento × co_habilitacao × dt_competencia)
- `cnes_habilitacoes` (cnes × sgruphab × cmpt_ini × cmpt_fim)
- **Join:** `cnes_habilitacoes.sgruphab = sigtap_rl_proc_habilitacao.co_habilitacao`
- **Atenção:** `nu_grupo_habilitacao` chega vazio no arquivo fonte SIGTAP — não usar (ver DEC-003 / passo 1c).

**Fontes:**

| Documento | Ano | Trecho relevante |
|---|---|---|
| **Portaria GM/MS nº 321/2007** (Anexo) | 2007 | Define Habilitação como atributo obrigatório para procedimentos que exigem credenciamento: "o estabelecimento de saúde deve dispor desta habilitação cadastrada no CNES." |
| **Portaria de Consolidação GM/MS nº 1/2017** (Anexo XVII) | 2017 | Mantém habilitação como atributo. Art. 324 confere força normativa à tabela como requisito de validação SUS. |
| **Portaria de Consolidação SAES/MS nº 1/2022** (Art. 412, Anexo LVIII) | 2022 | Consolida SAS 436/2010. O atributo complementar "Verifica Habilitação" instrui o SIA a cruzar com o cadastro CNES antes de aprovar o pagamento. |
| **Portaria SAS/MS nº 1.229, de 20/12/2012** | 2012 | Condicionou explicitamente o financiamento FAEC à comprovação de habilitação: estabelecimentos sem a habilitação pertinente não recebem crédito. |

---

## Regra 3 — Serviço/Classificação do CNES × Procedimento

**O quê:** distinto da habilitação, o atributo Serviço/Classificação exige que o CNES possua determinado serviço especializado registrado (ex.: Serviço de Nefrologia, Saúde Mental) para faturar o procedimento.

**Ação no sistema:** **bloqueio** antes de persistir o registro.

**Tabelas envolvidas:**
- `sigtap_rl_proc_servico` (co_procedimento × co_servico × co_classificacao × dt_competencia)
- `cnes_servicos` (cnes × serv_esp × class_sr × competen), filtro `ambul = 'S'`
- **Join:** `cnes_servicos.serv_esp = sigtap_rl_proc_servico.co_servico AND cnes_servicos.class_sr = sigtap_rl_proc_servico.co_classificacao`

**Fontes:**

| Documento | Ano | Trecho relevante |
|---|---|---|
| **Portaria GM/MS nº 321/2007** (Anexo) | 2007 | Define Serviço/Classificação como atributo do procedimento: "o estabelecimento de saúde deve dispor deste serviço/classificação cadastrado no CNES." |
| **Portaria de Consolidação GM/MS nº 1/2017** (Anexo XVII) | 2017 | Incorpora o atributo. |
| **Portaria de Consolidação SAES/MS nº 1/2022** (Art. 412, Anexo LVIII) | 2022 | Atributo Serviço/Classificação como atributo geral vinculado à validação CNES. |
| **Portaria SAS/MS nº 911, de 29/08/2012** | 2012 | Exemplo concreto: exige registro de Serviço de Saúde Bucal no CNES para procedimentos odontológicos especializados em BPA-I. |

---

## Regra 4 — Instrumento correto (BPA-C vs. BPA-I)

**O quê:** cada procedimento tem instrumento de registro definido no SIGTAP. Submeter um procedimento BPA-I no instrumento BPA-C (ou vice-versa) resulta em rejeição. Quando um procedimento admite ambos os instrumentos (co_registro = ambos na `rl_proc_registro`), o CNES **deve usar o mesmo instrumento para todos os registros daquele procedimento na mesma competência** — mistura é vetada pelo SIA.

**Ação no sistema:** **bloqueio** antes de persistir o registro.

**Tabelas envolvidas:**
- `sigtap_rl_proc_registro` (co_procedimento × co_registro × dt_competencia)
  - co_registro `01` = BPA-I (individualizado, exige CNS do paciente)
  - co_registro `02` = BPA-C (consolidado)
- `registros_producao` — para detectar mistura de instrumentos no mesmo CNES/procedimento/competência

**Fontes:**

| Documento | Ano | Trecho relevante |
|---|---|---|
| **Portaria SAS/MS nº 709, de 27/12/2007** | 2007 | **Institui o BPA-I.** Art. 1: divide o BPA magnético em BPA-C e BPA-I. Art. 2 + Anexo I: lista procedimentos com registro individualizado obrigatório. URL: https://bvsms.saude.gov.br/bvs/saudelegis/sas/2007/prt0709_27_12_2007.html |
| **Portaria SAS/MS nº 380, de 12/08/2010** | 2010 | Migra procedimentos adicionais de BPA-C para BPA-I obrigatório (Arts. 1, Anexos I–IV). URL: https://bvsms.saude.gov.br/bvs/saudelegis/sas/2010/prt0380_12_08_2010.html |
| **Portaria SAS/MS nº 1.362, de 04/12/2013** | 2013 | **Art. 2 — regra crítica de unicidade:** "o Estabelecimento que optar pelo registro de determinado procedimento em BPA-C ou BPA-I em determinada competência deverá registrar todos os procedimentos desse tipo pelo mesmo instrumento naquela competência." O SIA valida e rejeita mistura. URL: https://bvsms.saude.gov.br/bvs/saudelegis/sas/2013/prt1362_04_12_2013.html |
| **Portaria de Consolidação GM/MS nº 1/2017** (Anexo XVII) | 2017 | Instrumento de registro é atributo de cada procedimento no SIGTAP. |

---

## Regra 5 — Duplicidade (procedimento + profissional + paciente + data)

**O quê:** mesma combinação CNS paciente + co_procedimento + cbo + dt_atendimento + cnes na mesma competência indica possível duplicação. Casos legítimos existem (ex.: dois curativos no mesmo paciente no mesmo dia) — por isso a ação é alerta, não bloqueio.

**Ação no sistema:** **alerta** — marca para revisão pelo faturista.

**Tabelas envolvidas:**
- `registros_producao` — verificação antes de inserir novo registro

**Fontes:**

| Documento | Ano | Trecho relevante |
|---|---|---|
| **Manual Técnico Operacional SIA/SUS** (DATASUS/MS) | Ed. 2010 | "Não pode existir duplicidade de folhas com mesmo número para um mesmo CNES em uma mesma competência." Para BPA-I, o sistema usa CNS paciente + procedimento + data + profissional como chave de unicidade. |
| **Portaria SAES/MS nº 1.110, de 11/11/2021** | 2021 | Art. 1, IV define "reapresentação" como reenvio de produção anteriormente **rejeitada** — pressupõe que o SIA detecta e rejeita duplicatas na apresentação original. URL: https://bvsms.saude.gov.br/bvs/saudelegis/saes/2021/prt1110_18_11_2021.html |
| **Portaria SAS/MS nº 1.362/2013** | 2013 | Art. 2: veda o uso de instrumentos diferentes para o mesmo procedimento na mesma competência — inclui proibição de registrar o mesmo atendimento em BPA-C e BPA-I simultaneamente. |

**Nota:** não há portaria específica que "institui a regra de duplicidade" por nome. Ela é consequência da lógica de processamento do SIA definida no Manual Operacional e operacionalizada pelo sistema DATASUS.

---

## Regra 6 — FPO (Teto Físico-Orçamentário)

**O quê:** a FPO é a programação físico-orçamentária que o gestor define por estabelecimento/procedimento/competência. Produção acima do teto para MAC não é paga, mas deve ser registrada para justificar aumento futuro do teto. Para PAB, não há glosa por FPO — a produção básica é registrada integralmente.

**Ação no sistema:** **alerta** — não bloqueia (produção acima do teto é evidência para renegociação). Marca o registro para revisão do faturista.

**Tabelas envolvidas:**
- `fpo_programacao` (cnes × co_procedimento × competencia × qt_aprovada) — inserção manual pelo faturista
- `registros_producao` — soma de quantidade na competência para comparação

**Fontes:**

| Documento | Ano | Trecho relevante |
|---|---|---|
| **Portaria SAS/MS nº 496, de 30/06/2006** | 2006 | **Norma-mãe da FPO.** Art. 1: permite programação por grupo, subgrupo, nível de organização e/ou procedimento a partir da competência setembro/2006. **Art. 7**: procedimentos com financiamento PAB **não sofrem glosa por insuficiência de FPO** — produção básica registrada integralmente. URL: https://bvsms.saude.gov.br/bvs/saudelegis/sas/2006/prt0496_30_06_2006.html |
| **Manual Operacional da FPO** (DATASUS/SIA wiki) | Vigente | O processamento mensal confronta produção apresentada (BPA) com programação aprovada. Excedentes MAC são retidos no processamento financeiro (não rejeitados no arquivo BPA pela captação). |
| **Portaria de Consolidação GM/MS nº 1/2017** (Arts. 324–335) | 2017 | SIA é o sistema de informação ambulatorial do SUS; FPO é seu mecanismo de controle orçamentário. |

**Distinção operacional importante:** o FPO não rejeita individualmente cada registro de BPA — ele limita o **volume total pago** por procedimento/grupo ao CNES na competência. Registros acima do teto ficam "em estoque" no processamento financeiro. O sistema deve alertar, não bloquear.

---

## Regra 7 — Data do atendimento × Competência (retroatividade máxima)

**O quê:** o SIA aceita datas de atendimento das 3 competências anteriores à competência de apresentação (totalizando 4 competências: a atual + 3 anteriores). Registros com data de atendimento fora dessa janela são rejeitados.

**Ação no sistema:** **bloqueio** — registro com data fora da janela não pode ser persistido.

**Tabelas envolvidas:**
- `registros_producao.dt_atendimento` × `registros_producao.competencia` — validação por regra de data (sem tabela externa)

**Fontes:**

| Documento | Ano | Trecho relevante |
|---|---|---|
| **Portaria SAS/MS nº 496/2006** | 2006 | **Art. 5**: "a produção apresentada no SIA/SUS em até 3 meses após a realização do atendimento onerará o orçamento da competência de apresentação." Estabelece a janela de 3 meses retroativos. |
| **Portaria SAES/MS nº 1.110, de 11/11/2021** | 2021 | **Art. 1, III** (definição de "Apresentação Retroativa"): "envio de atendimentos em competência posterior à do atendimento, respeitado o prazo máximo de até **4 competências** (contando a partir do mês do atendimento)." **Art. 3 (SIA/SUS):** aceita competência corrente + 3 meses anteriores. URL: https://bvsms.saude.gov.br/bvs/saudelegis/saes/2021/prt1110_18_11_2021.html |
| **Manual Técnico Operacional SIA/SUS** | Ed. 2010 | "No BPA-Individualizado, a data de atendimento pertence à competência atual ou a três meses anteriores, no máximo." |

**Esclarecimento da contagem:** "3 competências retroativas" e "4 competências totais" são a mesma regra — a Portaria 1.110/2021 inclui a competência atual na contagem de 4.

---

## Regra 8 — Formato do CNS (dígito verificador)

**O quê:** o CNS com dígito verificador inválido é rejeitado na importação do BPA pelo SIA. O registro pode ser persistido (para não travar o profissional), mas a exportação do arquivo BPA deve ser bloqueada enquanto houver CNS inválido na competência.

**Ação no sistema:** **alerta** no registro — **bloqueio** na exportação BPA.

**Tabelas envolvidas:**
- `registros_producao.cns_hash` — o dígito verificador deve ser validado no momento da captura (antes de persistir o hash), pois o CNS em texto plano nunca é armazenado.

**Fontes:**

| Documento | Ano | Trecho relevante |
|---|---|---|
| **Algoritmo de validação do CNS** (DATASUS) | Vigente | Algoritmo de módulo 11 publicado pela RNDS/DATASUS. Referência técnica: https://integracao.esusab.ufsc.br/v211/docs/algoritmo_CNS.html |
| **Manual Técnico Operacional SIA/SUS** | Ed. 2010 | CNS com dígito verificador inválido causa rejeição na importação do arquivo BPA pelo SIA. |

---

## Matriz resumida

| # | Regra | Ação | Norma principal | Norma complementar | Dado SIGTAP | Dado SCNES/local |
|---|---|---|---|---|---|---|
| 1 | CBO × Procedimento | Bloqueio | Portaria GM 321/2007 → Consolidação GM 1/2017 (Anexo XVII) | Consolidação SAES 1/2022 (Art. 412) | `rl_proc_ocupacao` | `profissionais.cbo` |
| 2 | Habilitação CNES | Bloqueio | Portaria GM 321/2007 → Consolidação GM 1/2017 | Portaria SAS 1.229/2012; Consolidação SAES 1/2022 | `rl_proc_habilitacao` | `cnes_habilitacoes` |
| 3 | Serviço/Classif. CNES | Bloqueio | Portaria GM 321/2007 → Consolidação GM 1/2017 | Portaria SAS 911/2012; Consolidação SAES 1/2022 | `rl_proc_servico` | `cnes_servicos` |
| 4 | Instrumento BPA-C/I | Bloqueio | **Portaria SAS 709/2007** (institui BPA-I) | Portaria SAS 380/2010; **Portaria SAS 1.362/2013** (Art. 2) | `rl_proc_registro` | `registros_producao` |
| 5 | Duplicidade | Alerta | Manual Operacional SIA/SUS; Portaria SAES 1.110/2021 | Portaria SAS 1.362/2013 (Art. 2) | — | `registros_producao` |
| 6 | FPO (teto MAC) | Alerta | **Portaria SAS 496/2006** (Arts. 1, 5, 7) | Consolidação GM 1/2017 (Arts. 324–335) | — | `fpo_programacao` + `registros_producao` |
| 7 | Retroatividade (máx. 3 comp.) | Bloqueio | **Portaria SAS 496/2006** (Art. 5) | **Portaria SAES 1.110/2021** (Art. 1 III, Art. 3) | — | Regra de data |
| 8 | CNS inválido (dígito verifador) | Alerta/bloqueio exportação | Algoritmo DATASUS/RNDS | Manual Operacional SIA/SUS | — | Algoritmo local |

---

## O que o SIGTAP disponibiliza vs. o que o PRD menciona (gap análise)

### Disponível no BDSIA — pode ser implementado com dados locais
- ✅ CBO × Procedimento (`rl_proc_ocupacao`)
- ✅ Habilitação CNES × Procedimento (`rl_proc_habilitacao` — join via `co_habilitacao`, não `nu_grupo_habilitacao`)
- ✅ Serviço/Classificação CNES × Procedimento (`rl_proc_servico`)
- ✅ Instrumento correto BPA-C vs. BPA-I (`rl_proc_registro`)
- ✅ Compatibilidade entre procedimentos (`rl_procedimento_compativel` + `rl_excecao_compatibilidade`)

### Disponível apenas como regra local (sem tabela SIGTAP)
- ✅ Duplicidade — lógica sobre `registros_producao`
- ✅ FPO — lógica sobre `fpo_programacao` + `registros_producao`
- ✅ Retroatividade — regra de data fixa (3 competências anteriores)
- ✅ CNS inválido — algoritmo módulo 11

### Fora do escopo MVP (listado para consciência)
- ⏳ Compatibilidade entre procedimentos (`rl_procedimento_compativel`) — regra mais complexa, muitos pares; implementar pós-BPA
- ⏳ Incremento de valor por habilitação (`rl_procedimento_incremento`) — relevante para auditoria financeira, não para bloqueio de registro
- ⏳ Validação CID × Procedimento (`rl_procedimento_cid`) — listada como v2 no PRD

---

*FaturaSUS — DataBrasil | Referência normativa para passo 6 (validação anti-glosa) | Abril/2026*
