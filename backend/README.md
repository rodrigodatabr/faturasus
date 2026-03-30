# FaturaSUS — Backend

API REST para faturamento ambulatorial SUS (BPA-C e BPA-I).

## Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Variáveis de ambiente

Copie `.env.example` para `.env` e preencha:

```
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/faturasus
```

## Rodar

```bash
uvicorn app.main:app --reload
```

## Health check

```
GET /health → {"status": "ok", "db": true}
```

## Migrations (Alembic)

```bash
alembic upgrade head      # Aplicar migrations
alembic revision --autogenerate -m "descricao"  # Gerar nova migration
```
