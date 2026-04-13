import sqlite3
from typing import Generator

from fastapi import Header

from app.config import DEFAULT_USER
from app.database import connect_db


def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = connect_db()
    try:
        yield conn
    finally:
        conn.close()


def get_username(x_user: str | None = Header(default=None)) -> str:
    return x_user or DEFAULT_USER
