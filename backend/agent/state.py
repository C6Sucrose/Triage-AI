from typing import Literal, TypedDict


class GraphState(TypedDict):
    tenant_id: str
    sender_email: str
    original_subject: str
    raw_body: str
    scrubbed_body: str
    category: Literal["bug", "billing", "general_inquiry", "feature_request"]