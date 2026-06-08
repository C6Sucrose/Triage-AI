from agent.state import GraphState
from utils.pii_scrubber import scrub_pii


def scrub_pii_node(state: GraphState) -> dict:
    scrubbed_text = scrub_pii(state["raw_body"])
    return {"scrubbed_body": scrubbed_text}