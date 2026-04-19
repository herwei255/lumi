"""
Text embeddings via Gemini's embedding API (gemini-embedding-001, 768 dims).

We use raw httpx here instead of the google-generativeai SDK because the SDK
has gRPC/fork issues inside Celery workers on Mac (see CLAUDE.md Known Issues).
The REST API works fine.
"""

import httpx
from config import settings

_MODEL = "gemini-embedding-001"
EMBEDDING_DIM = 768  # model supports up to 3072; we pin to 768 to match DB schema


def get_embedding(text: str) -> list[float] | None:
    """
    Return a 768-dim embedding vector for `text`, or None on any failure.

    Callers should handle None gracefully — messages without embeddings are
    still saved to the DB, just without semantic search support.
    """
    if not settings.gemini_api_key:
        return None

    try:
        resp = httpx.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{_MODEL}:embedContent",
            params={"key": settings.gemini_api_key},
            json={
                "model": f"models/{_MODEL}",
                "content": {"parts": [{"text": text}]},
                "outputDimensionality": EMBEDDING_DIM,
            },
            timeout=10.0,
        )
        resp.raise_for_status()
        return resp.json()["embedding"]["values"]
    except Exception as e:
        print(f"[embeddings] Failed: {e}")
        return None
