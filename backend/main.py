import io
import logging
import os

import jwt
from dotenv import load_dotenv
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, UploadFile, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field
from supabase import Client, create_client

from utils.pdf_parser import extract_text_from_pdf
from utils.rag_engine import ingest_document

load_dotenv()

INBOUND_WEBHOOK_API_KEY = os.getenv("INBOUND_WEBHOOK_API_KEY")
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY")

CLERK_PEM_PUBLIC_KEY = os.getenv("CLERK_PEM_PUBLIC_KEY")
if CLERK_PEM_PUBLIC_KEY:
    CLERK_PEM_PUBLIC_KEY = CLERK_PEM_PUBLIC_KEY.replace('\\n', '\n')

logger = logging.getLogger("triage.backend")

app = FastAPI(title="Triage AI Backend")

# ── Security ─────────

api_key_header = HTTPBearer()


def verify_api_key(api_key: str = Depends(api_key_header)) -> str:
    if api_key != INBOUND_WEBHOOK_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return api_key


_bearer_scheme = HTTPBearer()


def verify_clerk_token(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> str:
    """Decode a Clerk-issued JWT using the RS256 Public Key."""
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            CLERK_PEM_PUBLIC_KEY,
            algorithms=["RS256"],
            options={"verify_aud": False} # Session tokens don't always have a strict 'aud' claim
        )
    except jwt.ExpiredSignatureError:
        logger.error("Clerk token has expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clerk token has expired",
        )
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid Clerk token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Clerk token",
        )
        
    sub: str | None = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject claim",
        )
    return sub


# ── Schemas ─────────────────────────

class InboundEmailPayload(BaseModel):
    tenant_id: str = Field(..., description="Clerk user ID this email belongs to")
    sender_email: EmailStr
    original_subject: str = Field(..., min_length=1)
    body_text: str


# ── Helpers ──────────

def _get_supabase_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError(
            "Missing NEXT_PUBLIC_SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY"
        )
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


# ── Background task ───────────

def process_inbound_email(payload: InboundEmailPayload) -> None:
    try:
        supabase = _get_supabase_client()

        # Removed .single() to avoid the fatal PGRST116 exception
        user_result = (
            supabase.table("users")
            .select("id")
            .eq("clerk_id", payload.tenant_id)
            .execute()
        )

        # handle the case where the user does not exist
        if not user_result.data:
            logger.warning(
                "No user found for clerk_id=%s. Dropping payload.", payload.tenant_id,
            )
            return

        # Extract the UUID from the first dictionary in the returned list
        user_id: str = user_result.data[0]["id"]

        ticket_result = (
            supabase.table("tickets")
            .insert(
                {
                    "user_id": user_id,
                    "sender_email": payload.sender_email,
                    "original_subject": payload.original_subject,
                    "status": "queued",
                }
            )
            .execute()
        )

        if ticket_result.data:
            logger.info(
                "Ticket created for user_id=%s from %s",
                user_id,
                payload.sender_email,
            )
    except Exception:
        logger.exception(
            "Failed to process inbound email for tenant_id=%s",
            payload.tenant_id,
        )


# ── Routes ────────────

@app.get("/")
def read_root() -> dict[str, str]:
    return {"status": "Backend is running!"}


@app.post(
    "/api/v1/webhooks/inbound-email",
    dependencies=[Depends(verify_api_key)],
    status_code=status.HTTP_202_ACCEPTED,
)
async def inbound_email_webhook(
    payload: InboundEmailPayload,
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    background_tasks.add_task(process_inbound_email, payload)
    return {"status": "accepted"}


@app.post(
    "/api/v1/documents",
    status_code=status.HTTP_200_OK,
)
async def upload_document(
    file: UploadFile,
    tenant_id: str = Depends(verify_clerk_token),
) -> dict[str, str | int]:
    try:
        file_bytes = await file.read()
        filename = file.filename or "unnamed.pdf"
        supabase = _get_supabase_client()

        # Step A — Resilience Storage: upload to Supabase Storage
        storage_path = f"{tenant_id}/{filename}"
        supabase.storage.from_("raw_documents").upload(
            path=storage_path,
            file=file_bytes,
            file_options={
                "content-type": "application/pdf",
                "upsert": "true"
            }
        )

        # Step B — Extraction: parse PDF text
        text = extract_text_from_pdf(file_bytes)

        # Step C — Ingestion: chunk + embed + store in ChromaDB
        chunks_count = ingest_document(text, tenant_id, filename)

        return {
            "status": "uploaded",
            "filename": filename,
            "chunks_ingested": chunks_count,
        }
    except Exception:
        logger.exception("Document upload/ingestion failed for tenant=%s", tenant_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document upload or ingestion failed",
        )