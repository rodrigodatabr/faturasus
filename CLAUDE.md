# FaturaSUS

> Decisões não óbvias de produto e arquitetura: ver [`DECISIONS.md`](DECISIONS.md).

Assistente PWA de faturamento ambulatorial SUS — toda a produção ambulatorial (BPA-C e BPA-I), abrangendo MAC e Atenção Básica/PAB, com separação automática por financiamento na exportação. Fora de escopo: AIH e APAC. Profissional escaneia cartão SUS, grava áudio descrevendo o procedimento, e o sistema classifica via SIGTAP, valida contra glosas e gera o arquivo BPA para o SIA/SUS.

## Stack

| Camada | Tecnologia |
|---|---|
| Frontend | React 19 + Vite 8 (PWA) |
| Backend | Python FastAPI — Railway |
| Banco | PostgreSQL + pgvector — Railway |
| Transcrição | OpenAI Whisper API |
| Classificação SIGTAP | Claude Haiku (Anthropic API) |
| Embeddings | OpenAI `text-embedding-3-small` |
| Identificação paciente | API CADSUS v5 (SOAP/RNDS) |

## Estrutura de arquivos

```
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── eslint.config.js
│   ├── public/
│   │   ├── favicon.svg
│   │   └── icons.svg
│   └── src/
│       ├── main.jsx          # Entry point
│       ├── App.jsx            # Componente único — toda a UI do protótipo
│       ├── index.css          # Estilos globais (Vite scaffold)
│       └── assets/
├── backend/
│   ├── app/
│   │   ├── main.py        # FastAPI app, lifespan, CORS
│   │   ├── config.py      # Settings via pydantic-settings
│   │   ├── db.py          # Engine async + sessionmaker (asyncpg)
│   │   ├── routers/
│   │   │   ├── health.py      # GET /health
│   │   │   ├── transcricao.py # POST /transcricao (Whisper)
│   │   │   ├── busca.py       # GET /busca/procedimentos (pgvector)
│   │   │   ├── classificacao.py # POST /classificar (Haiku)
│   │   │   └── registros.py   # POST /registros (anti-glosa + persistência)
│   │   ├── models/
│   │   │   ├── __init__.py    # Re-exporta todos os models (Alembic + main.py)
│   │   │   ├── sigtap.py      # 20 tabelas SIGTAP
│   │   │   ├── cnes.py        # 4 tabelas CNES
│   │   │   └── operacional.py # 4 tabelas operacionais (profissionais, registros, etc.)
│   │   ├── seeds/
│   │   │   └── seed_profissionais.py  # profissionais fictícios + CNES demo
│   │   ├── ingest/
│   │   │   ├── sigtap.py              # Ingestão BDSIA → 20 tabelas sigtap_* (UPSERT, lotes de 500)
│   │   │   ├── cnes.py                # Ingestão SCNES → 4 tabelas cnes_* (filtro --municipios por IBGE 6 dígitos)
│   │   │   ├── embeddings.py          # Indexação SIGTAP → embeddings_procedimentos (OpenAI, lotes de 100)
│   │   │   └── test_sigtap_dry_run.py # Valida layouts localmente sem banco
│   │   ├── schemas/       # Pydantic schemas (vazio por ora)
│   │   └── services/
│   │       ├── classificacao.py  # Hybrid search (pgvector + substring) → Claude Haiku
│   │       └── anti_glosa.py     # 8 verificações anti-glosa em asyncio.gather
│   ├── alembic/
│   │   ├── env.py         # Migrations async
│   │   └── versions/
│   ├── alembic.ini
│   ├── requirements.txt
│   ├── .env.example
│   └── Procfile
├── docs/
│   ├── layout_sigtap.md   # Layout real do BDSIA (41 tabelas, 22 relevantes para BPA)
│   └── layout_scnes.md    # Layout real do SCNES (ST, PF, HB, SR) + mapeamento arquivo→tabela real
└── prd_faturasus.md       # PRD completo do produto
```

## Deploy

O protótipo frontend está hospedado na Railway:
**https://faturasus-production.up.railway.app/**

## O que já está implementado (protótipo interativo)

- Tela de captura mobile-first estilo chat, com frame de celular em desktop
- Scan de cartão SUS com câmera real (getUserMedia) + flash de sucesso
- Fallbacks: digitar CPF ou CNS manualmente com máscara e validação de tamanho
- Dados mockados de paciente (CADSUS) e procedimento (SIGTAP)
- Simulação de gravação de áudio com waveform animado
- Fluxo de desambiguação (ex: com/sem biópsia) via quick-reply buttons
- Tela de validação anti-glosa (CBO, CNES) e resumo do registro
- Confirmação e mini-dashboard com stats do dia (registros, pendências, tempo médio)
- Responsivo: 100dvh sem bordas no mobile, frame 375×780 em desktop

## O que falta construir (ver PRD §5 para escopo completo)

- ~~**Backend FastAPI**~~ — scaffold criado (sem auth/JWT ainda)
- ~~**Layouts SIGTAP + SCNES**~~ — mapeados em `docs/`; ver `roadmap.md` passo 0c antes de criar o schema
- ~~**Banco PostgreSQL**~~ — 28 tabelas criadas (SIGTAP + CNES + operacional); migration aplicada no Railway; pgvector ativo
- ~~**Script de ingestão SIGTAP**~~ — `app/ingest/sigtap.py`; executado contra Railway (competência 202603): 20/20 tabelas OK, 4980 procedimentos, 194720 rl_proc_ocupacao
- ~~**Script de ingestão SCNES**~~ — `app/ingest/cnes.py`; filtro `--municipios` por código IBGE; ingerido para Naviraí-MS, Três Pontas-MG, Esteio-RS (903 est., 5.399 prof., 878 serv., 39 hab.)
- ~~**Embeddings SIGTAP + busca semântica**~~ — `app/ingest/embeddings.py`; 4.980 procedimentos indexados localmente; migration `0002_ivfflat_embeddings` (IVFFlat); endpoint `GET /busca/procedimentos`. **Pendente no Railway:** rodar indexação e migration apontando para produção.
- **Integração CADSUS v5** — SOAP real via barramento RNDS (sem cache persistente de pacientes; apenas cache volátil de sessão)
- ~~**Pipeline de registro**~~ — Whisper → pgvector → Claude Haiku → validação anti-glosa → `POST /registros` persistindo em `registros_producao`
- **Fontes de dados externas** — SIGTAP/BDSIA (cron diário), SCNES PF+HB (upload mensal), FPO (manual). Ver PRD §3.3
- **Dashboard gerencial** — KPIs, drill-down, correção inline pelo faturista
- **Geração BPA** — exportação `.PA` no layout magnético DATASUS com separação automática PAB/MAC
- **LGPD** — hash SHA-256 do CNS, descarte de áudio, criptografia em repouso

## Convenções de código

### Frontend
- React funcional com hooks — sem classes
- JSX inline styles (não CSS modules) — padrão do protótipo atual
- Constantes de cor no topo do arquivo (BLUE, GREEN, etc.)
- Componentes no mesmo arquivo enquanto couberem; extrair quando > ~100 linhas
- Sem TypeScript por enquanto (JSX puro)

### Backend
- Python 3.12+, FastAPI + SQLAlchemy 2.x async
- Async-first (asyncpg, não psycopg)
- Identificadores em inglês; comentários/docstrings em português

### Geral
- Nomes de variáveis e funções em inglês; textos de UI em português (pt-BR)

## Comandos

### Frontend
```bash
cd frontend
npm install        # Instalar dependências
npm run dev        # Dev server (Vite) — http://localhost:5173
npm run build      # Build de produção
npm run preview    # Preview do build
npm run lint       # ESLint
```

### Backend
```bash
cd backend
pip install -r requirements.txt          # Instalar dependências
uvicorn app.main:app --reload            # Dev server — http://localhost:8000
alembic upgrade head                     # Aplicar migrations
alembic revision --autogenerate -m "x"   # Gerar migration
```

## Variáveis de ambiente

### Backend (ativas)
```
DATABASE_URL=             # PostgreSQL com asyncpg (obrigatória)
CORS_ORIGINS=             # Lista JSON de origens (opcional)
OPENAI_API_KEY=           # Whisper (transcrição) + embeddings
ANTHROPIC_API_KEY=        # Claude Haiku (classificação SIGTAP) — opcional até o passo 5
```

> **Nota de ambiente:** para rodar migrations/seeds localmente contra o Railway, usar a `DATABASE_PUBLIC_URL` (host `gondola.proxy.rlwy.net:29300`) com o IP direto `66.33.22.247:29300` caso o DNS local não resolva `*.rlwy.net`. O serviço `faturasus` no Railway usa a URL interna (`postgres.railway.internal:5432`).

### Futuras
```
CADSUS_CERTIFICATE=       # Certificado digital p/ barramento RNDS
CADSUS_ENDPOINT=          # URL do serviço CADSUS v5
JWT_SECRET=               # Auth
```
