from functools import lru_cache
from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

from agent.state import GraphState
from utils.pii_scrubber import scrub_pii
from utils.rag_engine import retrieve_context
from utils.trello_client import create_trello_card


class TicketCategory(BaseModel):
    """Classify a support email into one of five routing categories.

    Categories:
        bug:            The user reports a crash, error, malfunction, or broken
                        feature — anything indicating the product is not working
                        as intended.
        billing:        The user asks about invoices, charges, refunds, payment
                        methods, pricing, or subscription changes.
        general_inquiry: The user asks a question that does not fit the other
                        categories — e.g. "How do I…?", account settings, or
                        general curiosity.
        feature_request: The user suggests a new capability, enhancement, or
                        improvement they would like added to the product.
        spam:           The email is promotional, malicious, phishing, or
                        otherwise irrelevant — it should not be processed
                        further.
    """

    category: Literal["bug", "billing", "general_inquiry", "feature_request", "spam"] = Field(
        description="The support category assigned to this email."
    )


_CATEGORY_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a support-ticket classifier. "
            "Read the scrubbed email body below and assign exactly one category. "
            "Respond with the category name only.",
        ),
        ("human", "{scrubbed_body}"),
    ]
)


@lru_cache(maxsize=1)
def _get_category_chain():
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
    ).with_structured_output(TicketCategory)
    return _CATEGORY_PROMPT | llm


def scrub_pii_node(state: GraphState) -> dict:
    scrubbed_text = scrub_pii(state["raw_body"])
    return {"scrubbed_body": scrubbed_text}


def categorize_email_node(state: GraphState) -> dict:
    result = _get_category_chain().invoke({"scrubbed_body": state["scrubbed_body"]})
    return {"category": result.category}


# ── Drafter prompt ─────────────────────────────────────────────────

_DRAFTER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful B2B support agent. "
            "Draft a reply to the user's email using ONLY the provided "
            "'Retrieved Context'. If the context does not contain the answer, "
            "politely state that you are escalating the ticket to a human "
            "agent. Do not hallucinate.",
        ),
        (
            "human",
            "Retrieved Context:\n{retrieved_context}\n\n"
            "User Email:\n{scrubbed_body}",
        ),
    ]
)


@lru_cache(maxsize=1)
def _get_drafter_chain():
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2)
    return _DRAFTER_PROMPT | llm


# ── Retriever node ─────────────────────────────────────────────────

def retrieve_context_node(state: GraphState) -> dict:
    context = retrieve_context(
        query=state["scrubbed_body"],
        tenant_id=state["tenant_id"],
    )
    return {"retrieved_context": context}


# ── Drafter node ───────────────────────────────────────────────────

def draft_response_node(state: GraphState) -> dict:
    response = _get_drafter_chain().invoke(
        {
            "retrieved_context": state["retrieved_context"],
            "scrubbed_body": state["scrubbed_body"],
        },
    )
    return {"draft_response": response.content}


# ── Ticket creation node ────────────────────────────────────────────

def create_ticket_node(state: GraphState) -> dict:
    title = f"[{state['category'].upper()}] {state['original_subject']}"
    description = (
        f"**Sender:** {state['sender_email']}\n\n"
        f"**Original email:**\n{state['raw_body']}\n\n"
        f"**Drafted response:**\n{state['draft_response']}"
    )
    card_url = create_trello_card(title=title, description=description)
    return {"trello_card_url": card_url}