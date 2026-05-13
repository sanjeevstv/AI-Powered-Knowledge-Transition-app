# KT Platform API

FastAPI service for sessions, AI processing, RAG chat, and dashboard metrics.

## Local setup

```bash
cd apps/api
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .
cp ../../.env.example ../../.env   # optional: set OPENAI_API_KEY
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

OpenAPI docs: http://localhost:8000/docs
