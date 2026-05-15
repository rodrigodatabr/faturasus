# Prompt de desenvolvimento — Diagnóstico de Subregistro Municipal

> **Contexto para o desenvolvedor:**
> Este módulo não faz parte do fluxo principal do FaturaSUS (registro de produção ambulatorial).
> É um módulo de diagnóstico/prospecção: dado um município, estima quanto de produção MAC
> está sendo subregistrada comparando dois anos completos de produção real do DATASUS.
> O resultado alimentará uma feature futura no dashboard gerencial ("Estimativa de ROI")
> que mostrará ao secretário de saúde o potencial de receita federal não capturada.
>
> A análise-piloto foi feita para Naviraí/MS (2023 vs. 2025) usando valores médios do SIGTAP
> como proxy — metodologia descartada em favor desta abordagem (valores reais por procedimento
> via PA do FTP DATASUS, que elimina o problema de média vs. mediana do catálogo SIGTAP).

---

## Objetivo

Este documento cobre os três sub-itens do passo 7 do roadmap.

### 7a — Mapeamento MAC/FAEC no banco

A classificação por financiamento vem de `sigtap_rl_proc_financiamento`, **não** dos arquivos PA.
O join correto:

```sql
SELECT p.co_procedimento, p.no_procedimento, f.co_financiamento, f.no_financiamento
FROM sigtap_procedimentos p
JOIN sigtap_rl_proc_financiamento rf USING (co_procedimento)
JOIN sigtap_financiamento f USING (co_financiamento)
WHERE rf.dt_competencia = (SELECT MAX(dt_competencia) FROM sigtap_rl_proc_financiamento)
  AND f.co_financiamento IN ('04', '06')  -- FAEC e MAC
```

Isso produz a lista canônica de quais procedimentos são MAC/FAEC antes de olhar qualquer arquivo PA.
Um procedimento pode ter zero registros num dado ano no PA e ainda assim ser MAC — a fonte do
SIGTAP é a referência, não o que apareceu na produção histórica.

### 7b e 7c — Script de ingestão e relatório

Construir um script Python standalone (`backend/app/ingest/sia_producao.py`) que:

1. Baixa os arquivos de Produção Ambulatorial (PA) do FTP do DATASUS para um município e dois anos
2. Filtra por `PA_TPFIN IN ('04', '06')` e `PA_MUNPCN = municipio`
3. Agrega por `(PA_PROC_ID, ano)` — soma `PA_QTDAPR`, soma `PA_VALAPR`
4. Cruza com o mapeamento 7a (via banco) para validar e enriquecer com nome e financiamento
5. Aplica lógica de subregistro (ver seção abaixo)
6. Gera CSV + sumário no stdout
7. Limpa arquivos `.dbc` temporários

---

## Decisões de arquitetura já tomadas

### Horizonte temporal: anos completos (não meses)
Municípios de pequeno porte (< 100k hab.) têm volume mensal baixo em vários subgrupos —
comparar meses individuais gera ruído estatístico alto. Usar 12 meses completos de cada período
garante significância mesmo para subgrupos com poucos procedimentos/mês.

Parâmetros do script: `--municipio 500570 --ano-ref 2023 --ano-atual 2025`

### Fonte dos dados: FTP DATASUS direto (não pysus como dependência principal)
O FTP do DATASUS (`ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Dados/`) contém
arquivos `PAMS{AA}{MM}.dbc` (AM = Mato Grosso do Sul, por exemplo) com toda a produção
ambulatorial do estado por mês.

**Não usar pysus como dependência obrigatória** — a biblioteca (AlertaDengue/PySUS) é mantida
por terceiros (Fiocruz/FGV) com cadência lenta (~22 commits/ano) e risco de quebra em mudanças
no FTP. Usar apenas `blast-dbf` ou `dbfread` para conversão `.dbc → DataFrame`, isolando
a dependência em uma função `_dbc_to_df(path)` trocável. Ver como o CNES/HB foi tratado
em `backend/app/ingest/cnes.py` (mesma estratégia: `.dbc` local sem pysus).

### Campos relevantes do arquivo PA (produção ambulatorial)
Os arquivos `.dbc` do SIA/PA têm layout fixo. Campos necessários:

| Campo | Descrição |
|---|---|
| `PA_CODUNI` | CNES do estabelecimento |
| `PA_MUNPCN` | Município de residência do paciente (IBGE 6 dígitos) — **não** `PA_MUNRES` |
| `PA_PROC_ID` | Código do procedimento (10 dígitos) |
| `PA_QTDAPR` | Quantidade aprovada |
| `PA_VALAPR` | Valor aprovado (já em reais — diferente do SIGTAP que usa centavos) |
| `PA_TPFIN` | Financiamento ('06' = MAC, '04' = FAEC) — **não** `PA_FINANC` |
| `PA_CMP` | Competência (AAMM) |

> **Atenção (verificado no arquivo real PAMS2301.dbc):** os campos `PA_MUNRES` e `PA_FINANC`
> mencionados na documentação DATASUS/PySUS **não existem** no layout real dos arquivos PA de MS.
> Os campos corretos são `PA_MUNPCN` (município de residência do paciente) e `PA_TPFIN` (tipo de
> financiamento). Validar para outros estados antes de assumir que são universais.

**Filtrar por `PA_MUNPCN`** (município de residência do paciente), não `PA_UFMUN` (município do
prestador). Isso reflete a produção do município independente de onde o atendimento foi prestado.

### Armazenamento: tabela temporária, não persistente
Os dados de produção PA **não devem ser persistidos permanentemente** no banco principal.
São volumosos (um mês de PA de MS tem ~500k linhas) e só são necessários até a geração
do relatório de diagnóstico. Estratégia:

```sql
CREATE TABLE IF NOT EXISTS diagnostico_subregistro_raw (
    municipio_ibge  CHAR(6),
    co_procedimento CHAR(10),
    ano             SMALLINT,
    qt_total        INTEGER,
    vl_total_aprovado NUMERIC(14,2),
    created_at      TIMESTAMP DEFAULT NOW()
);
-- Ao gerar o relatório, deletar: DELETE FROM diagnostico_subregistro_raw WHERE municipio_ibge = ?
```

Alternativamente, usar tabela temporária de sessão (`CREATE TEMP TABLE`) se o script rodar
em uma única conexão. Mais limpo, sem necessidade de limpeza manual.

### Lógica de estimativa de subregistro

```
ratio = qt_ano_atual / qt_ano_ref

se qt_ano_ref > 0 e qt_ano_atual = 0  → "procedimento desapareceu" — sinalizar separadamente (caso mais grave)
se ratio < 0.50                        → suspeita de subregistro → usar qt_ano_ref como estimativa real
caso contrário                         → sem subregistro aparente → usar qt_ano_atual
```

**Valor unitário para o gap:** usar o valor unitário do SIGTAP (`vl_sh + vl_sa + vl_sp + vl_ob + vl_ho`),
não `PA_VALAPR / PA_QTDAPR`. O valor aprovado no PA reflete o que o SIA pagou após possíveis cortes
de quantidade — usar como base do gap distorceria o potencial de receita para baixo.

O valor do PA (`PA_VALAPR / PA_QTDAPR`) deve aparecer no CSV apenas como coluna informativa
("valor médio aprovado pelo SIA"), para que o gestor possa comparar com o valor SIGTAP e entender
eventuais diferenças.

**Categorias no relatório:**
1. `desapareceu` — qt_ano_ref > 0, qt_ano_atual = 0
2. `subregistro` — ratio < 0.50 (e qt_ano_atual > 0)
3. `estável` — ratio ≥ 0.50

### Separação MAC vs. FAEC no relatório
- **MAC (fin=06):** impacta diretamente o argumento de pleito de aumento de teto
- **FAEC (fin=04):** pago por produção, fora do teto — reportar separadamente como "receita adicional não capturada"

---

## Interface do script

```bash
cd backend
PYTHONPATH=. python -m app.ingest.sia_producao \
    --municipio 500570 \        # IBGE 6 dígitos
    --uf MS \                   # UF para localizar os arquivos no FTP
    --ano-ref 2023 \            # Ano de referência (alta produção esperada)
    --ano-atual 2025 \          # Ano de comparação
    --output diagnostico_navira_2023_2025.csv
```

O script deve:
1. Baixar 24 arquivos `.dbc` (12 meses × 2 anos) para um diretório temporário
2. Converter cada `.dbc` para DataFrame, filtrar por `PA_MUNRES` e `PA_FINANC IN ('04','06')`
3. Agregar por `(PA_PROC_ID, ano)` → soma de `PA_QTDAPR` e média ponderada de `PA_VALAPR/PA_QTDAPR`
4. Cruzar com `sigtap_procedimentos` (competência mais recente) para validar e enriquecer com nome
5. Aplicar lógica de subregistro (threshold 50%)
6. Gerar CSV + sumário no stdout (total MAC registrado, estimado, gap; total FAEC idem)
7. Limpar arquivos `.dbc` temporários

---

## Estrutura esperada do output CSV

```
co_procedimento; no_procedimento; co_financiamento; subgrupo; categoria;
qt_ano_ref; qt_ano_atual; ratio;
vl_unitario_sigtap; vl_unitario_aprovado_pa;
vl_producao_registrada; vl_producao_estimada;
vol_subregistro; vl_subregistro
```

`categoria` = `desapareceu` | `subregistro` | `estável`

`vl_unitario_sigtap` = valor do catálogo SIGTAP (base do gap estimado)
`vl_unitario_aprovado_pa` = `PA_VALAPR / PA_QTDAPR` do ano de referência (informativo)

---

## 7d — Frontend e entrega do resultado

### Onde fica o frontend
Página pública no **site da DataBrasil** — não no FaturaSUS. Qualquer secretário de saúde
acessa sem cadastro ou contrato. O objetivo é geração de leads: o município vê o diagnóstico
antes de fechar contrato, tornando o ROI do FaturaSUS concreto e auditável.

### Como o frontend chama o backend
O site da DataBrasil faz `POST /diagnostico/subregistro` no backend do FaturaSUS (Railway).
O banco PostgreSQL nunca é exposto diretamente — toda a lógica fica no backend FaturaSUS,
acessível via API HTTP normal. É a mesma arquitetura de qualquer integração entre dois projetos.

### Endpoint backend

```
POST /diagnostico/subregistro
Body: { municipio_ibge, uf, ano_ref, ano_atual, email }
Response: { job_id, mensagem: "Relatório será enviado para {email} em alguns minutos" }
```

O job roda em background (estimativa: 3–10 min, limitado pela velocidade do FTP DATASUS).
**Não usar polling** — o usuário não vai ficar com a aba aberta. Ao concluir, o backend
envia o CSV por email com link de download.

### Formulário (página DataBrasil)
Campos: município (autocomplete por nome), UF, ano de referência, email.
Após envio: mensagem de confirmação com estimativa de tempo. Sem área de resultados inline.

### No futuro — feature de ROI dentro do FaturaSUS
Quando o município já for cliente, o mesmo endpoint alimentará uma página de diagnóstico
no menu lateral do FaturaSUS (fora do fluxo principal de registro):
- Tabela por subgrupo com gap de subregistro
- Resumo executivo: "Produção MAC registrada: R$ X | Estimativa real: R$ Y | Gap: R$ Z"
- Comparação com o teto MAC vigente (via SISMAC ou valor informado manualmente)
- Botão "Exportar relatório" (PDF ou XLSX)

---

## Referências

- `backend/app/ingest/cnes.py` — padrão de ingestão `.dbc` já usado no projeto (mesma estratégia para PA)
- [PySUS SIA docs](https://pysus.readthedocs.io/pt/stable/databases/SIA.html) — referência de campos PA
- [FTP DATASUS SIASUS](ftp://ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Dados/) — fonte dos arquivos
