import logging
import os

from dotenv import load_dotenv
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, EmailStr, Field
from supabase import Client, create_client

load_dotenv()

INBOUND_WEBHOOK_API_KEY = os.getenv("INBOUND_WEBHOOK_API_KEY")
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

logger = logging.getLogger("triage.backend")

app = FastAPI(title="Triage AI Backend")

# ── Security ──────

api_key_header = APIKeyHeader(name="X-API-Key")


def verify_api_key(api_key: str = Depends(api_key_header)) -> str:
    if api_key != INBOUND_WEBHOOK_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return api_key


# ── Schemas ─────────────────────────

class InboundEmailPayload(BaseModel):
    tenant_id: str = Field(..., description="Clerk user ID this email belongs to")
    sender_email: EmailStr
    original_subject: str = Field(..., min_length=1)
    body_text: str


# ── Background task ───────────

def _get_supabase_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError(
            "Missing NEXT_PUBLIC_SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY"
        )
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


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