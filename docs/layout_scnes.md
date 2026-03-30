# Layout SCNES — Arquivos PF, HB e ST

Mapeamento dos arquivos de dados abertos do CNES (Cadastro Nacional de Estabelecimentos de Saúde) relevantes para o FaturaSUS.

---

## 1. Fonte de download

### ZIP nacional — ST, PF, SR (usado pelo FaturaSUS)

| Item | Valor |
|---|---|
| FTP | `ftp://ftp.datasus.gov.br/cnes/BASE_DE_DADOS_CNES_{AAMM}.ZIP` |
| Exemplo | `ftp://ftp.datasus.gov.br/cnes/BASE_DE_DADOS_CNES_202602.ZIP` |
| Formato | **CSV com separador `;`, encoding Latin-1** (não `.dbf` — `dbfread` não serve) |
| Documentação | https://cnes.datasus.gov.br/pages/downloads/documentacao.jsp |

Download via curl:
```bash
curl -o backend/data/cnes/BASE_DE_DADOS_CNES_202602.ZIP \
  "ftp://ftp.datasus.gov.br/cnes/BASE_DE_DADOS_CNES_202602.ZIP"
```

### Mapeamento arquivo → tabela (ZIP nacional)

| Tabela PostgreSQL | Arquivo no ZIP | Observações |
|---|---|---|
| `cnes_estabelecimentos` | `tbEstabelecimento{AAMM}.csv` | CNES = `CO_CNES` (7 chars) |
| `cnes_profissionais` | `tbCargaHorariaSus{AAMM}.csv` + JOIN `tbDadosProfissionalSus{AAMM}.csv` | Ver §3.3 abaixo |
| `cnes_servicos` | `rlEstabServClass{AAMM}.csv` | `CO_AMBULATORIAL_SUS='1'` equivale a `AMBUL='S'` |
| `cnes_habilitacoes` | **ausente no ZIP** | Usar caminho `.dbc` por UF (§1.2) |

### .dbc por UF — HB obrigatório

Habilitações **não estão no ZIP nacional**. O ZIP contém apenas `tbSubGruposHabilitacao` (tabela de domínio com nomes — 560 linhas), sem vínculos estabelecimento×habilitação.

| Item | Valor |
|---|---|
| FTP | `ftp://ftp.datasus.gov.br/dissemin/publicos/CNES/200508_/Dados/HB/` |
| Naming | `HB{UF}{AA}{MM}.dbc` — ex: `HBSP2602.dbc`, `HBRJ2602.dbc` |
| Formato | `.dbc` (DBF comprimido, algoritmo blast/PKWare) |
| Disponível desde | mar/2007 |
| Leitura | `dbc-to-dbf` (Python puro) + `dbfread` ou `pandas` — **sem PySUS** |

> PySUS não é pacote oficial (projeto acadêmico AlertaDengue) e tem histórico de quebra por mudanças no FTP. Para atualização mensal em produção usar `dbc-to-dbf` + `ftplib` diretamente.

O caminho `.dbc` também pode ser usado para ST/PF/SR por UF quando necessário (filtro geográfico antes da ingestão).

---

## 2. Formato e encoding

| Fonte | Formato | Encoding | Leitura em Python |
|---|---|---|---|
| ZIP nacional (ST, PF, SR) | CSV com separador `;` | Latin-1 | `pandas.read_csv(sep=';', encoding='latin-1')` |
| .dbc por UF (HB) | DBF comprimido (blast/PKWare) | Latin-1 | `dbc-to-dbf` (decompress) + `dbfread` |

**Pipeline ZIP:** `pandas.read_csv(sep=';', encoding='latin-1')` → filtrar → PostgreSQL (upsert).

**Pipeline HB:** `ftplib` (download) → `dbc-to-dbf` (decompress) → `dbfread` → filtrar → PostgreSQL (upsert).

---

## 3. PF — Profissionais (Pessoa Física)

Vincula profissionais a estabelecimentos de saúde. Um profissional pode ter múltiplos vínculos (CBOs distintos) no mesmo CNES.

**Chave composta:** (`CNES`, `CPF_PROF`, `CBO`, `COMPETEN`)

### 3.1 Todas as colunas

| # | Coluna | Tipo | Tam | Descrição |
|---|---|---|---|---|
| 1 | `CNES` | C | 7 | Código CNES do estabelecimento (FK → ST) |
| 2 | `CODUFMUN` | C | 6 | Código IBGE UF+Município |
| 3 | `REGSAUDE` | C | 4 | Região de saúde |
| 4 | `MICR_REG` | C | 6 | Microrregião de saúde |
| 5 | `DISTRSAN` | C | 4 | Distrito sanitário |
| 6 | `DISTRADM` | C | 4 | Distrito administrativo |
| 7 | `TPGESTAO` | C | 1 | Tipo de gestão (M/E/D/S) |
| 8 | `PF_PJ` | C | 1 | Pessoa Física (1) ou Jurídica (3) |
| 9 | `CPF_CNPJ` | C | 14 | CPF ou CNPJ do estabelecimento |
| 10 | `NIV_DEP` | C | 1 | Nível de dependência |
| 11 | `CNPJ_MAN` | C | 14 | CNPJ da mantenedora |
| 12 | `ESFERA_A` | C | 2 | Esfera administrativa |
| 13 | `ATIVIDAD` | C | 2 | Atividade ensino/pesquisa |
| 14 | `RETENCAO` | C | 2 | Retenção de tributos |
| 15 | `NATUREZA` | C | 2 | Natureza da organização |
| 16 | `CLIENTEL` | C | 2 | Fluxo de clientela |
| 17 | `TP_UNID` | C | 2 | Tipo de unidade |
| 18 | `TURNO_AT` | C | 2 | Turno de atendimento |
| 19 | `NIV_HIER` | C | 2 | Nível de hierarquia |
| 20 | `TERCEIRO` | C | 1 | Estabelecimento terceirizado (S/N) |
| 21 | `CPF_PROF` | C | 11 | CPF do profissional |
| 22 | `CNS_PROF` | C | 15 | CNS do profissional |
| 23 | `NOMEPROF` | C | 60 | Nome completo do profissional |
| 24 | `CBO` | C | 6 | Código CBO-2002 |
| 25 | `CBOUNICO` | C | 1 | CBO único (S/N) |
| 26 | `REGISTRO` | C | 13 | Registro no conselho de classe |
| 27 | `CONSELHO` | C | 2 | Código do conselho de classe |
| 28 | `VINCULAC` | C | 6 | Código do vínculo empregatício |
| 29 | `VINCUL_C` | C | 1 | Vínculo contratado SUS (S/N) |
| 30 | `VINCUL_A` | C | 1 | Vínculo autônomo SUS (S/N) |
| 31 | `VINCUL_N` | C | 1 | Vínculo não identificado (S/N) |
| 32 | `PROF_SUS` | C | 1 | **Atende SUS (S/N)** |
| 33 | `PROFNSUS` | C | 1 | Atende não-SUS (S/N) |
| 34 | `HORAOUTR` | N | 3 | CH outras atividades |
| 35 | `HORAHOSP` | N | 3 | CH hospitalar |
| 36 | `HORA_AMB` | N | 3 | CH ambulatorial |
| 37 | `COMPETEN` | C | 6 | Competência (AAAAMM) |
| 38 | `UFMUNRES` | C | 6 | Município de residência (IBGE) |
| 39 | `NAT_JUR` | C | 4 | Natureza jurídica |

### 3.2 Mapeamento real CSV → PostgreSQL

O arquivo `tbCargaHorariaSus{AAMM}.csv` **não contém CNS nem nome do profissional**. É necessário JOIN com `tbDadosProfissionalSus{AAMM}.csv` (7,6M linhas) via `CO_PROFISSIONAL_SUS` (hash hex 16 chars).

| Coluna CSV (`tbCargaHorariaSus`) | Coluna CSV (`tbDadosProfissionalSus`) | Campo PostgreSQL | Observação |
|---|---|---|---|
| `CO_UNIDADE` | — | `cnes` CHAR(7) | CO_UNIDADE tem 31 chars; CNES = últimos 7 chars (validar amostra) ou join com tbEstabelecimento |
| `CO_PROFISSIONAL_SUS` → join | `CO_CNS` | `cns_prof` CHAR(15) | Hash descartado após join; persistir só o CNS |
| — | `NO_PROFISSIONAL` | `nomeprof` VARCHAR(60) | Via join |
| `CO_CBO` | — | `cbo` CHAR(6) | |
| `TP_SUS_NAO_SUS` | — | `prof_sus` CHAR(1) | Filtro: `upper(TP_SUS_NAO_SUS) = 'S'` |
| `QT_CARGA_HORARIA_AMBULATORIAL` | — | `hora_amb` SMALLINT | |
| `IND_VINCULACAO` | — | `vinculac` CHAR(6) | |
| `CO_CONSELHO_CLASSE` | — | `conselho` CHAR(2) | |
| `NU_REGISTRO` | — | `registro` VARCHAR(13) | Número no conselho — obrigatório BPA-I |
| (derivado de CO_UNIDADE) | — | `competen` CHAR(6) | Não há coluna COMPETEN; derivar da competência do arquivo |

**Filtro na importação:** `upper(TP_SUS_NAO_SUS) == 'S'` (valores observados: `'S'`, `'N'`, `'s'`)

**Estratégia de join na ingestão:** carregar `tbDadosProfissionalSus` em dict `{CO_PROFISSIONAL_SUS: (CO_CNS, NO_PROFISSIONAL)}` em memória antes de iterar `tbCargaHorariaSus`.

**Nota sobre CBO:** desde ago/2007 o CNES usa CBO-2002 (6 dígitos). Registros anteriores podem ter CBO-1994 (5 dígitos). Normalizar para 6 dígitos (pad left '0') antes de cruzar com SIGTAP.

---

## 4. HB — Habilitações

Habilitações (qualificações) de cada estabelecimento. Determina quais procedimentos o CNES pode faturar.

**Chave composta:** (`CNES`, `SGRUPHAB`, `COMPETEN`)

### 4.1 Todas as colunas

| # | Coluna | Tipo | Tam | Descrição |
|---|---|---|---|---|
| 1 | `CNES` | C | 7 | Código CNES (FK → ST) |
| 2 | `CODUFMUN` | C | 6 | Código IBGE UF+Município |
| 3 | `COMPETEN` | C | 6 | Competência (AAAAMM) |
| 4 | `SGRUPHAB` | C | 4 | Código do subgrupo de habilitação |
| 5 | `CMPT_INI` | C | 6 | Competência inicial (AAAAMM) |
| 6 | `CMPT_FIM` | C | 6 | Competência final (AAAAMM) |
| 7 | `NULEITOS` | N | 4 | Leitos associados |
| 8 | `PORTARIA` | C | 20 | Nº da portaria de habilitação |
| 9 | `DTPORTAR` | C | 8 | Data da portaria (DDMMAAAA) |
| 10 | `MAPORTAR` | C | 6 | Mês/Ano da portaria (AAAAMM) |

### 4.2 Estrutura do código SGRUPHAB

```
SGRUPHAB = TTSS
  TT = Tipo (01=Federal/SAS/MS, 09-29=Estadual/Municipal)
  SS = Subtipo dentro do grupo
```

Exemplo: procedimentos oncológicos exigem habilitação `17xx`.

### 4.3 Colunas a persistir no PostgreSQL

| Coluna | Justificativa |
|---|---|
| `CNES` | FK para estabelecimento |
| `SGRUPHAB` | Código de habilitação — join com `sigtap_rl_proc_habilitacao.co_habilitacao` (NÃO `nu_grupo_habilitacao`, que chega vazio no arquivo fonte) |
| `CMPT_INI` | Início da vigência |
| `CMPT_FIM` | Fim da vigência |
| `COMPETEN` | Controle temporal |
| `PORTARIA` | Rastreabilidade |

**Validação de vigência:** `CMPT_INI <= competência_atual <= CMPT_FIM`

---

## 5. ST — Estabelecimentos

Cadastro master dos estabelecimentos. Arquivo muito grande (150+ colunas). Aqui apenas as relevantes para faturamento.

**Chave composta:** (`CNES`, `COMPETEN`)

### 5.1 Colunas relevantes para faturamento BPA

#### Identificação

| # | Coluna | Tipo | Tam | Descrição |
|---|---|---|---|---|
| 1 | `CNES` | C | 7 | Código CNES (**PK**) |
| 2 | `CODUFMUN` | C | 6 | Código IBGE UF+Município |
| 3 | `COD_CEP` | C | 8 | CEP |
| 4 | `CPF_CNPJ` | C | 14 | CPF ou CNPJ |
| 5 | `PF_PJ` | C | 1 | Pessoa Física (1) ou Jurídica (3) |
| 6 | `CNPJ_MAN` | C | 14 | CNPJ da mantenedora |

#### Classificação administrativa

| # | Coluna | Tipo | Tam | Descrição |
|---|---|---|---|---|
| 7 | `NIV_DEP` | C | 1 | Nível de dependência |
| 8 | `VINC_SUS` | C | 1 | Vínculo com SUS (S/N) |
| 9 | `TPGESTAO` | C | 1 | Tipo de gestão (D/E/M/S) |
| 10 | `ESFERA_A` | C | 2 | Esfera administrativa |
| 11 | `NATUREZA` | C | 2 | Natureza da organização |
| 12 | `NAT_JUR` | C | 4 | Natureza jurídica |
| 13 | `CLIENTEL` | C | 2 | Fluxo de clientela |
| 14 | `TP_UNID` | C | 2 | Tipo de unidade |
| 15 | `TURNO_AT` | C | 2 | Turno de atendimento |
| 16 | `NIV_HIER` | C | 2 | Nível de hierarquia |
| 17 | `TP_PREST` | C | 2 | Tipo de prestador |

#### Atendimento

| # | Coluna | Tipo | Tam | Descrição |
|---|---|---|---|---|
| 18 | `ATENDAMB` | C | 1 | Atendimento ambulatorial (S/N) |
| 19 | `NIVATE_A` | C | 1 | Nível de atenção ambulatorial |

#### Temporal

| # | Coluna | Tipo | Tam | Descrição |
|---|---|---|---|---|
| 20 | `COMPETEN` | C | 6 | Competência (AAAAMM) |

### 5.2 Colunas a persistir no PostgreSQL

| Coluna | Justificativa |
|---|---|
| `CNES` | PK — chave universal do sistema |
| `CODUFMUN` | Município — cabeçalho do BPA |
| `CPF_CNPJ` | Identificação fiscal — cabeçalho do BPA |
| `VINC_SUS` | Filtro: só estabelecimentos SUS |
| `TP_UNID` | Tipo de unidade — regras de faturamento |
| `NIV_HIER` | Nível hierárquico — compatibilidade procedimento |
| `TP_PREST` | Tipo de prestador — regras BPA |
| `ATENDAMB` | Confirmação de ambulatório |
| `NIVATE_A` | Nível de atenção ambulatorial |
| `COMPETEN` | Controle temporal |

**Descarte seguro:** colunas de leitos (`QTLEITP*`), serviços de apoio (`SERAP*`), resíduos (`RES_*`), comissões (`COMISS*`), infraestrutura (`QTINST*`) — irrelevantes para faturamento ambulatorial.

---

## 6. Relações entre arquivos

```
ST (Estabelecimento)            PF (Profissional)
┌──────────────────┐            ┌──────────────────┐
│ CNES (PK)    C(7)│◄───┬───────│ CNES (FK)    C(7)│
│ CODUFMUN     C(6)│    │       │ CNS_PROF    C(15)│
│ TP_UNID      C(2)│    │       │ NOMEPROF    C(60)│
│ VINC_SUS     C(1)│    │       │ CBO          C(6)│──→ SIGTAP rl_proc_ocupacao
│ COMPETEN     C(6)│    │       │ PROF_SUS     C(1)│
│ ...              │    │       │ HORA_AMB     N(3)│
└──────────────────┘    │       │ COMPETEN     C(6)│
                        │       └──────────────────┘
HB (Habilitação)        │
┌──────────────────┐    │
│ CNES (FK)    C(7)│────┤
│ SGRUPHAB     C(4)│──────────→ SIGTAP rl_proc_habilitacao.NU_GRUPO_HABILITACAO
│ CMPT_INI     C(6)│    │       (⚠️ não CO_HABILITACAO)
│ CMPT_FIM     C(6)│    │
│ COMPETEN     C(6)│    │
└──────────────────┘    │
                        │
SR (Serviços)           │
┌──────────────────┐    │
│ CNES (FK)    C(7)│────┘
│ SERV_ESP     C(3)│──────────→ SIGTAP rl_proc_servico.CO_SERVICO
│ CLASS_SR     C(3)│──────────→ SIGTAP rl_proc_servico.CO_CLASSIFICACAO
│ AMBUL        C(1)│
│ COMPETEN     C(6)│
└──────────────────┘
```

### Joins internos

| Relação | Join |
|---|---|
| Profissional → Estabelecimento | `PF.CNES = ST.CNES` |
| Habilitação → Estabelecimento | `HB.CNES = ST.CNES` |
| Temporal (todos) | `*.COMPETEN` (AAAAMM) |

### Joins externos (→ SIGTAP)

| De | Para | Chave | Validação |
|---|---|---|---|
| `PF.CBO` | `sigtap_cbo_procedimento.CO_CBO` | CBO 6 dígitos | Profissional pode realizar o procedimento? |
| `HB.SGRUPHAB` | Tabela de habilitações exigidas por procedimento | Código 4 dígitos | Estabelecimento tem habilitação exigida? |
| `ST.CNES` | Cabeçalho BPA | CNES 7 dígitos | Identificação do estabelecimento |

---

## 7. Validações anti-glosa usando SCNES

| Regra | Dados necessários | Arquivos |
|---|---|---|
| CBO do profissional é compatível com o procedimento? | `PF.CBO` × SIGTAP | PF |
| Profissional atende SUS? | `PF.PROF_SUS = 'S'` | PF |
| CH ambulatorial suficiente para a produção? | `PF.HORA_AMB` × qtd registros | PF |
| Estabelecimento tem habilitação exigida pelo procedimento? | `HB.SGRUPHAB` vigente | HB |
| Estabelecimento é vinculado ao SUS? | `ST.VINC_SUS = 'S'` | ST |
| Tipo de unidade é compatível? | `ST.TP_UNID` × regras SIGTAP | ST |

---

## 8. Schema PostgreSQL recomendado

```sql
-- Estabelecimentos (importação mensal do ST)
CREATE TABLE cnes_estabelecimentos (
    cnes         CHAR(7)  NOT NULL,
    codufmun     CHAR(6)  NOT NULL,
    cpf_cnpj     VARCHAR(14),
    vinc_sus     CHAR(1),
    tp_unid      CHAR(2),
    niv_hier     CHAR(2),
    tp_prest     CHAR(2),
    atendamb     CHAR(1),
    nivate_a     CHAR(1),
    competen     CHAR(6)  NOT NULL,
    PRIMARY KEY (cnes, competen)
);

-- Profissionais (importação mensal do PF, filtro PROF_SUS = 'S')
CREATE TABLE cnes_profissionais (
    cnes         CHAR(7)  NOT NULL,
    cns_prof     VARCHAR(15) NOT NULL,
    nomeprof     VARCHAR(60),
    cbo          CHAR(6)  NOT NULL,
    prof_sus     CHAR(1)  NOT NULL DEFAULT 'S',
    hora_amb     SMALLINT,
    vinculac     CHAR(6),
    conselho     CHAR(2),
    competen     CHAR(6)  NOT NULL,
    PRIMARY KEY (cnes, cns_prof, cbo, competen),
    FOREIGN KEY (cnes, competen) REFERENCES cnes_estabelecimentos(cnes, competen)
);

-- Habilitações (importação mensal do HB)
CREATE TABLE cnes_habilitacoes (
    cnes         CHAR(7)  NOT NULL,
    sgruphab     CHAR(4)  NOT NULL,
    cmpt_ini     CHAR(6),
    cmpt_fim     CHAR(6),
    portaria     VARCHAR(20),
    competen     CHAR(6)  NOT NULL,
    PRIMARY KEY (cnes, sgruphab, competen),
    FOREIGN KEY (cnes, competen) REFERENCES cnes_estabelecimentos(cnes, competen)
);

-- Índices para validação anti-glosa
CREATE INDEX idx_prof_cbo ON cnes_profissionais(cbo);
CREATE INDEX idx_prof_cns ON cnes_profissionais(cns_prof);
CREATE INDEX idx_hab_vigencia ON cnes_habilitacoes(cnes, sgruphab, cmpt_ini, cmpt_fim);
```

---

## 6b. SR — Serviços do Estabelecimento

Serviços habilitados por estabelecimento. Determina quais serviços/classificações o CNES oferece, cruzando com `rl_procedimento_servico` do SIGTAP para validação anti-glosa.

**Chave composta:** (`CNES`, `SERV_ESP`, `CLASS_SR`, `COMPETEN`)

### 6b.1 Colunas relevantes

| # | Coluna | Tipo | Tam | Descrição |
|---|---|---|---|---|
| 1 | `CNES` | C | 7 | Código CNES (FK → ST) |
| 2 | `CODUFMUN` | C | 6 | Código IBGE UF+Município |
| 3 | `SERV_ESP` | C | 3 | **Código do serviço** — corresponde a `CO_SERVICO` no SIGTAP |
| 4 | `CLASS_SR` | C | 3 | **Classificação do serviço** — corresponde a `CO_CLASSIFICACAO` no SIGTAP |
| 5 | `SRVUNICO` | C | 1 | Serviço único no estabelecimento (S/N) |
| 6 | `NIVEL_SR` | C | 2 | Nível do serviço |
| 7 | `AMBUL` | C | 1 | Atendimento ambulatorial (S/N) |
| 8 | `HOSP` | C | 1 | Internação (S/N) |
| 9 | `COMPETEN` | C | 6 | Competência (AAAAMM) |

As demais colunas (identificação do estabelecimento: `TPGESTAO`, `PF_PJ`, `CPF_CNPJ`, `ESFERA_A`, `NATUREZA`, etc.) são idênticas às do arquivo ST e irrelevantes para a validação de serviço.

### 6b.2 Colunas a persistir no PostgreSQL

| Coluna | Justificativa |
|---|---|
| `CNES` | FK para estabelecimento |
| `SERV_ESP` | Join com `rl_procedimento_servico.CO_SERVICO` |
| `CLASS_SR` | Join com `rl_procedimento_servico.CO_CLASSIFICACAO` |
| `AMBUL` | Filtro: só serviços ambulatoriais (`= 'S'`) |
| `COMPETEN` | Controle temporal |

**Filtro na importação:** `WHERE AMBUL = 'S'`

### 6b.3 Fonte e nomenclatura

| Item | Valor |
|---|---|
| Subpasta FTP | `.../CNES/200508_/Dados/SR/` |
| Naming | `SR{UF}{AA}{MM}.dbc` — ex: `SRSP2603.dbc` |
| Disponível desde | ago/2005 |

### 6b.4 Join com SIGTAP

```sql
-- Estabelecimento tem o serviço/classificação exigido pelo procedimento?
SELECT 1
FROM   cnes_servicos cs
JOIN   sigtap_rl_proc_servico rps
    ON  rps.co_servico      = cs.serv_esp
   AND  rps.co_classificacao = cs.class_sr
   AND  rps.dt_competencia   = :competencia
WHERE  cs.cnes      = :cnes
  AND  cs.competen  = :competencia
  AND  rps.co_procedimento = :co_procedimento
```

### 6b.5 Schema PostgreSQL

```sql
CREATE TABLE cnes_servicos (
    cnes        CHAR(7)  NOT NULL,
    serv_esp    CHAR(3)  NOT NULL,
    class_sr    CHAR(3)  NOT NULL,
    ambul       CHAR(1),
    competen    CHAR(6)  NOT NULL,
    PRIMARY KEY (cnes, serv_esp, class_sr, competen),
    FOREIGN KEY (cnes, competen) REFERENCES cnes_estabelecimentos(cnes, competen)
);

CREATE INDEX idx_srv_cnes_servico ON cnes_servicos(cnes, serv_esp, class_sr);
```

---

## 9. Notas de implementação

### Pipeline de importação

**ST + PF + SR (ZIP nacional):**
1. Download do ZIP via `ftplib` ou curl
2. Leitura com `pandas.read_csv(sep=';', encoding='latin-1')`
3. Filtros: `upper(TP_SUS_NAO_SUS) == 'S'` (PF) · `CO_AMBULATORIAL_SUS == '1'` (SR)
4. Join PF: carregar `tbDadosProfissionalSus` em dict memória → enriquecer com CNS + nome
5. Upsert com `ON CONFLICT ... DO UPDATE`

**HB (.dbc por UF — lista de UFs configurável):**
1. Download de `HB{UF}{AAMM}.dbc` para cada UF da lista via `ftplib`
2. Descompressão: `dbc-to-dbf` (Python puro, algoritmo blast estável — sem PySUS)
3. Leitura: `dbfread` com `encoding='latin-1'`
4. Filtro por `CODUFMUN` se necessário
5. Upsert com `ON CONFLICT ... DO UPDATE`

### Peculiaridades

- **CNES sempre 7 caracteres** com zero à esquerda — manter como `CHAR(7)`, nunca converter para inteiro
- **CO_UNIDADE** em `tbCargaHorariaSus` tem 31 chars (código composto) — CNES nos últimos 7 chars (validar amostra)
- **CODUFMUN** é IBGE 6 dígitos (sem dígito verificador) — diferente do IBGE 7 dígitos
- **Nomes** (`NO_PROFISSIONAL`) vêm em MAIÚSCULAS com acentos Latin-1
- **CPF** é mascarado com `X` na fonte pública (`XXX.786.996.XX`) — não usar para identificação
- **COMPETEN** formato `AAAAMM` — string, não data. Comparar lexicograficamente funciona
- **CBO pode ter 5 ou 6 dígitos** — normalizar para 6 dígitos (pad left com zero) antes de cruzar com SIGTAP
- **HB não está no ZIP nacional** — obrigatório usar `.dbc` por UF para `cnes_habilitacoes`

### Volume estimado

| Fonte | Arquivo | Registros típicos | Tamanho |
|---|---|---|---|
| ZIP nacional | `tbCargaHorariaSus` (PF) | ~15M (nacional) | 806 MB |
| ZIP nacional | `tbDadosProfissionalSus` | ~7,6M (nacional) | 891 MB |
| ZIP nacional | `tbEstabelecimento` (ST) | ~350K (nacional) | 273 MB |
| ZIP nacional | `rlEstabServClass` (SR) | ~500K (nacional) | 126 MB |
| .dbc por UF | `HB{UF}` (SP) | ~50K | ~5 MB |

Filtrar por `CODUFMUN` do município-alvo reduz para centenas/milhares de registros.
