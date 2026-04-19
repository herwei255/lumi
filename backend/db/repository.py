"""
All database read/write operations for Lumi's memory.

Each function opens its own connection and closes it when done.
This is fine for a Celery worker that handles one message at a time.
"""

from db.connection import get_connection


def get_or_create_user(chat_id: str) -> int:
    """
    Return the DB user_id for a Telegram chat_id, creating the row if needed.
    ON CONFLICT means this is safe to call every time without checking first.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO users (chat_id) VALUES (%s)
        ON CONFLICT (chat_id) DO UPDATE SET chat_id = EXCLUDED.chat_id
        RETURNING id
        """,
        (chat_id,),
    )
    user_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return user_id


def save_message(user_id: int, role: str, content: str, embedding: list[float] | None = None) -> None:
    """Persist one message turn. embedding may be None if Gemini API is unavailable."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO messages (user_id, role, content, embedding) VALUES (%s, %s, %s, %s)",
        (user_id, role, content, embedding),
    )
    conn.commit()
    cur.close()
    conn.close()


def get_recent_messages(user_id: int, limit: int = 10) -> list[dict]:
    """
    Return the last `limit` messages in chronological order (oldest first).
    This is the primary context window — what happened recently.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT role, content FROM messages
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (user_id, limit),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    # fetchall returns newest-first, reverse so LLM sees chronological order
    return [{"role": row[0], "content": row[1]} for row in reversed(rows)]


def search_similar_messages(user_id: int, embedding: list[float], limit: int = 5) -> list[dict]:
    """
    Find messages semantically similar to `embedding`, skipping the most recent 10.

    The <=> operator is pgvector's cosine distance (lower = more similar).
    We exclude the last 10 because get_recent_messages already covers those —
    no point duplicating them in the context.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT role, content FROM messages
        WHERE user_id = %s
          AND embedding IS NOT NULL
          AND id NOT IN (
              SELECT id FROM messages
              WHERE user_id = %s
              ORDER BY created_at DESC
              LIMIT 10
          )
        ORDER BY embedding <=> %s::vector
        LIMIT %s
        """,
        (user_id, user_id, embedding, limit),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"role": row[0], "content": row[1]} for row in rows]
