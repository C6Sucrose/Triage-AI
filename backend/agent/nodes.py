from functools import lru_cache
from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

from agent.state import GraphState
from utils.pii_scrubber import scrub_pii


class TicketCategory(BaseModel):
    """Classify a support email into one of four routing categories.

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
    """

    category: Literal["bug", "billing", "general_inquiry", "feature_request"] = Field(
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