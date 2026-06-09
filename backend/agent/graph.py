from langgraph.graph import END, StateGraph, START

from agent.nodes import (
    categorize_email_node,
    create_ticket_node,
    draft_response_node,
    finalize_ticket_node,
    retrieve_context_node,
    scrub_pii_node,
)
from agent.state import GraphState


def route_email(state: GraphState) -> str:
    if state["category"] == "spam":
        return "finalize_ticket"
    return "retrieve"


workflow = StateGraph(GraphState)

workflow.add_node("scrub", scrub_pii_node)
workflow.add_node("categorize", categorize_email_node)
workflow.add_node("retrieve", retrieve_context_node)
workflow.add_node("draft", draft_response_node)
workflow.add_node("create_ticket", create_ticket_node)
workflow.add_node("finalize_ticket", finalize_ticket_node)

workflow.add_edge(START, "scrub")
workflow.add_edge("scrub", "categorize")
workflow.add_conditional_edges(
    "categorize",
    route_email,
    {"retrieve": "retrieve", "finalize_ticket": "finalize_ticket"},
)
workflow.add_edge("retrieve", "draft")
workflow.add_edge("draft", "create_ticket")
workflow.add_edge("create_ticket", "finalize_ticket")
workflow.add_edge("finalize_ticket", END)

app = workflow.compile()