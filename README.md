# Autonomous Spec-to-Playwright Engine with Self-Healing Loop

A production-grade, zero-cost AI Engineering portfolio project bridging Automation QA expertise with Agentic Workflows, Hybrid Retrieval-Augmented Generation (RAG), and Cloud Deployment.

## Monorepo Layout

```text
.
├── apps/
│   ├── backend/               # FastAPI + LangGraph + Supabase pgvector + Playwright
│   │   ├── src/
│   │   │   ├── main.py        # FastAPI entrypoint, CORS, /health, and SSE streaming
│   │   │   ├── config.py      # Environment settings and configuration
│   │   │   ├── db/            # Supabase connection & pgvector search
│   │   │   ├── graph/         # LangGraph state machine & self-healing loop
│   │   │   ├── rag/           # Ingestion & Hybrid RAG retriever
│   │   │   └── sandbox/       # Headless Playwright test execution runner
│   │   ├── requirements.txt   # Python dependencies
│   │   └── .env.example       # Backend environment variables
│   │
│   └── frontend/              # Next.js 15 App Router, TypeScript, Tailwind CSS
│       ├── src/
│       │   └── app/           # App Router pages and layouts
│       ├── package.json       # Frontend dependencies
│       └── .env.example       # Frontend environment variables
│
├── packages/
│   └── test-fixtures/         # Reference Page Objects & Playwright baseline tests
└── README.md
```

## Quick Start

### 1. Backend Setup (`apps/backend`)

```bash
cd apps/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn src.main:app --reload --port 8000
```

Verify backend health check:
```bash
curl http://localhost:8000/health
```

### 2. Frontend Setup (`apps/frontend`)

```bash
cd apps/frontend
npm install
npm run dev
```

The Next.js dashboard will be available at `http://localhost:3000`.

