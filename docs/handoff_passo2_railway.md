# Handoff — Passo 2: finalizar deploy no Railway

## Estado atual (2026-03-30)

### O que está feito ✅
- Embeddings: 4.980 procedimentos indexados no banco Railway (competência 202603)
- Migration `0002_ivfflat_embeddings` aplicada — Railway está na `head`
- `backend/app/config.py` corrigido com `extra = "ignore"` (aceita `DATABASE_PUBLIC_URL` no `.env`)
- Backend FastAPI deployado no Railway via `backend/Procfile` — **ACTIVE, Deployment successful**

### O que falta ⚠️

O serviço `faturasus` no Railway está rodando o **FastAPI** mas marcado como **"Unexposed service"** — sem domínio público gerado. A URL histórica `faturasus-production.up.railway.app` era do frontend estático (deployado quando o React estava na raiz do repo, antes de mover para `frontend/`).

**Decisão arquitetural: um serviço no Railway** ✅

FastAPI serve `frontend/dist/` como static files via `StaticFiles` do Starlette. Um domínio só, padrão do stack (outro projeto da DataBrasil segue o mesmo modelo no Railway).

### Passos

1. Gerar domínio no Railway: serviço `faturasus` → Settings → Generate Domain → copiar URL
2. Adicionar ao `backend/app/main.py` a montagem do `frontend/dist/` como `StaticFiles`
3. Criar `railway.json` (ou `nixpacks.toml`) com build command: `cd frontend && npm install && npm run build`
4. Ajustar o `Procfile` se necessário (uvicorn já está correto)
5. Testar `/docs` e o frontend no mesmo domínio

### Testar o backend (quando tiver domínio)

`GET https://<url-backend>/docs` deve mostrar o Swagger com os endpoints:
- `GET /health`
- `POST /transcricao`
- `GET /busca/procedimentos`

Casos de teste para `/busca/procedimentos`:

| q | competencia | cbo | Esperado no top-3 |
|---|---|---|---|
| `consulta medica atencao basica` | `202603` | — | CONSULTA MÉDICA EM ATENÇÃO BÁSICA |
| `curativo complexo paciente diabetico` | `202603` | `225125` | CURATIVO ESPECIAL ou CURATIVO GRAU II (cbo_compativel: true) |
| `ultrassonografia obstetrica` | `202603` | — | ULTRASSONOGRAFIA OBSTETRICA |

## Arquivos relevantes

- `backend/app/main.py` — FastAPI app (ponto de entrada para adicionar StaticFiles na Opção A)
- `backend/app/ingest/embeddings.py` — script de indexação (idempotente)
- `backend/app/routers/busca.py` — endpoint de busca semântica
- `backend/alembic/versions/0002_ivfflat_embeddings.py` — migration IVFFlat (já aplicada)
- `frontend/src/App.jsx` — todo o protótipo; dados mockados inline (substituir por API calls)

## Próximo passo após resolver o deploy

Passo 3 (Whisper) e Passo 4 (CADSUS mock) podem avançar em paralelo — ambos independentes do deploy.
O passo 5 (pipeline Claude Haiku) depende dos dois anteriores.
