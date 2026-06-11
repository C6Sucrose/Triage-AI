# ⚡ Triage AI

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black?logo=next.js)](https://nextjs.org/)
[![Docker](https://img.shields.io/badge/Docker-Supported-2496ED?logo=docker)](https://www.docker.com/)

**An open-source, asynchronous B2B workflow automation platform that triages customer support emails using LangGraph, RAG, and external ticketing APIs.**

---

### 🚀 See it in Action

<img width="1155" height="936" alt="Animation" src="https://github.com/user-attachments/assets/d774ecac-949f-4c9a-938d-65bc26f10ad4" />


## 📖 Overview

Triage AI automates the mundane task of manually triaging customer support emails. It routes, classifies, and drafts grounded responses using your own private knowledge base — no wrappers, no public model exposure, no cross-tenant data leakage.

Built with a **Bring Your Own Cloud (BYOC)** philosophy, the entire stack is fully containerized and ready for on-premise or cloud deployment.

### ✨ Key Features

- **Asynchronous Webhook Ingestion** — Accepts inbound emails from providers like Resend/SendGrid via a 202-accepted background task pipeline. The webhook never blocks or times out.
- **Multi-Agent AI Routing** — A LangGraph state machine classifies emails into five categories (Bug, Billing, Feature Request, General Inquiry, Spam) and conditionally short-circuits spam before retrieval, saving LLM tokens and latency.
- **Multi-Tenant Vector RAG** — Company PDFs are chunked, embedded, and stored in ChromaDB with tenant-scoped metadata filters. Retrieval is always scoped to the uploading organization — zero cross-tenant leakage.
- **PII Redaction** — Emails, phone numbers, and credit card numbers are scrubbed before any LLM call, ensuring sensitive data never reaches external models.
- **Action Execution** — Drafted responses and full context are pushed directly to engineering boards (Trello) via REST APIs with automatic retry and graceful degradation.
- **Secure by Design** — Clerk authentication with RS256 JWT verification on the frontend and API-key auth on the webhook endpoint. Supabase enforces Row Level Security with the anon key; the backend container uses the service role key in a sealed environment.

---

## 🏗️ Architecture

```
  ┌───────────────┐     ┌───────────────┐      ┌───────────────┐
  │   Frontend     │    │    Backend     │     │    ChromaDB    │
  │   Next.js 14   │──▶ │    FastAPI     │ ──▶│   Vector DB    │
  │   Port 3000    │    │   Port 8080    │     │   Port 8000    │
  │  Clerk Auth    │    │  LangGraph +   │     │  Tenant-scoped │
  │  Supabase      │    │  ChatGroq      │     │  Metadata      │
  │  (anon key)    │    │                │     │  Filtering     │
  └───────────────┘     └───────┬───────┘      └───────────────┘
                                │
                         ┌──────┴──────┐
                         │   Supabase   │
                         │   (Cloud)    │
                         │  Postgres +  │
                         │   Storage    │
                         └─────────────┘
```

### Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | Next.js 14 (App Router), TypeScript, Tailwind CSS, shadcn/ui, Clerk |
| **Backend** | Python 3.12, FastAPI, Pydantic V2, LangGraph, LangChain |
| **AI / LLM** | ChatGroq (`llama-3.3-70b-versatile`), HuggingFace (`all-MiniLM-L6-v2` local embeddings) |
| **Database & State** | Supabase (PostgreSQL 15 + Storage), ChromaDB (persistent vector store) |
| **Infrastructure** | Docker, Docker Compose |

---

## 🔄 How It Works

### Email Triage Pipeline

```
Inbound Email → Webhook (202 Accepted)
                    │
                    ▼ (Background Task)
              ┌───────────┐
              │    Scrub  │  Redact PII (emails, phones, credit cards)
              └─────┬─────┘
                    ▼
              ┌───────────┐
              │ Categorize│  ChatGroq → Bug / Billing / Feature / General / Spam
              └─────┬─────┘
                    ▼
              ┌─ Conditional Route ─┐
              │                     │
         Spam?──YES──▶ Finalize     │
              │      (status=spam)  │
              │                     │
             NO──────▶ Retrieve     │
              │    (ChromaDB RAG)   │
              ▼                     │
           Draft                    │
        (anti-hallucination)        │
              ▼                     │
         Create Ticket (Trello)     │
              ▼                     │
         Finalize (status=completed)│
              └─────────────────────┘
```

1. **Ingest** — The webhook accepts the email payload and returns immediately. Processing runs asynchronously in a FastAPI background task.
2. **Scrub** — Regex-based PII redaction removes emails, phone numbers, and credit card numbers before any LLM call.
3. **Categorize** — A ChatGroq chain with structured output classifies the email. Spam emails short-circuit directly to finalization.
4. **Retrieve** — Tenant-scoped ChromaDB similarity search (k=3) fetches relevant context from the organization's knowledge base.
5. **Draft** — A ChatGroq chain with an anti-hallucination prompt generates a grounded response using only the retrieved context.
6. **Execute** — A Trello card is created with the full context (sender, body, drafted reply). On failure, the pipeline continues — no single peripheral step blocks the core flow.
7. **Finalize** — The Supabase ticket row is updated with the category, drafted reply, and external ticket URL.

### Document Upload Pipeline

```
PDF Upload (Clerk JWT auth)
      │
      ▼
  ┌────────────┐
  │ Storage    │  Raw PDF → Supabase `raw_documents` bucket (best-effort)
  └─────┬──────┘
        ▼
  ┌────────────┐
  │ Extract    │  pypdf → plain text (graceful on encrypted/corrupted files)
  └─────┬──────┘
        ▼
  ┌────────────┐
  │ Ingest     │  Chunk → Embed → ChromaDB (tenant-scoped metadata)
  └─────┬──────┘
        ▼
  ┌────────────┐
  │ Catalog    │  Metadata row → Supabase `documents` table (best-effort)
  └────────────┘
```

### Authentication Flow

| Flow | Mechanism | Endpoint |
|------|-----------|----------|
| **Webhook** (machine-to-machine) | Bearer API key (`INBOUND_WEBHOOK_API_KEY`) | `POST /api/v1/webhooks/inbound-email` |
| **Document Upload** (user-facing) | Clerk JWT (RS256, `sub` → `tenant_id`) | `POST /api/v1/documents` |
| **Dashboard** (user-facing) | Clerk session + Supabase anon key (RLS-enforced) | `/dashboard`, `/dashboard/knowledge` |
| **User Sync** (Clerk → Supabase) | Svix signature verification | `POST /api/webhooks/clerk` |

---

## ⏱️ Quickstart

Get the entire stack running locally in under 5 minutes.

### Prerequisites

- [Docker](https://www.docker.com/products/docker-desktop/) & Docker Compose
- [Supabase Account](https://supabase.com/) (Free Tier)
- [Clerk Account](https://clerk.com/) (Free Tier)
- [Groq API Key](https://console.groq.com/) (Free Tier)

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/triage-ai.git
cd triage-ai
```

### 2. Configure Environment Variables

```bash
cp frontend/.env.local.example frontend/.env.local
cp backend/.env.example backend/.env
```

Fill in the required keys (see [Environment Variables](#-environment-variables)).

### 3. Start the Stack

```bash
docker-compose up --build
```

| Service | URL |
|---------|-----|
| Frontend Dashboard | `http://localhost:3000` |
| FastAPI Swagger Docs | `http://localhost:8080/docs` |
| ChromaDB | `http://localhost:8000` (internal only within Docker) |

---

## ⚙️ Environment Variables

### Backend (`backend/.env`)

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase Project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase Service Role Key (backend container only; bypasses RLS) |
| `CLERK_SECRET_KEY` | Clerk Backend Secret Key |
| `CLERK_PEM_PUBLIC_KEY` | RS256 Public Key for Clerk JWT verification |
| `INBOUND_WEBHOOK_API_KEY` | Shared secret for inbound email webhook auth |
| `GROQ_API_KEY` | Groq API key for ChatGroq LLM calls |
| `CHROMA_DB_URL` | ChromaDB server URL (`http://localhost:8000` locally, `http://chromadb:8000` in Docker) |
| `TRELLO_API_KEY` | Trello API key for ticket creation |
| `TRELLO_API_TOKEN` | Trello API token for ticket creation |

### Frontend (`frontend/.env.local`)

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Clerk frontend publishable key |
| `NEXT_PUBLIC_CLERK_SIGN_IN_URL` | Sign-in route (`/sign-in`) |
| `NEXT_PUBLIC_CLERK_SIGN_UP_URL` | Sign-up route (`/sign-up`) |
| `CLERK_SECRET_KEY` | Clerk backend secret (server-side only) |
| `WEBHOOK_SECRET` | Svix secret for Clerk webhook signature verification |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase Project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase Anon Key (RLS-enforced, no service role in frontend) |
| `NEXT_PUBLIC_API_URL` | Backend API URL — must be browser-resolvable (`http://localhost:8080`) |

---

## 🐳 Docker & Containerization

The stack runs as three Docker services with a persistent named volume for ChromaDB data:

| Service | Base Image | Port | Healthcheck | Notes |
|---------|-----------|------|-------------|-------|
| **frontend** | `node:22-alpine` (multi-stage) | `3000:3000` | `wget` every 30s | Standalone Next.js output, non-root user, 6 build-time `NEXT_PUBLIC_*` args |
| **backend** | `python:3.12-slim` (multi-stage) | `8080:8080` | `urllib` every 15s | Non-root `appuser`, pinned requirements, uvicorn entrypoint |
| **chromadb** | `chromadb/chroma:latest` | `8000` (internal) | — | Persistent volume (`chroma_data`), `IS_PERSISTENT=TRUE` |

All Dockerfiles use multi-stage builds with non-root users for minimal, secure production images. Environment secrets are injected at runtime via `env_file` directives — never baked into image layers.

**Networking**: The frontend's `NEXT_PUBLIC_API_URL` is hardcoded to `http://localhost:8080` because it's a browser-side variable that must resolve outside the Docker network. The backend-to-ChromaDB connection uses Docker DNS (`http://chromadb:8000`).

---

## 🗺️ Roadmap

### V1 — Core Platform ✓

- [x] Supabase schema with Row Level Security and Clerk user sync
- [x] Next.js 14 dashboard with Clerk auth and shadcn/ui components
- [x] FastAPI webhook ingestion with Pydantic validation and background tasks
- [x] PDF extraction (pypdf) and ChromaDB vectorization (tenant-scoped)
- [x] LangGraph state machine (PII scrub → categorize → retrieve → draft → execute → finalize)
- [x] Trello API action execution with retry and graceful degradation
- [x] Document upload pipeline with Clerk JWT auth and resilience-first design
- [ ] Guard Rails and Test Suites in Github Actions

### V2 — Next Steps

- [ ] Linear/Jira integration alongside Trello
- [ ] Slack notification channel for critical tickets
- [ ] Admin dashboard with analytics and ticket volume metrics
- [ ] Multi-provider email ingestion (SendGrid, Mailgun, Postmark)
- [ ] Custom category taxonomy per organization
- [ ] Rate limiting and webhook IP whitelisting

---

## 🤝 Contributing

Contributions make the open-source community an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

Distributed under the GNU GPLv3 License. See `LICENSE` for more information.
