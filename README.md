# ⚡ Triage AI

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black?logo=next.js)](https://nextjs.org/)
[![Docker](https://img.shields.io/badge/Docker-Supported-2496ED?logo=docker)](https://www.docker.com/)

**An open-source, asynchronous B2B workflow automation platform that triages customer support emails using LangGraph, RAG, and external ticketing APIs.**

---

### 🚀 See it in Action

> *[Insert a 5-second GIF here showing a dummy email being sent, and the Trello/Linear card magically appearing with a drafted response]*

## 📖 Overview

Triage AI is designed to solve the "Enterprise Data Chasm." It allows companies to autonomously route, classify, and draft responses to customer support tickets using their own private knowledge base, without relying on thin wrappers or exposing data to public models. 

Built with a focus on **Bring Your Own Cloud (BYOC)**, it is fully containerized and ready for on-premise or cloud deployment.

### ✨ Key Features
* **Asynchronous Webhook Ingestion:** Safely catches incoming emails from providers like Resend/SendGrid without freezing or timing out.
* **Multi-Agent AI Routing:** Utilizes **LangGraph** to classify issues (Bug, Billing, General) and route them to the correct retrieval pipeline.
* **Multi-Tenant Vector RAG:** Embeds company PDFs into **ChromaDB**, ensuring responses are grounded in strict company policy and protected by tenant-level filtering.
* **Action Execution:** Automatically drafts responses and pushes them directly to engineering boards (Linear/Trello) via REST/GraphQL APIs.
* **Secure by Default:** Built on **Supabase** with strict Row-Level Security (RLS) and **Clerk** authentication.

---

## 🏗️ Architecture

> *[Insert an Excalidraw or Mermaid.js architecture diagram here showing the flow from Webhook -> FastAPI -> LangGraph -> ChromaDB -> Trello]*

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
