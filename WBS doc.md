# 📄 Work Breakdown Structure (WBS): Triage AI (V1.0.0)

**Project:** Triage AI – B2B Support Orchestration Platform
**Architecture:** Next.js (Frontend), FastAPI (Backend), Supabase (Database), LangGraph (AI Engine), ChromaDB (Vector DB)
**Objective:** End-to-end development of an asynchronous webhook-to-ticketing AI pipeline.

---

## Epic 1: Infrastructure & Data Layer

Establishing the foundational database schema, security boundaries, and local development environments.

### DB-01: Provision Base PostgreSQL Tables & Types

**Priority:** 🔴 Critical
**Dependencies:** None
**Requirements:** Define `ticket_status` and `ticket_category` ENUMs. Create `users`, `tickets` (foreign key to users), and `documents` (foreign key to users) tables in Supabase.
**Acceptance Criteria:** Migrations run successfully, and all tables appear in the Supabase UI with correct foreign key constraints.

### DB-02: Implement Row-Level Security (RLS) Policies

**Priority:** 🔴 Critical
**Dependencies:** DB-01
**Requirements:** Enable RLS on `tickets` and `documents`. Write PostgreSQL policies utilizing `auth.uid()` for `SELECT`, `INSERT`, `UPDATE`, and `DELETE`.
**Acceptance Criteria:** A raw SQL test query using a mock JWT only returns rows matching that specific user ID.

### OPS-01: Containerize Next.js Frontend

**Priority:** 🔴 Critical
**Dependencies:** None
**Requirements:** Write a `Dockerfile` for the Next.js App Router application using a lightweight Node.js Alpine image.
**Acceptance Criteria:** `docker build` succeeds, and running the container serves the default Next.js page on port 3000.

### OPS-02: Containerize FastAPI Backend & ChromaDB

**Priority:** 🔴 Critical
**Dependencies:** OPS-01
**Requirements:** Write a multi-stage `Dockerfile` for the Python 3.11 FastAPI backend. Write a `docker-compose.yml` orchestrating the Frontend, Backend, and a local `chromadb/chroma` container.
**Acceptance Criteria:** Executing `docker-compose up` spins up all three services simultaneously without port conflicts.

---

## Epic 2: Authentication & Core Plumbing

Locking down the user interface and building the secure ingestion webhook for email payloads.

### UI-01: Next.js Initialization & Shadcn/UI Setup

**Priority:** 🟡 High
**Dependencies:** OPS-01
**Requirements:** Initialize Next.js with Tailwind CSS. Install Shadcn/UI and configure base visual components (`Button`, `Card`, `Table`, `Input`).
**Acceptance Criteria:** A static dashboard layout featuring a Header, Sidebar, and Main Content Area renders successfully on localhost.

### UI-02: Clerk Auth Integration

**Priority:** 🟡 High
**Dependencies:** UI-01
**Requirements:** Wrap the Next.js `layout.tsx` in `<ClerkProvider>`. Configure Next.js middleware to protect the `/dashboard` route.
**Acceptance Criteria:** Unauthenticated users attempting to navigate to `/dashboard` are forcibly redirected to the Clerk sign-in page.

### API-01: Clerk to Supabase Sync Webhook

**Priority:** 🟡 High
**Dependencies:** UI-02, DB-01
**Requirements:** Create a Next.js API route (`/api/webhooks/clerk`) to listen for Clerk's `user.created` events. Verify the Svix webhook signature and insert the `clerk_id` and `email` into the Supabase database.
**Acceptance Criteria:** Creating a test account in the frontend UI automatically generates a corresponding user row in Supabase.

### API-02: FastAPI Inbound Email Webhook & Validation

**Priority:** 🟡 High
**Dependencies:** DB-01, OPS-02
**Requirements:** Create a `POST /api/v1/webhooks/inbound-email` endpoint in FastAPI. Implement strict Pydantic schema validation for the JSON payload. Enforce API Key verification.
**Acceptance Criteria:** Sending a malformed POST request via Postman returns `422 Unprocessable Entity`; a valid request returns `200 OK`.

### API-03: Asynchronous Handoff & Database Queueing

**Priority:** 🟡 High
**Dependencies:** API-02
**Requirements:** Implement FastAPI `BackgroundTasks` for the inbound webhook. Insert a new row into the Supabase `tickets` table with status `queued`, returning `202 Accepted` immediately while processing continues in the background.
**Acceptance Criteria:** The HTTP request resolves in under 500ms, and a corresponding `queued` ticket appears in the database.

---

## Epic 3: Knowledge Base & RAG Pipeline

Building the ingestion engine to parse, chunk, and securely store company documents for AI context retrieval.

### AI-01: PDF Parsing Utility

**Priority:** 🟡 High
**Dependencies:** None
**Requirements:** Write a Python utility using `PyPDF2` (or `pdfplumber`) to convert uploaded `.pdf` byte streams into continuous text strings.
**Acceptance Criteria:** The utility function accurately extracts all text from a standard 3-page test PDF document.

### AI-02: Document Chunking & ChromaDB Ingestion

**Priority:** 🟡 High
**Dependencies:** AI-01, OPS-02
**Requirements:** Implement LangChain's `RecursiveCharacterTextSplitter`. Embed chunks using OpenAI and insert them into ChromaDB. Mandate the injection of `{"tenant_id": current_user}` into the metadata of every chunk.
**Acceptance Criteria:** Extracted text is successfully chunked, vectorized, and retrievable via a localized manual Python script.

### API-04: Secure Document Upload Endpoint

**Priority:** 🟡 High
**Dependencies:** AI-02, UI-02
**Requirements:** Create a FastAPI `POST /documents` endpoint accepting `multipart/form-data`. Validate the incoming Clerk JWT token to extract the `tenant_id` and pass the file to the pipeline established in AI-02.
**Acceptance Criteria:** An authenticated user can upload a PDF via Postman, and the backend securely processes and stores it in ChromaDB mapped to their tenant ID.

---

## Epic 4: The LangGraph Engine

Constructing the multi-agent state machine that drives classification, retrieval, and response drafting.

### AI-03: LangGraph State Definition & PII Scrubber Node

**Priority:** 🟡 High
**Dependencies:** None
**Requirements:** Define the `GraphState` TypedDict. Write a Node function utilizing Regex/Presidio to automatically mask sensitive data (credit cards, phone numbers) before LLM execution.
**Acceptance Criteria:** Inputting a string with a dummy credit card number outputs the same string with the numbers scrubbed to `[REDACTED]`.

### AI-04: The Categorizer Node

**Priority:** 🟡 High
**Dependencies:** AI-03
**Requirements:** Configure a GPT-4o-mini prompt instructing the LLM to read the incoming email and return a strict JSON object mapping to the defined `ticket_category` ENUM.
**Acceptance Criteria:** The LLM consistently outputs valid JSON category mapping (e.g., `{"category": "bug"}`) across 5 distinct test emails.

### AI-05: The Retriever & Drafter Nodes

**Priority:** 🟡 High
**Dependencies:** AI-04, AI-02
**Requirements:** Build the Retriever Node to execute a similarity search on ChromaDB, strictly filtered by the current `tenant_id`. Build the Drafter Node to prompt the LLM to write a reply using *only* that retrieved context.
**Acceptance Criteria:** LangSmith observability traces confirm the Drafter LLM is exclusively utilizing the correct ChromaDB context within its system prompt.

### AI-06: Graph Compilation & Testing

**Priority:** 🟡 High
**Dependencies:** AI-03, AI-04, AI-05
**Requirements:** Wire all nodes together using `StateGraph`. Configure conditional routing edges (e.g., if category is `spam`, skip the Retriever and proceed to End).
**Acceptance Criteria:** Injecting a raw email payload into the compiled graph successfully traverses all required nodes and yields a drafted reply.

---

## Epic 5: Output Integration & UI Finalization

Connecting the generated AI output to external systems and surfacing the data to the user dashboard.

### API-05: External Ticketing API Integration

**Priority:** 🟢 Medium
**Dependencies:** AI-06
**Requirements:** Write a Python REST client to POST a generated ticket to Trello or Linear. Wrap the HTTP request in a `tenacity` retry decorator to ensure network resilience. Create a final LangGraph `Ticket_Creator` node.
**Acceptance Criteria:** A successful LangGraph execution physically creates a corresponding ticket on a live test Trello/Linear board.

### API-06: Database State Finalization

**Priority:** 🟢 Medium
**Dependencies:** API-05
**Requirements:** Update the original Supabase `tickets` table row status from `processing` to `completed`. Insert the generated drafted text and the external ticket URL into the row.
**Acceptance Criteria:** The database row accurately reflects the completed job parameters and houses the external URL.

### UI-03: Dashboard Data Table & Upload Interface

**Priority:** 🟢 Medium
**Dependencies:** UI-02, API-06
**Requirements:** Build a Shadcn table component fetching data from the Supabase `tickets` table (filtered by the logged-in user). Implement a Modal containing a file input to POST PDFs to the `API-04` endpoint.
**Acceptance Criteria:** The UI displays the correct historical tickets, and the file upload modal successfully triggers a network request to the backend.

---

## Epic 6: Testing & Quality Assurance

Ensuring system determinism, robust error handling, and strict AI guardrails.

### TEST-01: Pytest Suite - Inbound Webhook Contracts

**Priority:** 🔴 Critical
**Dependencies:** API-02
**Requirements:** Configure `pytest-asyncio` and `FastAPI.TestClient`. Mock the Supabase client. Write tests verifying HTTP response codes based on payload validity and missing authentication.
**Acceptance Criteria:** The test suite passes 100%, accurately returning `422` for bad payloads, `401` for missing keys, and `202` for valid mocked handoffs.

### TEST-02: AI Guardrail - PII Scrubber Determinism

**Priority:** 🔴 Critical
**Dependencies:** AI-03
**Requirements:** Create a test suite of 20 "dirty" strings containing various formats of PII. Assert that the scrubber function successfully intercepts and mutates the data.
**Acceptance Criteria:** The test proves a 100% interception rate for targeted PII without false-positive redactions on benign alphanumeric strings.

### TEST-03: AI Guardrail - Categorizer Schema Enforcement

**Priority:** 🔴 Critical
**Dependencies:** AI-04
**Requirements:** Utilize `instructor` or LangChain's `with_structured_output`. Write a Pytest function feeding predefined emails to the Categorizer node to ensure strict Pydantic model adherence.
**Acceptance Criteria:** 10/10 test iterations successfully parse into the target Pydantic schema without throwing structural validation errors.

### TEST-04: AI Guardrail - Hallucination Strictness

**Priority:** 🔴 Critical
**Dependencies:** AI-05
**Requirements:** Establish an "LLM-as-a-judge" evaluation criteria. Feed the Drafter an out-of-context request (e.g., asking for a refund when the context only covers password resets) and evaluate the refusal rate.
**Acceptance Criteria:** The evaluation proves the drafted response contains zero factual claims outside of the injected context and gracefully refuses the out-of-bounds request.

---

## Epic 7: CI/CD & Deployment

Automating tests, enforcing code standards, and deploying to Google Cloud Platform.

### OPS-03: GitHub Actions - The CI/CD Gatekeeper

**Priority:** 🟢 Medium
**Dependencies:** Epic 6, OPS-02
**Requirements:** Create `.github/workflows/main.yml`. Define sequential pipeline jobs: `Lint`, `Test_Traditional`, `Test_AI_Evals`, and `Build_Deploy`. Configure GitHub Secrets for API keys.
**Acceptance Criteria:** A Pull Request triggers the test suite. Deliberate code breakages fail the pipeline and block merges. A successful merge to `main` automatically builds and pushes the Docker container to GCP Cloud Run.