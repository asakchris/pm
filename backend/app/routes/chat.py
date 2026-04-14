import sqlite3
import time

from fastapi import APIRouter, Depends, HTTPException

from app.ai import apply_actions, build_structured_messages, call_openrouter, parse_structured_output
from app.database import fetch_board, get_or_create_user
from app.dependencies import get_db, get_username
from app.models import ChatRequest, ChatResponse

router = APIRouter()

_last_chat_time: dict[str, float] = {}
_CHAT_MIN_INTERVAL = 1.0  # seconds between requests per user


def _check_rate_limit(username: str) -> None:
    now = time.monotonic()
    last = _last_chat_time.get(username, 0.0)
    if now - last < _CHAT_MIN_INTERVAL:
        raise HTTPException(status_code=429, detail="Too many requests. Please wait a moment.")
    _last_chat_time[username] = now


@router.post("/api/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    username: str = Depends(get_username),
    conn: sqlite3.Connection = Depends(get_db),
) -> ChatResponse:
    _check_rate_limit(username)
    user_id = get_or_create_user(conn, username)
    board = fetch_board(conn, user_id)
    messages = build_structured_messages(board, payload.history, payload.message)
    content, model = call_openrouter(messages)
    structured = parse_structured_output(content)

    reply = structured.reply
    if payload.apply_updates and structured.actions:
        skipped = apply_actions(conn, user_id, structured.actions)
        board = fetch_board(conn, user_id)
        if skipped:
            reply += f" ({skipped} action{'s' if skipped > 1 else ''} could not be applied — the referenced card or column may no longer exist.)"

    return ChatResponse(
        response=reply,
        actions=structured.actions,
        board=board,
        model=model,
    )
