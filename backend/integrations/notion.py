"""
Notion integration — add pages to a database (inbox).
Uses Notion's internal integration API key (not OAuth).
"""

import httpx

from config import settings

NOTION_API_VERSION = "2022-06-28"


def add_to_inbox(title: str, content: str = "") -> dict:
    """
    Create a new page in the configured Notion database.
    Returns {"ok": True, "url": "..."} or {"ok": False, "error": "..."}
    """
    if not settings.notion_api_key or not settings.notion_database_id:
        return {"ok": False, "error": "Notion not configured"}

    headers = {
        "Authorization": f"Bearer {settings.notion_api_key}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_API_VERSION,
    }

    body: dict = {
        "parent": {"database_id": settings.notion_database_id},
        "properties": {
            "Name": {
                "title": [{"text": {"content": title}}]
            }
        },
    }

    # Add body content as a paragraph block if provided
    if content:
        body["children"] = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": content}}]
                },
            }
        ]

    resp = httpx.post(
        "https://api.notion.com/v1/pages",
        headers=headers,
        json=body,
        timeout=10.0,
    )

    if resp.status_code != 200:
        print(f"[notion] error {resp.status_code}: {resp.text[:200]}")
        return {"ok": False, "error": resp.text[:200]}

    url = resp.json().get("url", "")
    return {"ok": True, "url": url}
