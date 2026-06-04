import os

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, EmailStr, Field

load_dotenv()

INBOUND_WEBHOOK_API_KEY = os.getenv("INBOUND_WEBHOOK_API_KEY")

app = FastAPI(title="Triage AI Backend")

# ── Security ──────────────────────────────────────────────────────────────────

api_key_header = APIKeyHeader(name="X-API-Key")


def verify_api_key(api_key: str = Depends(api_key_header)) -> str:
    if api_key != INBOUND_WEBHOOK_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return api_key


# ── Schemas ───────────────────────────────────────────────────────────────────

class InboundEmailPayload(BaseModel):
    tenant_id: str = Field(..., description="Clerk user ID this email belongs to")
    sender_email: EmailStr
    original_subject: str = Field(..., min_length=1)
    body_text: str


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
def read_root() -> dict[str, str]:
    return {"status": "Backend is running!"}


@app.post(
    "/api/v1/webhooks/inbound-email",
    dependencies=[Depends(verify_api_key)],
)
async def inbound_email_webhook(payload: InboundEmailPayload) -> dict[str, str]:
    # TODO: Process the inbound email (e.g., store it, trigger triage workflow)
    return {"status": "accepted"}