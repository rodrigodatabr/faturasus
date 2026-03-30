# Layout do Pacote BDSIA (SIGTAP/DATASUS)

Mapeamento completo dos arquivos `.txt` do pacote BDSIA para importação no PostgreSQL do FaturaSUS.

## Fonte oficial de download

| Item | Valor |
|------|-------|
| Portal | http://sigtap.datasus.gov.br |
| Download | http://sigtap.datasus.gov.br/tabela-unificada/app/download.jsp |
| RSS competencias | `/tabela-unificada/competencias.rss` |
| Padrão nome arquivo | `BDSIAaaaammv.exe` (aaaa=ano, mm=mes, v=versao) |
| Wiki | https://wiki.saude.gov.br/sigtap/index.php/Download |

Seleciona-se a competencia (mes/ano) e o sistema gera um ZIP com todos os `.txt` + seus respectivos `_layout.txt`.

## Formato geral dos arquivos

| Propriedade | Valor |
|-------------|-------|
| Encoding | ISO-8859-1 (Latin-1) |
| Formato | Posicional (largura fixa) — sem delimitadores |
| Quebra de linha | CRLF (`\r\n`) |
| Versionamento | Campo `DT_COMPETENCIA` (AAAAMM) em quase todas as tabelas |
| Total de tabelas | 41 (24 dominio `tb_` + 17 relacionamento `rl_`) |
| Arquivos por tabela | 2 (dados `.txt` + `_layout.txt` com documentacao) |

---

## Inventario completo de arquivos

### Tabelas de dominio (tb_)

| # | Arquivo | Descricao | Relevancia BPA |
|---|---------|-----------|----------------|
| 1 | `tb_procedimento.txt` | Procedimentos — tabela central | **Essencial** |
| 2 | `tb_grupo.txt` | Grupos de procedimentos | Essencial |
| 3 | `tb_sub_grupo.txt` | Subgrupos | Essencial |
| 4 | `tb_forma_organizacao.txt` | Formas de organizacao | Essencial |
| 5 | `tb_financiamento.txt` | Tipos de financiamento (MAC, PAB, FAEC) | **Essencial** |
| 6 | `tb_rubrica.txt` | Rubricas orcamentarias | Essencial |
| 7 | `tb_registro.txt` | Instrumentos de registro (BPA-C, BPA-I, APAC, AIH) | **Essencial** |
| 8 | `tb_ocupacao.txt` | Ocupacoes CBO | **Essencial** |
| 9 | `tb_servico.txt` | Servicos | Importante |
| 10 | `tb_servico_classificacao.txt` | Classificacoes de servico | Importante |
| 11 | `tb_cid.txt` | CID-10 | Importante |
| 12 | `tb_habilitacao.txt` | Habilitacoes | Importante |
| 13 | `tb_grupo_habilitacao.txt` | Grupos de habilitacao | Importante |
| 14 | `tb_descricao.txt` | Descricao completa dos procedimentos | Util (embeddings) |
| 15 | `tb_detalhe.txt` | Atributos complementares | Opcional |
| 16 | `tb_descricao_detalhe.txt` | Descricao dos detalhes | Opcional |
| 17 | `tb_modalidade.txt` | Modalidades de atendimento | Opcional |
| 18 | `tb_componente_rede.txt` | Componentes de rede | Descartavel |
| 19 | `tb_rede_atencao.txt` | Redes de atencao | Descartavel |
| 20 | `tb_regra_condicionada.txt` | Regras condicionadas | Descartavel |
| 21 | `tb_renases.txt` | RENASES | Descartavel |
| 22 | `tb_tuss.txt` | Terminologia TUSS | Descartavel |
| 23 | `tb_tipo_leito.txt` | Tipos de leito | **Fora de escopo** (hospitalar) |
| 24 | `tb_sia_sih.txt` | Mapeamento legado SIA/SIH | Descartavel |

### Tabelas de relacionamento (rl_)

| # | Arquivo | Descricao | Relevancia BPA |
|---|---------|-----------|----------------|
| 1 | `rl_procedimento_ocupacao.txt` | Procedimento x CBO | **Essencial** (anti-glosa) |
| 2 | `rl_procedimento_registro.txt` | Procedimento x Instrumento (BPA-C/I) | **Essencial** (anti-glosa) |
| 3 | `rl_procedimento_servico.txt` | Procedimento x Servico/Classificacao | **Essencial** (anti-glosa CNES) |
| 4 | `rl_procedimento_cid.txt` | Procedimento x CID | Importante |
| 5 | `rl_procedimento_habilitacao.txt` | Procedimento x Habilitacao | **Essencial** (anti-glosa) |
| 6 | `rl_procedimento_compativel.txt` | Compatibilidade entre procedimentos | Importante |
| 7 | `rl_excecao_compatibilidade.txt` | Excecoes de compatibilidade | Importante |
| 8 | `rl_procedimento_incremento.txt` | Incrementos por habilitacao | Opcional |
| 9 | `rl_procedimento_detalhe.txt` | Procedimento x Atributos complementares | Opcional |
| 10 | `rl_procedimento_modalidade.txt` | Procedimento x Modalidade | Opcional |
| 11 | `rl_procedimento_origem.txt` | Procedimento x Codigo de origem | Descartavel |
| 12 | `rl_procedimento_sia_sih.txt` | Mapeamento legado SIA/SIH | Descartavel |
| 13 | `rl_procedimento_comp_rede.txt` | Procedimento x Componente de rede | Descartavel |
| 14 | `rl_procedimento_regra_cond.txt` | Procedimento x Regras condicionadas | Descartavel |
| 15 | `rl_procedimento_renases.txt` | Procedimento x RENASES | Descartavel |
| 16 | `rl_procedimento_tuss.txt` | Procedimento x TUSS | Descartavel |
| 17 | `rl_procedimento_leito.txt` | Procedimento x Tipo de leito | **Fora de escopo** (hospitalar) |

---

## Layout detalhado — Tabelas essenciais

### tb_procedimento.txt (336 chars/linha)

Tabela central do SIGTAP. Cada procedimento e uma linha.

> **Nota:** O layout oficial publicado no wiki indica 330 chars com VL_* de 10 chars.
> O arquivo real (verificado em 202603) tem **336 chars** — VL_SH, VL_SA e VL_SP sao **12 chars cada**.
> As posicoes abaixo refletem o arquivo real.

| Campo | Inicio | Fim | Tam | Tipo | PK/FK | Descricao |
|-------|--------|-----|-----|------|-------|-----------|
| CO_PROCEDIMENTO | 1 | 10 | 10 | CHAR | **PK** | Codigo (formato `GGSSFFPPPP`) |
| NO_PROCEDIMENTO | 11 | 260 | 250 | VARCHAR | | Nome do procedimento |
| TP_COMPLEXIDADE | 261 | 261 | 1 | CHAR | | `0`=N/A, `1`=Basica, `2`=Media, `3`=Alta |
| TP_SEXO | 262 | 262 | 1 | CHAR | | `M`, `F`, `N`(ao se aplica) |
| QT_MAXIMA_EXECUCAO | 263 | 266 | 4 | INT | | Qtd maxima execucao |
| QT_DIAS_PERMANENCIA | 267 | 270 | 4 | INT | | Dias permanencia (hospitalar — ignorar) |
| QT_PONTOS | 271 | 274 | 4 | INT | | Pontos (SP) |
| VL_IDADE_MINIMA | 275 | 278 | 4 | INT | | Idade minima (meses ou anos) |
| VL_IDADE_MAXIMA | 279 | 282 | 4 | INT | | Idade maxima |
| VL_SH | 283 | 294 | **12** | INT | | Valor Servico Hospitalar (ignorar) |
| VL_SA | 295 | 306 | **12** | INT | | **Valor Servico Ambulatorial** |
| VL_SP | 307 | 318 | **12** | INT | | Valor Servico Profissional |
| CO_FINANCIAMENTO | 319 | 320 | 2 | CHAR | FK `tb_financiamento` | Tipo financiamento (MAC/PAB/FAEC) |
| CO_RUBRICA | 321 | 326 | 6 | CHAR | FK `tb_rubrica` | Rubrica orcamentaria |
| QT_TEMPO_PERMANENCIA | 327 | 330 | 4 | INT | | Tempo permanencia (hospitalar — ignorar) |
| DT_COMPETENCIA | 331 | 336 | 6 | CHAR | **PK** | Competencia AAAAMM |

**Nota sobre CO_PROCEDIMENTO:** Os 10 digitos codificam a hierarquia:
- Posicoes 1-2 = `CO_GRUPO`
- Posicoes 3-4 = `CO_SUB_GRUPO`
- Posicoes 5-6 = `CO_FORMA_ORGANIZACAO`
- Posicoes 7-10 = Sequencial dentro da forma de organizacao

**Nota sobre valores monetarios:** Campos `VL_*` sao inteiros sem separador decimal. Os 2 ultimos digitos representam centavos. Ex: `0000001250` = R$ 12,50.

### tb_financiamento.txt (108 chars/linha)

| Campo | Inicio | Fim | Tam | Tipo | PK/FK | Descricao |
|-------|--------|-----|-----|------|-------|-----------|
| CO_FINANCIAMENTO | 1 | 2 | 2 | CHAR | **PK** | Codigo financiamento |
| NO_FINANCIAMENTO | 3 | 102 | 100 | VARCHAR | | Nome |
| DT_COMPETENCIA | 103 | 108 | 6 | CHAR | **PK** | Competencia AAAAMM |

**Valores conhecidos de CO_FINANCIAMENTO:**

| Codigo | Significado | Relevancia FaturaSUS |
|--------|-------------|----------------------|
| `01` | MAC (Media e Alta Complexidade) | **Sim** — separa arquivo BPA |
| `02` | PAB (Piso da Atencao Basica) | **Sim** — separa arquivo BPA |
| `04` | FAEC (Fundo de Acoes Estrategicas e Compensacao) | Sim |
| `05` | Incentivo MAC | Opcional |
| `06` | Incentivo PAB | Opcional |
| `07` | CEREST | Raro |

### tb_registro.txt (58 chars/linha)

| Campo | Inicio | Fim | Tam | Tipo | PK/FK | Descricao |
|-------|--------|-----|-----|------|-------|-----------|
| CO_REGISTRO | 1 | 2 | 2 | CHAR | **PK** | Codigo instrumento |
| NO_REGISTRO | 3 | 52 | 50 | VARCHAR | | Nome do instrumento |
| DT_COMPETENCIA | 53 | 58 | 6 | CHAR | **PK** | Competencia AAAAMM |

**Valores conhecidos de CO_REGISTRO:**

| Codigo | Instrumento | Escopo FaturaSUS |
|--------|-------------|------------------|
| `01` | BPA-I (Individualizado) | **Sim** |
| `02` | BPA-C (Consolidado) | **Sim** |
| `03` | APAC | Fora de escopo |
| `04` | AIH | Fora de escopo |

### tb_ocupacao.txt (156 chars/linha)

| Campo | Inicio | Fim | Tam | Tipo | PK/FK | Descricao |
|-------|--------|-----|-----|------|-------|-----------|
| CO_OCUPACAO | 1 | 6 | 6 | CHAR | **PK** | Codigo CBO (6 digitos) |
| NO_OCUPACAO | 7 | 156 | 150 | VARCHAR | | Nome da ocupacao |

**Sem DT_COMPETENCIA** — tabela CBO nao e versionada por competencia no SIGTAP.

### tb_grupo.txt (108 chars/linha)

| Campo | Inicio | Fim | Tam | Tipo | PK/FK | Descricao |
|-------|--------|-----|-----|------|-------|-----------|
| CO_GRUPO | 1 | 2 | 2 | CHAR | **PK** | Codigo grupo |
| NO_GRUPO | 3 | 102 | 100 | VARCHAR | | Nome grupo |
| DT_COMPETENCIA | 103 | 108 | 6 | CHAR | **PK** | Competencia AAAAMM |

### tb_sub_grupo.txt (110 chars/linha)

| Campo | Inicio | Fim | Tam | Tipo | PK/FK | Descricao |
|-------|--------|-----|-----|------|-------|-----------|
| CO_GRUPO | 1 | 2 | 2 | CHAR | FK `tb_grupo` | Codigo grupo |
| CO_SUB_GRUPO | 3 | 4 | 2 | CHAR | **PK** | Codigo subgrupo |
| NO_SUB_GRUPO | 5 | 104 | 100 | VARCHAR | | Nome subgrupo |
| DT_COMPETENCIA | 105 | 110 | 6 | CHAR | **PK** | Competencia AAAAMM |

### tb_forma_organizacao.txt (112 chars/linha)

| Campo | Inicio | Fim | Tam | Tipo | PK/FK | Descricao |
|-------|--------|-----|-----|------|-------|-----------|
| CO_GRUPO | 1 | 2 | 2 | CHAR | FK `tb_grupo` | Codigo grupo |
| CO_SUB_GRUPO | 3 | 4 | 2 | CHAR | FK `tb_sub_grupo` | Codigo subgrupo |
| CO_FORMA_ORGANIZACAO | 5 | 6 | 2 | CHAR | **PK** | Codigo forma org |
| NO_FORMA_ORGANIZACAO | 7 | 106 | 100 | VARCHAR | | Nome forma org |
| DT_COMPETENCIA | 107 | 112 | 6 | CHAR | **PK** | Competencia AAAAMM |

### tb_rubrica.txt (~112 chars/linha)

| Campo | Inicio | Fim | Tam | Tipo | PK/FK | Descricao |
|-------|--------|-----|-----|------|-------|-----------|
| CO_RUBRICA | 1 | 6 | 6 | CHAR | **PK** | Codigo rubrica |
| NO_RUBRICA | 7 | 106 | 100 | VARCHAR | | Nome rubrica |
| DT_COMPETENCIA | 107 | 112 | 6 | CHAR | **PK** | Competencia AAAAMM |

---

## Layout detalhado — Tabelas de relacionamento essenciais

### rl_procedimento_ocupacao.txt (22 chars/linha)

Procedimento x CBO — validacao anti-glosa principal.

| Campo | Inicio | Fim | Tam | Tipo | PK/FK | Descricao |
|-------|--------|-----|-----|------|-------|-----------|
| CO_PROCEDIMENTO | 1 | 10 | 10 | CHAR | FK `tb_procedimento` | Codigo procedimento |
| CO_OCUPACAO | 11 | 16 | 6 | CHAR | FK `tb_ocupacao` | Codigo CBO |
| DT_COMPETENCIA | 17 | 22 | 6 | CHAR | | Competencia AAAAMM |

**PK composta:** (CO_PROCEDIMENTO, CO_OCUPACAO, DT_COMPETENCIA)

### rl_procedimento_registro.txt (18 chars/linha)

Procedimento x Instrumento — define se vai em BPA-C, BPA-I ou ambos.

| Campo | Inicio | Fim | Tam | Tipo | PK/FK | Descricao |
|-------|--------|-----|-----|------|-------|-----------|
| CO_PROCEDIMENTO | 1 | 10 | 10 | CHAR | FK `tb_procedimento` | Codigo procedimento |
| CO_REGISTRO | 11 | 12 | 2 | CHAR | FK `tb_registro` | Instrumento (01=BPA-I, 02=BPA-C) |
| DT_COMPETENCIA | 13 | 18 | 6 | CHAR | | Competencia AAAAMM |

**PK composta:** (CO_PROCEDIMENTO, CO_REGISTRO, DT_COMPETENCIA)

### rl_procedimento_servico.txt (22 chars/linha)

Procedimento x Servico/Classificacao — valida contra SCNES.

| Campo | Inicio | Fim | Tam | Tipo | PK/FK | Descricao |
|-------|--------|-----|-----|------|-------|-----------|
| CO_PROCEDIMENTO | 1 | 10 | 10 | CHAR | FK `tb_procedimento` | Codigo procedimento |
| CO_SERVICO | 11 | 13 | 3 | CHAR | FK `tb_servico` | Codigo servico |
| CO_CLASSIFICACAO | 14 | 16 | 3 | CHAR | FK `tb_servico_classificacao` | Classificacao do servico |
| DT_COMPETENCIA | 17 | 22 | 6 | CHAR | | Competencia AAAAMM |

**PK composta:** (CO_PROCEDIMENTO, CO_SERVICO, CO_CLASSIFICACAO, DT_COMPETENCIA)

### rl_procedimento_habilitacao.txt (24 chars/linha)

Procedimento x Habilitacao — valida contra habilitacoes do CNES.

| Campo | Inicio | Fim | Tam | Tipo | PK/FK | Descricao |
|-------|--------|-----|-----|------|-------|-----------|
| CO_PROCEDIMENTO | 1 | 10 | 10 | CHAR | FK `tb_procedimento` | Codigo procedimento |
| CO_HABILITACAO | 11 | 14 | 4 | CHAR | FK `tb_habilitacao` | Codigo habilitacao |
| NU_GRUPO_HABILITACAO | 15 | 18 | 4 | CHAR | FK `tb_grupo_habilitacao` | Grupo habilitacao |
| DT_COMPETENCIA | 19 | 24 | 6 | CHAR | | Competencia AAAAMM |

**PK composta:** (CO_PROCEDIMENTO, CO_HABILITACAO, NU_GRUPO_HABILITACAO, DT_COMPETENCIA)

### rl_procedimento_cid.txt (21 chars/linha)

Procedimento x CID — CIDs permitidos/exigidos para BPA-I.

| Campo | Inicio | Fim | Tam | Tipo | PK/FK | Descricao |
|-------|--------|-----|-----|------|-------|-----------|
| CO_PROCEDIMENTO | 1 | 10 | 10 | CHAR | FK `tb_procedimento` | Codigo procedimento |
| CO_CID | 11 | 14 | 4 | CHAR | FK `tb_cid` | Codigo CID-10 |
| ST_PRINCIPAL | 15 | 15 | 1 | CHAR | | Principal? (`S`/`N`) |
| DT_COMPETENCIA | 16 | 21 | 6 | CHAR | | Competencia AAAAMM |

### rl_procedimento_compativel.txt (35 chars/linha)

Compatibilidade entre procedimentos na mesma competencia.

| Campo | Inicio | Fim | Tam | Tipo | PK/FK | Descricao |
|-------|--------|-----|-----|------|-------|-----------|
| CO_PROCEDIMENTO | 1 | 10 | 10 | CHAR | FK `tb_procedimento` | Procedimento principal |
| CO_REGISTRO_PRINCIPAL | 11 | 12 | 2 | CHAR | FK `tb_registro` | Registro principal |
| CO_PROCEDIMENTO_COMPATIVEL | 13 | 22 | 10 | CHAR | FK `tb_procedimento` | Procedimento compativel |
| CO_REGISTRO_COMPATIVEL | 23 | 24 | 2 | CHAR | FK `tb_registro` | Registro compativel |
| TP_COMPATIBILIDADE | 25 | 25 | 1 | CHAR | | Tipo compatibilidade |
| QT_PERMITIDA | 26 | 29 | 4 | INT | | Quantidade permitida |
| DT_COMPETENCIA | 30 | 35 | 6 | CHAR | | Competencia AAAAMM |

### rl_procedimento_incremento.txt (41 chars/linha)

Incrementos percentuais por habilitacao (afeta valor final).

| Campo | Inicio | Fim | Tam | Tipo | PK/FK | Descricao |
|-------|--------|-----|-----|------|-------|-----------|
| CO_PROCEDIMENTO | 1 | 10 | 10 | CHAR | FK `tb_procedimento` | Codigo procedimento |
| CO_HABILITACAO | 11 | 14 | 4 | CHAR | FK `tb_habilitacao` | Codigo habilitacao |
| VL_PERCENTUAL_SH | 15 | 21 | 7 | DEC(7,2) | | % incremento SH (ignorar) |
| VL_PERCENTUAL_SA | 22 | 28 | 7 | DEC(7,2) | | % incremento SA |
| VL_PERCENTUAL_SP | 29 | 35 | 7 | DEC(7,2) | | % incremento SP |
| DT_COMPETENCIA | 36 | 41 | 6 | CHAR | | Competencia AAAAMM |

---

## Layout detalhado — Tabelas de apoio importantes

### tb_habilitacao.txt (160 chars/linha)

| Campo | Inicio | Fim | Tam | Tipo | PK/FK | Descricao |
|-------|--------|-----|-----|------|-------|-----------|
| CO_HABILITACAO | 1 | 4 | 4 | CHAR | **PK** | Codigo habilitacao |
| NO_HABILITACAO | 5 | 154 | 150 | VARCHAR | | Nome habilitacao |
| DT_COMPETENCIA | 155 | 160 | 6 | CHAR | **PK** | Competencia AAAAMM |

### tb_grupo_habilitacao.txt (274 chars/linha)

| Campo | Inicio | Fim | Tam | Tipo | PK/FK | Descricao |
|-------|--------|-----|-----|------|-------|-----------|
| NU_GRUPO_HABILITACAO | 1 | 4 | 4 | CHAR | **PK** | Numero grupo habilitacao |
| NO_GRUPO_HABILITACAO | 5 | 24 | 20 | VARCHAR | | Nome |
| DS_GRUPO_HABILITACAO | 25 | 274 | 250 | VARCHAR | | Descricao |

### tb_servico.txt (129 chars/linha)

| Campo | Inicio | Fim | Tam | Tipo | PK/FK | Descricao |
|-------|--------|-----|-----|------|-------|-----------|
| CO_SERVICO | 1 | 3 | 3 | CHAR | **PK** | Codigo servico |
| NO_SERVICO | 4 | 123 | 120 | VARCHAR | | Nome servico |
| DT_COMPETENCIA | 124 | 129 | 6 | CHAR | **PK** | Competencia AAAAMM |

### tb_servico_classificacao.txt (162 chars/linha)

| Campo | Inicio | Fim | Tam | Tipo | PK/FK | Descricao |
|-------|--------|-----|-----|------|-------|-----------|
| CO_SERVICO | 1 | 3 | 3 | CHAR | FK `tb_servico` | Codigo servico |
| CO_CLASSIFICACAO | 4 | 6 | 3 | CHAR | **PK** | Codigo classificacao |
| NO_CLASSIFICACAO | 7 | 156 | 150 | VARCHAR | | Nome classificacao |
| DT_COMPETENCIA | 157 | 162 | 6 | CHAR | **PK** | Competencia AAAAMM |

### tb_cid.txt (111 chars/linha)

| Campo | Inicio | Fim | Tam | Tipo | PK/FK | Descricao |
|-------|--------|-----|-----|------|-------|-----------|
| CO_CID | 1 | 4 | 4 | CHAR | **PK** | Codigo CID-10 |
| NO_CID | 5 | 104 | 100 | VARCHAR | | Nome |
| TP_AGRAVO | 105 | 105 | 1 | CHAR | | Tipo de agravo |
| TP_SEXO | 106 | 106 | 1 | CHAR | | Sexo |
| TP_ESTADIO | 107 | 107 | 1 | CHAR | | Estadio |
| VL_CAMPOS_IRRADIADOS | 108 | 111 | 4 | INT | | Campos irradiados |

### tb_descricao.txt (4016 chars/linha)

| Campo | Inicio | Fim | Tam | Tipo | PK/FK | Descricao |
|-------|--------|-----|-----|------|-------|-----------|
| CO_PROCEDIMENTO | 1 | 10 | 10 | CHAR | FK `tb_procedimento` | Codigo procedimento |
| DS_PROCEDIMENTO | 11 | 4010 | 4000 | TEXT | | Descricao completa |
| DT_COMPETENCIA | 4011 | 4016 | 6 | CHAR | | Competencia AAAAMM |

---

## Diagrama de relacoes entre tabelas

```
tb_grupo (CO_GRUPO)
  └── tb_sub_grupo (CO_GRUPO, CO_SUB_GRUPO)
        └── tb_forma_organizacao (CO_GRUPO, CO_SUB_GRUPO, CO_FORMA_ORGANIZACAO)

tb_procedimento (CO_PROCEDIMENTO = GGSSFFPPPP)
  ├── CO_PROCEDIMENTO[1:2] ──────── FK → tb_grupo.CO_GRUPO
  ├── CO_PROCEDIMENTO[3:4] ──────── FK → tb_sub_grupo.CO_SUB_GRUPO
  ├── CO_PROCEDIMENTO[5:6] ──────── FK → tb_forma_organizacao.CO_FORMA_ORGANIZACAO
  ├── CO_FINANCIAMENTO ──────────── FK → tb_financiamento
  ├── CO_RUBRICA ────────────────── FK → tb_rubrica
  │
  ├── rl_procedimento_ocupacao ──── FK → tb_ocupacao (CBO)
  ├── rl_procedimento_registro ──── FK → tb_registro (BPA-C/BPA-I)
  ├── rl_procedimento_servico ───── FK → tb_servico + tb_servico_classificacao
  ├── rl_procedimento_habilitacao ─ FK → tb_habilitacao + tb_grupo_habilitacao
  ├── rl_procedimento_cid ──────── FK → tb_cid
  ├── rl_procedimento_compativel ── FK → tb_procedimento (auto-ref) + tb_registro
  ├── rl_procedimento_incremento ── FK → tb_habilitacao
  └── tb_descricao ──────────────── 1:1 descricao completa

rl_excecao_compatibilidade ──────── FK → tb_procedimento (3x) + tb_registro (2x)
```

---

## Recomendacao de persistencia no PostgreSQL

### Importar (essencial para faturamento BPA)

| Tabela | Colunas a persistir | Justificativa |
|--------|---------------------|---------------|
| `tb_procedimento` | **Todas exceto** QT_DIAS_PERMANENCIA, QT_TEMPO_PERMANENCIA, VL_SH | Campos hospitalares nao impactam BPA |
| `tb_financiamento` | Todas | Separar MAC/PAB na geracao do arquivo BPA |
| `tb_rubrica` | Todas | Detalhe orcamentario por financiamento |
| `tb_registro` | Todas | Decodificar BPA-C (02) vs BPA-I (01) |
| `tb_ocupacao` | Todas | Lookup de CBO para anti-glosa |
| `tb_grupo` | Todas | Hierarquia — dashboard e relatorios |
| `tb_sub_grupo` | Todas | Hierarquia |
| `tb_forma_organizacao` | Todas | Hierarquia |
| `rl_procedimento_ocupacao` | Todas | **Anti-glosa: procedimento x CBO** |
| `rl_procedimento_registro` | Todas | **Anti-glosa: instrumento correto** |
| `rl_procedimento_servico` | Todas | **Anti-glosa: servico CNES** |
| `rl_procedimento_habilitacao` | Todas | **Anti-glosa: habilitacao CNES** |
| `rl_procedimento_cid` | Todas | Validacao CID no BPA-I |
| `rl_procedimento_compativel` | Todas | Validacao compatibilidade |
| `rl_excecao_compatibilidade` | Todas | Complemento compatibilidade |

### Importar (apoio — validacao e classificacao)

| Tabela | Colunas a persistir | Justificativa |
|--------|---------------------|---------------|
| `tb_habilitacao` | Todas | Lookup para validacao habilitacao |
| `tb_grupo_habilitacao` | Todas | Agrupamento de habilitacoes |
| `tb_servico` | Todas | Lookup para validacao CNES |
| `tb_servico_classificacao` | Todas | Lookup classificacao servico |
| `tb_cid` | CO_CID, NO_CID, TP_SEXO | Lookup CID-10 (TP_AGRAVO, TP_ESTADIO e VL_CAMPOS_IRRADIADOS sao oncologicos — fora de escopo) |
| `tb_descricao` | Todas | Input para embeddings (pgvector) e classificacao Claude Haiku |
| `rl_procedimento_incremento` | CO_PROCEDIMENTO, CO_HABILITACAO, VL_PERCENTUAL_SA, VL_PERCENTUAL_SP | Apenas % ambulatorial — descartar VL_PERCENTUAL_SH |

### Nao importar (fora do escopo BPA ambulatorial)

| Tabela | Motivo |
|--------|--------|
| `tb_tipo_leito` | Hospitalar (AIH) |
| `rl_procedimento_leito` | Hospitalar (AIH) |
| `tb_sia_sih` | Mapeamento legado |
| `rl_procedimento_sia_sih` | Mapeamento legado |
| `tb_modalidade` / `rl_procedimento_modalidade` | Nao impacta validacao BPA |
| `tb_detalhe` / `tb_descricao_detalhe` / `rl_procedimento_detalhe` | Atributos complementares — nao usados em BPA |
| `tb_componente_rede` / `tb_rede_atencao` / `rl_procedimento_comp_rede` | Classificacao de rede — nao impacta faturamento |
| `tb_regra_condicionada` / `rl_procedimento_regra_cond` | Regras condicionadas — nao usadas em BPA |
| `tb_renases` / `rl_procedimento_renases` | RENASES — informativo, nao bloqueia |
| `tb_tuss` / `rl_procedimento_tuss` | Mapeamento TUSS — nao usado no SUS publico |

---

## Peculiaridades do formato

1. **Encoding ISO-8859-1:** Converter para UTF-8 na importacao. Nomes de procedimentos contem acentos e cedilhas.

2. **Valores monetarios sem separador decimal:** `VL_SA = 0000001250` significa R$ 12,50. Dividir por 100 ao importar.

3. **Percentuais sem separador decimal:** `VL_PERCENTUAL_SA = 0001500` significa 15,00%. Dividir por 100.

4. **Campos numericos com zero-fill:** `QT_MAXIMA_EXECUCAO = 0001` significa 1. Tratar como inteiro.

5. **CO_PROCEDIMENTO composto:** Os 10 digitos nao sao um numero — sao uma concatenacao `GG + SS + FF + PPPP`. Armazenar como CHAR(10), nunca como INTEGER.

6. **DT_COMPETENCIA como parte da PK:** Cada competencia gera um snapshot completo. Na importacao, filtrar pela competencia vigente e descartar anteriores (ou manter historico para auditoria).

7. **tb_ocupacao sem DT_COMPETENCIA:** Unica tabela de dominio que nao e versionada por competencia.

8. **Linhas sem terminador explicito:** Algumas implementacoes usam CRLF, outras apenas LF. O parser deve aceitar ambos.

9. **Campos texto com espacos a direita:** Nomes e descricoes sao preenchidos com espacos ate o tamanho maximo. Fazer RTRIM na importacao.

10. **Arquivo `.exe` vs `.zip`:** O download oficial e um `.exe` auto-extraivel, mas o conteudo e identico a um ZIP e pode ser extraido com `unzip` ou `7z`.

---

## Chaves compartilhadas com outras fontes

Estas chaves conectam o SIGTAP a outras bases de dados do SUS e serao usadas nas analises subsequentes (SCNES, FPO, BPA):

| Chave | Formato | Presente em | Uso no FaturaSUS |
|-------|---------|-------------|------------------|
| `CO_PROCEDIMENTO` | CHAR(10) | SIGTAP, BPA (.PA), FPO | Identificacao unica do procedimento |
| `CO_OCUPACAO` (CBO) | CHAR(6) | SIGTAP, SCNES (PF), BPA (.PA) | Validacao profissional x procedimento |
| `CO_SERVICO` | CHAR(3) | SIGTAP, SCNES (HB) | Validacao servico do estabelecimento |
| `CO_CLASSIFICACAO` | CHAR(3) | SIGTAP, SCNES (HB) | Validacao classificacao do servico |
| `CO_HABILITACAO` | CHAR(4) | SIGTAP, SCNES (HB) | Validacao habilitacao do estabelecimento |
| `CO_CID` | CHAR(4) | SIGTAP, BPA-I (.PA) | CID principal no registro individualizado |
| `CO_CNES` | CHAR(7) | SCNES, BPA (.PA), FPO | Identificacao do estabelecimento (nao esta no SIGTAP) |
| `CO_INE` | CHAR(10) | SCNES, BPA (.PA) | Equipe de saude da familia (nao esta no SIGTAP) |
| `CNS_PROFISSIONAL` | CHAR(15) | SCNES (PF), BPA-I (.PA) | Cartao Nacional de Saude do profissional |
| `CNS_PACIENTE` | CHAR(15) | CADSUS, BPA-I (.PA) | Cartao Nacional de Saude do paciente |
| `CO_FINANCIAMENTO` | CHAR(2) | SIGTAP | Separacao MAC/PAB no arquivo BPA |

---

## Fontes e referencias

| Fonte | URL |
|-------|-----|
| SIGTAP Portal Oficial | http://sigtap.datasus.gov.br |
| SIGTAP Download | http://sigtap.datasus.gov.br/tabela-unificada/app/download.jsp |
| Wiki SIGTAP | https://wiki.saude.gov.br/sigtap/index.php/ |
| ricmed/importSIGTAPTables (SQL) | https://github.com/ricmed/importSIGTAPTables |
| RicardoHerrero/SIGTAP-dataSUS (layouts) | https://github.com/RicardoHerrero/SIGTAP-dataSUS |
| rdsilva/SIGTAP (parser R) | https://github.com/rdsilva/SIGTAP |
