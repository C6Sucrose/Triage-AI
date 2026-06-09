import os

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

TRELLO_API_KEY = os.getenv("TRELLO_API_KEY")
TRELLO_API_TOKEN = os.getenv("TRELLO_API_TOKEN")
TRELLO_BASE_URL = "https://api.trello.com/1"
BOARD_NAME = "Triage AI Tickets"


def _auth_params() -> dict:
    return {"key": TRELLO_API_KEY, "token": TRELLO_API_TOKEN}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def _get_board_id() -> str:
    resp = requests.get(
        f"{TRELLO_BASE_URL}/members/me/boards",
        params={**_auth_params(), "fields": "name,id"},
        timeout=10,
    )
    resp.raise_for_status()
    boards = resp.json()

    for board in boards:
        if board["name"] == BOARD_NAME:
            return board["id"]

    # Board doesn't exist — create it
    resp = requests.post(
        f"{TRELLO_BASE_URL}/boards/",
        params={**_auth_params(), "name": BOARD_NAME},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["id"]


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def _get_first_list_id(board_id: str) -> str:
    resp = requests.get(
        f"{TRELLO_BASE_URL}/boards/{board_id}/lists",
        params={**_auth_params(), "fields": "name,id"},
        timeout=10,
    )
    resp.raise_for_status()
    lists = resp.json()
    if not lists:
        raise RuntimeError(f"No lists found on board {board_id}")
    return lists[0]["id"]


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def create_trello_card(title: str, description: str) -> str:
    board_id = _get_board_id()
    list_id = _get_first_list_id(board_id)

    resp = requests.post(
        f"{TRELLO_BASE_URL}/cards",
        params={
            **_auth_params(),
            "idList": list_id,
            "name": title,
            "desc": description,
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["url"]