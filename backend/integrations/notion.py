"""
Notion integration — add pages to a user's workspace inbox.
Uses per-user OAuth tokens stored in oauth_tokens (provider='notion').
refresh_token column stores workspace_id for reference.
"""

import httpx

from db.connection import get_connection

NOTION_API_VERSION = "2022-06-28"


def _get_notion_token(google_id: str) -> str | None:
    """Fetch the user's Notion access token from the DB."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT access_token FROM oauth_tokens WHERE google_id = %s AND provider = 'notion'",
        (google_id,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None


def _get_inbox_database_id(access_token: str) -> str | None:
    """
    Search the user's Notion workspace for a database to use as inbox.
    Looks for a database named 'Lumi Inbox' first, then falls back to the first database found.
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_API_VERSION,
    }
    resp = httpx.post(
        "https://api.notion.com/v1/search",
        headers=headers,
        json={"filter": {"value": "database", "property": "object"}, "page_size": 20},
        timeout=10.0,
    )
    if resp.status_code != 200:
        return None

    results = resp.json().get("results", [])
    # Prefer a database named "Lumi Inbox"
    for db in results:
        title_parts = db.get("title", [])
        name = "".join(p.get("plain_text", "") for p in title_parts)
        if name.lower() == "lumi inbox":
            return db["id"]
    # Fall back to first database
    return results[0]["id"] if results else None


def add_to_inbox(google_id: str, title: str, content: str = "") -> dict:
    """
    Create a new page in the user's Notion inbox database.
    Returns {"ok": True, "url": "..."} or {"ok": False, "error": "..."}
    """
    access_token = _get_notion_token(google_id)
    if not access_token:
        return {"ok": False, "error": "Notion not connected"}

    database_id = _get_inbox_database_id(access_token)
    if not database_id:
        return {"ok": False, "error": "No Notion database found — create a database named 'Lumi Inbox' in your workspace"}

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_API_VERSION,
    }

    body: dict = {
        "parent": {"database_id": database_id},
        "properties": {
            "Name": {
                "title": [{"text": {"content": title}}]
            }
        },
    }

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
