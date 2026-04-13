from fastapi import APIRouter

from app.routes import board, chat, static

api_router = APIRouter()
api_router.include_router(board.router)
api_router.include_router(chat.router)

static_router = static.router
