# Bug: validação anti-glosa sempre aprovando em produção (pós-deploy 06/04/2026)

## Sintoma

Após os dois últimos deploys (commits `f62c492` e `b134c03`), a classificação voltou a funcionar,
mas **nenhum bloqueio anti-glosa está sendo disparado**. Todo registro confirma com HTTP 201 e
"aprovado: true", mesmo para procedimentos que deveriam bloquear por CBO incompatível ou
habilitação ausente.

---

## Contexto dos últimos commits relevantes

### `69ef927` — corrige sessão e testes do passo 6b (15h11 de 06/04)
Esse commit validou anti-glosa funcionando:
- `registros.py`: substituiu `async with session.begin()` por `commit/rollback` explícito (DEC-012)
- `seed_profissionais.py`: reescreveu o seed completo, mudou profissional demo para
  Vanessa Gonçalves (CBO `322205`, CNES `2139200`)
- Resultado declarado: 10/10 pytest + 2× bloqueios confirmados na API ao vivo

### `f62c492` — corrige identidade profissional e competência dinâmica (20h12 de 06/04)
- Frontend: `DEMO_PROFISSIONAL.cbo` mudou de `225125` → `322205`, `cnes` de `0000001` → `2139200`
- `DEMO_COMPETENCIA = "202603"` substituído por `competenciaAtual()` → retorna `"202604"` agora

**Este commit é o principal suspeito.** A competência enviada ao `/registros` mudou de
`202603` para `202604`. As validações anti-glosa B1–B4 filtram por `dt_competencia = :competencia`
nas tabelas SIGTAP. **Se não há dados SIGTAP para competência `202604` no Railway**, as queries
retornam zero resultados e todas as checagens passam silenciosamente:

- `_check_b1_cbo`: `COUNT(*) = 0` → interpreta como "procedimento sem restrição de CBO" → `[]`
- `_check_b2_habilitacao`: `SELECT 1 ... WHERE dt_competencia = '202604'` → retorna nada → `[]`
- `_check_b3_servico`: idem → `[]`
- `_check_b4_instrumento`: idem → `[]`

---

## Hipótese principal

As tabelas SIGTAP no Railway (`sigtap_rl_proc_ocupacao`, `sigtap_rl_proc_habilitacao`,
`sigtap_rl_proc_servico`, `sigtap_rl_proc_registro`) têm dados apenas para **`202603`**.
Quando `competencia = '202604'` é passado às queries anti-glosa, todas retornam vazio e
todas as regras passam sem bloquear.

**Verificar no Railway:**
```sql
SELECT DISTINCT dt_competencia FROM sigtap_rl_proc_ocupacao;
SELECT DISTINCT dt_competencia FROM sigtap_rl_proc_habilitacao;
SELECT DISTINCT dt_competencia FROM sigtap_rl_proc_servico;
SELECT DISTINCT dt_competencia FROM sigtap_rl_proc_registro;
```
Esperado: apenas `202603`. Se confirmado, o anti-glosa está "passando no vácuo".

---

## Hipótese secundária

O mesmo problema da DEC-014 (classificador) se aplica ao anti-glosa: o parâmetro `competencia`
recebido pelo `/registros` não deveria ser usado como filtro direto nas tabelas SIGTAP — deveria
usar a competência mais recente disponível nessas tabelas (igual ao que foi feito no classificador
em `b134c03`).

---

## Solução proposta

Aplicar o mesmo padrão da DEC-014 ao `anti_glosa.py`:

1. No início de `validar_registro()`, consultar `MAX(dt_competencia)` de uma das tabelas SIGTAP
   (ex: `sigtap_rl_proc_ocupacao`) e usar esse valor em todas as checagens B1–B4.
2. Manter o `ctx.competencia` original para B5 (retroatividade) e para os alertas A1–A2, onde
   a competência do registro real importa.
3. Registrar como DEC-015.

**Atenção:** resolver isso não é apenas "usar MAX" cegamente — é necessário entender se alguma
regra anti-glosa genuinamente depende da competência correta vs. a mais recente disponível.
B1–B4 dependem de quais procedimentos/CBOs/habilitações estão vigentes: usar a competência
mais recente disponível é correto porque o SIGTAP não sofre mudanças drásticas mês a mês e
é melhor do que não validar nada.

---

## Arquivos a ler

- `backend/app/services/anti_glosa.py` — todas as checagens B1–B4 usam `ctx.competencia`
  como filtro em `dt_competencia`; o fix vai aqui
- `backend/app/routers/registros.py` — monta o `RegistroContext` com `competencia=body.competencia`
- `frontend/src/App.jsx` — `handleConfirm` envia `competencia: competenciaAtual()` ao `/registros`
- `backend/app/services/classificacao.py` — referência: já implementou MAX fallback em
  `_buscar_candidatos_hybrid` (commit `b134c03`)

---

## Decisão de design a registrar (DEC-015 candidata)

As checagens B1–B4 do anti-glosa (CBO, habilitação, serviço, instrumento) devem usar a
competência SIGTAP mais recente disponível no banco, não a competência do registro. Só B5
(retroatividade) e os alertas A1–A2 (duplicidade, FPO) usam a competência real do registro —
pois dependem de dados operacionais (`registros_producao`, `fpo_programacao`) que existem na
competência correta.
