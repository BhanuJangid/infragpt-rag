# InfraGPT

RAG chatbot for infra ops. FastAPI retrieves runbooks, the model can call **mock** VMware vCenter and Nutanix Prism tools, and a React UI chats against the API.

No live hypervisor credentials are used. Inventory is a JSON fixture.

## Stack

- FastAPI + OpenAPI (`/docs`)
- LangChain text splitters + TF-IDF retrieval (runs without an API key)
- Optional OpenAI function calling when `OPENAI_API_KEY` is set
- pgvector in Docker for a production-shaped vector store
- React (Vite) frontend
- Pytest + GitHub Actions

## Run locally

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt   # API + tests
# pip install -r requirements.txt     # also LangChain + OpenAI client
PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Swagger is at http://localhost:8000/docs.

Without an OpenAI key the API uses a deterministic mock LLM that still retrieves runbooks and calls tools.

## Docker

```bash
docker compose up --build
```

Postgres starts with the `vector` extension (`backend/data/init.sql`). The default chat path does not require it.

## Example prompts

- List powered-off VMs
- What is the Nutanix disk failure runbook?
- Reset `payments-api-01`
- Show critical Prism alerts

## Tests

```bash
cd backend
PYTHONPATH=. pytest -q
```
