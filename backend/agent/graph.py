from langgraph.graph import END, StateGraph, START

from agent.nodes import (
    categorize_email_node,
    draft_response_node,
    retrieve_context_node,
    scrub_pii_node,
)
from agent.state import GraphState


def route_email(state: GraphState) -> str:
    if state["category"] == "spam":
        return "end"
    return "retrieve"


workflow = StateGraph(GraphState)

workflow.add_node("scrub", scrub_pii_node)
workflow.add_node("categorize", categorize_email_node)
workflow.add_node("retrieve", retrieve_context_node)
workflow.add_node("draft", draft_response_node)

workflow.add_edge(START, "scrub")
workflow.add_edge("scrub", "categorize")
workflow.add_conditional_edges(
    "categorize",
    route_email,
    {"retrieve": "retrieve", "end": END},
)
workflow.add_edge("retrieve", "draft")
workflow.add_edge("draft", END)

app = workflow.compile()