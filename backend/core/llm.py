"""
LLM provider abstraction.

Swap between Gemini and Groq by changing LLM_PROVIDER in your .env.
Adding a new provider = add one function + one elif. Nothing else changes.
"""

import httpx
from groq import Groq

from config import settings


def chat(messages: list[dict], system: str) -> str:
    """Send a conversation to the LLM and return the reply text."""
    if settings.llm_provider == "gemini":
        return _gemini_chat(messages, system)
    elif settings.llm_provider == "groq":
        return _groq_chat(messages, system)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER '{settings.llm_provider}'.")


def chat_with_tools(
    messages: list[dict],
    system: str,
    tools: list[dict],
    tool_result: dict | None = None,
) -> dict:
    """
    Call Gemini with tool definitions. Returns either:
      {"type": "tool_call", "name": "...", "args": {...}}  — Gemini wants to call a tool
      {"type": "text", "text": "..."}                      — Gemini returned a normal reply

    If tool_result is provided, it appends the tool output to the conversation
    and makes a second call to get the final natural language reply.

    Only supported for Gemini (Groq tool use is different — add later if needed).
    """
    if settings.llm_provider != "gemini":
        # Fallback: just do a normal chat without tools
        return {"type": "text", "text": chat(messages, system)}

    contents = _messages_to_gemini(messages)

    # If we have a tool result, append it as a "function response" turn
    if tool_result:
        contents.append({
            "role": "user",
            "parts": [{
                "functionResponse": {
                    "name": tool_result["name"],
                    "response": {"content": tool_result["content"]},
                }
            }],
        })

    resp = httpx.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent",
        params={"key": settings.gemini_api_key},
        json={
            "system_instruction": {"parts": [{"text": system}]},
            "contents": contents,
            "tools": [{"functionDeclarations": tools}],
            "toolConfig": {"functionCallingConfig": {"mode": "AUTO"}},
        },
        timeout=30.0,
    )
    resp.raise_for_status()

    candidate = resp.json()["candidates"][0]["content"]
    parts = candidate.get("parts", [])

    # Scan all parts — Gemini 2.5 Flash sometimes puts functionCall after a thought/text part
    for part in parts:
        if "functionCall" in part:
            return {
                "type": "tool_call",
                "name": part["functionCall"]["name"],
                "args": part["functionCall"].get("args", {}),
            }

    # No tool call — collect all text parts
    text = " ".join(p.get("text", "") for p in parts if "text" in p)
    return {"type": "text", "text": text}


# ── Gemini ────────────────────────────────────────────────────────────────────

def _gemini_chat(messages: list[dict], system: str) -> str:
    """
    Call Gemini via the REST API using httpx (not the google-generativeai SDK).

    The SDK uses gRPC which breaks inside Celery forked workers on Mac.
    The REST API has no such issue — same fix we use for embeddings.
    """
    resp = httpx.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent",
        params={"key": settings.gemini_api_key},
        json={
            "system_instruction": {"parts": [{"text": system}]},
            "contents": _messages_to_gemini(messages),
        },
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"]


def _messages_to_gemini(messages: list[dict]) -> list[dict]:
    """Convert OpenAI-style messages to Gemini's content format."""
    return [
        {
            "role": "user" if msg["role"] == "user" else "model",
            "parts": [{"text": msg["content"]}],
        }
        for msg in messages
    ]


# ── Groq + Llama 3 ───────────────────────────────────────────────────────────

def _groq_chat(messages: list[dict], system: str) -> str:
    """Call Llama 3 via Groq's OpenAI-compatible API."""
    client = Groq(api_key=settings.groq_api_key)
    full_messages = [{"role": "system", "content": system}] + messages
    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=full_messages,
        max_tokens=1024,
    )
    return response.choices[0].message.content
