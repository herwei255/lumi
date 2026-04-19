"""
Run once on startup to create tables if they don't exist.
Safe to call every startup — all statements use IF NOT EXISTS.
"""

import psycopg2

from config import settings
from db.connection import get_connection


def init_db():
    # First pass: plain connection (no register_vector) to create the extension.
    # register_vector fails if the vector type doesn't exist yet, so we can't
    # use get_connection() until after this step.
    conn = psycopg2.connect(settings.database_url)
    cur = conn.cursor()
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
    conn.commit()
    cur.close()
    conn.close()

    # Second pass: now that the extension exists, get_connection() works fine.
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id        SERIAL PRIMARY KEY,
            chat_id   TEXT UNIQUE NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # Each row is one message turn. embedding is a 768-dim float vector
    # (Gemini text-embedding-004 output size). NULL when embedding unavailable.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id         SERIAL PRIMARY KEY,
            user_id    INTEGER REFERENCES users(id) ON DELETE CASCADE,
            role       TEXT NOT NULL,       -- 'user' or 'assistant'
            content    TEXT NOT NULL,
            embedding  VECTOR(768),
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS web_users (
            id               SERIAL PRIMARY KEY,
            google_id        TEXT UNIQUE NOT NULL,
            email            TEXT,
            telegram_chat_id TEXT,
            created_at       TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS telegram_link_tokens (
            code       TEXT PRIMARY KEY,
            google_id  TEXT NOT NULL,
            used       BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS oauth_tokens (
            id            SERIAL PRIMARY KEY,
            google_id     TEXT NOT NULL,
            provider      TEXT NOT NULL,
            access_token  TEXT,
            refresh_token TEXT,
            expires_at    TIMESTAMPTZ,
            created_at    TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(google_id, provider)
        )
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("[db] Tables ready.")
