# Roteiro de Demo — Validação Anti-Glosa em Tempo Real

Documento para apresentação a secretários de saúde. Demonstra como o FaturaSUS impede glosas antes que o erro chegue ao SIA/SUS.

---

## Perfil do cenário

| Campo | Valor |
|---|---|
| **Profissional** | Vanessa Aparecida Gonçalves |
| **Cargo** | Técnica de Enfermagem |
| **CBO** | 322205 |
| **CNS** | 709005854322518 |
| **CNES** | 2139200 |
| **Estabelecimento** | PSF Vila Nova — Três Pontas/MG |
| **Tipo de unidade** | 05 — PSF/Centro de Saúde |
| **Competência** | Março/2026 |

> Os dados do profissional e do estabelecimento são reais — extraídos do SCNES/DATASUS. A Vanessa existe no cadastro federal. O PSF existe. Apenas o fluxo de captura (câmera + áudio) é demonstrado em ambiente de homologação.

---

## Parte 1 — Procedimentos que passam

**Narrativa sugerida:**
> "Vou ditar três procedimentos comuns de uma UBS. O sistema valida cada um em tempo real contra a tabela SIGTAP — CBO da profissional, habilitações do CNES e instrumento de registro."

### 1. Aferição de Pressão Arterial

- **Código SIGTAP:** `0301100039`
- **Áudio a ditar:** *"aferição de pressão arterial"*
- **Resultado esperado:** aprovado — sem bloqueios, sem alertas
- **Por que passa:** CBO 322205 está na lista de ocupações autorizadas em `sigtap_rl_proc_ocupacao`; o procedimento não exige habilitação especial do CNES.

### 2. Glicemia Capilar

- **Código SIGTAP:** `0214010015`
- **Áudio a ditar:** *"glicemia capilar"*
- **Resultado esperado:** aprovado
- **Por que passa:** idem — CBO 322205 autorizado; sem exigência de habilitação.

### 3. Coleta de Material para Exame Laboratorial

- **Código SIGTAP:** `0201020041`
- **Áudio a ditar:** *"coleta de material para exame laboratorial"* ou *"coleta de sangue"*
- **Resultado esperado:** aprovado
- **Por que passa:** idem.

---

## Parte 2 — Procedimentos que bloqueiam

**Narrativa sugerida (antes de mostrar):**
> "Agora vou tentar registrar dois procedimentos que parecem rotineiros mas estão fora do escopo desta profissional ou deste estabelecimento. O sistema barra antes de salvar — o arquivo BPA que sairia para o SIA já estaria errado."

### Bloqueio B1 — CBO incompatível

- **Procedimento:** Consulta Médica em Atenção Primária
- **Código SIGTAP:** `0301010064`
- **Áudio a ditar:** *"consulta médica"*
- **Resultado esperado:** **BLOQUEADO**
- **Código do bloqueio:** `CBO_INCOMPATIVEL`
- **Mensagem exibida:** "CBO do profissional não autorizado para este procedimento."
- **Fundamento normativo:** Portaria GM/MS nº 321/2007 → Consolidação GM/MS nº 1/2017, Anexo XVII. O SIGTAP define a lista de CBOs autorizados para cada procedimento; CBO 322205 (técnico de enfermagem) não consta na lista de `0301010064`, que exige CBO médico.

**Narrativa após o bloqueio:**
> "Esse erro acontece hoje manualmente — o faturista precisa conferir CBO por CBO no SIGTAP. Com o FaturaSUS, ele é barrado no momento da fala, antes de qualquer digitação."

---

### Bloqueio B2 — Habilitação ausente no CNES

- **Procedimento:** Biópsia de Corpo Vertebral a Céu Aberto
- **Código SIGTAP:** `0201010127`
- **Áudio a ditar:** *"biópsia de coluna vertebral"* ou *"biópsia de corpo vertebral"*
- **Resultado esperado:** **BLOQUEADO**
- **Código do bloqueio:** `HABILITACAO_AUSENTE`
- **Mensagem exibida:** "Estabelecimento não possui a habilitação exigida para este procedimento."
- **Fundamento normativo:** Portaria SAS/MS nº 1.229/2012; Consolidação SAES/MS nº 1/2022, Art. 412. O procedimento exige habilitação de cirurgia de coluna (códigos 1706–1713). O PSF Vila Nova não possui essa habilitação — confirmado no CNES.

**Narrativa após o bloqueio:**
> "Esse bloqueio vem do próprio cadastro do estabelecimento no CNES. O PSF nunca seria pago por esse procedimento — o SIA rejeitaria na importação. O FaturaSUS cruza isso automaticamente antes de registrar."

---

## Observações técnicas para o apresentador

- O banco usa dados reais do SIGTAP (competência 202603) e do SCNES (202602) — releases diferentes são normais, ambos extraídos da mesma fonte DATASUS.
- O CNES 2139200 tem 10 habilitações reais cadastradas (oncologia, CAPS, trauma ortopédico), mas nenhuma de cirurgia de coluna — por isso o bloqueio B2 é genuíno, não simulado.
- Se o sistema de busca semântica não retornar o procedimento exato nos exemplos acima, ditar o nome mais próximo e confirmar na tela de desambiguação.

---

## Referências

- [docs/anti_glosa_fontes_normativas.md](anti_glosa_fontes_normativas.md) — arcabouço normativo completo das 8 regras
- [docs/prompt_passo6_anti_glosa.md](prompt_passo6_anti_glosa.md) — schema `ResultadoValidacao` e contrato de API
- [roadmap.md](../roadmap.md) — passo 6b

---

*FaturaSUS — DataBrasil | Roteiro demo passo 6b | Abril/2026*
