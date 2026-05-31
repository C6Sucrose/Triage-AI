# ⚡ Triage AI

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black?logo=next.js)](https://nextjs.org/)
[![Docker](https://img.shields.io/badge/Docker-Supported-2496ED?logo=docker)](https://www.docker.com/)

**An open-source, asynchronous B2B workflow automation platform that triages customer support emails using LangGraph, RAG, and external ticketing APIs.**

---

### 🚀 See it in Action

> *[quick 5-second GIF here showing a dummy email being sent, and the Trello/Linear card appearing with a drafted response here later]*

## 📖 Overview

Triage AI is designed to solve the mundane task of manually setting up support tickets for further handling. It allows companies to automatically route, classify, and draft responses to customer support tickets using their own private knowledge base, without relying on wrappers or exposing data to public models. 

Built with a focus on **Bring Your Own Cloud (BYOC)**, it is fully containerized and ready for on-premise or cloud deployment.

### ✨ Key Features
* **Asynchronous Webhook Ingestion:** Safely catches incoming emails from providers like Resend/SendGrid without freezing or timing out.
* **Multi-Agent AI Routing:** Utilizes **LangGraph** to classify issues (Bug, Billing, General) and route them to the correct retrieval pipeline.
* **Multi-Tenant Vector RAG:** Embeds company PDFs into **ChromaDB**, ensuring responses are grounded in strict company policy and protected by tenant-level filtering.
* **Action Execution:** Automatically drafts responses and pushes them directly to engineering boards (Linear/Trello) via REST/GraphQL APIs.
* **Secure by Default:** Built on **Supabase** with strict Row-Level Security (RLS) and **Clerk** authentication.

---

## 🏗️ Architecture

> *[Will insert flow diagram later here]*

### Tech Stack
* **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind CSS, Shadcn/UI
* **Backend:** Python 3.11, FastAPI, Pydantic V2
* **AI Engine:** LangGraph, LangChain, OpenAI (`gpt-4o-mini`, `text-embedding-3-small`)
* **Database & State:** Supabase (PostgreSQL 15), ChromaDB
* **Infrastructure:** Docker, Docker Compose, GitHub Actions (CI/CD)

---

## ⏱️ Quickstart (Local Development)

Get the entire stack (UI, API, and Vector DB) running locally in under 5 minutes using Docker.

### Prerequisites
* [Docker](https://www.docker.com/products/docker-desktop/) & Docker Compose
* [Supabase Account](https://supabase.com/) (Free Tier)
* [Clerk Account](https://clerk.com/) (Free Tier)
* OpenAI API Key

### 1. Clone the Repository
```bash
git clone [https://github.com/yourusername/triage-ai.git](https://github.com/yourusername/triage-ai.git)
cd triage-ai

```

### 2. Configure Environment Variables

Copy the example environment files for both the frontend and backend.

```bash
cp frontend/.env.example frontend/.env.local
cp backend/.env.example backend/.env

```

Fill in the required keys (see the [Environment Variables](#%EF%B8%8F-environment-variables) section below).

### 3. Spin up the Containers

```bash
docker-compose up --build

```

* **Frontend Dashboard:** `http://localhost:3000`
* **FastAPI Swagger Docs:** `http://localhost:8080/docs`
* **ChromaDB Instance:** `http://localhost:8000`

---

## ⚙️ Environment Variables

### Backend (`backend/.env`)

| Variable | Description |
| --- | --- |
| `OPENAI_API_KEY` | Your OpenAI API key for LLM and Embeddings. |
| `SUPABASE_URL` | Your Supabase Project URL. |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase Service Role Key (Keep this secret!). |
| `TRELLO_API_KEY` | (Optional) API Key for Trello integration. |
| `TRELLO_TOKEN` | (Optional) Token for Trello integration. |
| `LANGCHAIN_TRACING_V2` | Set to `true` to enable LangSmith observability. |
| `LANGCHAIN_API_KEY` | Your LangSmith API Key. |

### Frontend (`frontend/.env.local`)

| Variable | Description |
| --- | --- |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Clerk Auth Frontend Key. |
| `CLERK_SECRET_KEY` | Clerk Auth Backend Secret. |
| `NEXT_PUBLIC_API_URL` | Set to `http://localhost:8080/api/v1` locally. |

---

## 🗺️ Roadmap (V1)

* [x] Base PostgreSQL/Supabase Schema Initialization
* [x] Next.js Dashboard & Clerk Auth Integration
* [ ] FastAPI Webhook Ingestion & Pydantic Validation
* [ ] PyPDF2 Extraction & ChromaDB Vectorization
* [ ] LangGraph State Machine (Categorizer, Retriever, Drafter)
* [ ] Linear/Trello API Action Execution

---

## 🤝 Contributing

Contributions make the open-source community an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

Review the [CONTRIBUTING.md](docs/CONTRIBUTING.md) for detailed guidelines.

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.