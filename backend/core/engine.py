"""
The bot engine — the heart of Lumi.

Phase 2: Persistent memory via Postgres + pgvector.
Phase 3: Tool use for integrations (Google Calendar).
  - If the user has connected Google Calendar, Gemini can call get_calendar_events.
  - Tool calls are intercepted, executed, and results fed back to Gemini.
"""

from config import settings
from core.embeddings import get_embedding
from core.llm import chat, chat_with_tools
from db.repository import (
    get_or_create_user,
    get_recent_messages,
    save_message,
    search_similar_messages,
)
from integrations.google_calendar import get_calendar_events, get_google_id_for_chat
from integrations.gmail import search_emails
from integrations.notion import add_to_inbox
from messaging.telegram import TelegramMessenger

SYSTEM_PROMPT = """you're lumi, a personal assistant living in the user's telegram. think helpful older sister energy — casual, warm, a little witty, and actually useful. you text like a real person: short, natural, no corporate fluff.

keep responses brief. one or two lines is usually right. don't over-explain.

use emojis sparingly — maybe once early in a conversation to warm things up, or when it genuinely fits the moment. not on every message. never forced.

match their energy. if they're venting, be real with them. if they're being casual, be casual back. if they need a straight answer, just give it. no "sure!", "of course!", or "great question!" — ever.

you remember past conversations. use that context naturally when it's relevant, but don't make a thing of it.

you have access to tools — use them. when the user asks about their calendar or emails, call the relevant tool immediately. don't say you don't have access.

you don't know their name yet. if they share it, use it.
"""

# Tool definition for Gemini — describes what get_calendar_events does
CALENDAR_TOOL = {
    "name": "get_calendar_events",
    "description": "Get the user's upcoming Google Calendar events. Use this when the user asks about their schedule, upcoming events, what they have planned, or anything calendar-related.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "days_ahead": {
                "type": "INTEGER",
                "description": "How many days ahead to fetch events for. Default is 7.",
            }
        },
    },
}


NOTION_TOOL = {
    "name": "add_to_notion_inbox",
    "description": "Add an item to the user's Notion inbox. Use this when the user wants to save something, add a task, note, or idea to Notion.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "title": {
                "type": "STRING",
                "description": "The title of the Notion page to create.",
            },
            "content": {
                "type": "STRING",
                "description": "Optional additional details or body text for the page.",
            },
        },
        "required": ["title"],
    },
}

GMAIL_TOOL = {
    "name": "search_emails",
    "description": "Search the user's Gmail inbox. Use this when the user asks about emails, messages they've received, or wants to find a specific email.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "query": {
                "type": "STRING",
                "description": "Gmail search query — same syntax as the Gmail search box. E.g. 'in:inbox is:unread', 'from:boss@example.com', 'subject:invoice'. Default: 'in:inbox'.",
            },
            "max_results": {
                "type": "INTEGER",
                "description": "Max number of emails to return. Default: 5.",
            },
        },
    },
}


def process_message(chat_id: str, body: str) -> None:
    """
    Main entry point — called by the Celery worker for every incoming message.

    1. Look up (or create) the user in Postgres
    2. Get recent + semantically similar history from DB
    3. Check if the user has Google Calendar connected
    4. Call the LLM (with tools if Calendar is connected)
    5. If Gemini wants to call a tool — execute it, send result back, get final reply
    6. Save both turns to DB with embeddings
    7. Send the reply via Telegram
    """
    messenger = TelegramMessenger()

    user_id = get_or_create_user(chat_id)

    recent = get_recent_messages(user_id, limit=10)

    embedding = get_embedding(body)
    extra_context = []
    if embedding:
        similar = search_similar_messages(user_id, embedding, limit=5)
        recent_contents = {m["content"] for m in recent}
        extra_context = [m for m in similar if m["content"] not in recent_contents]

    messages = extra_context + recent + [{"role": "user", "content": body}]

    google_id = get_google_id_for_chat(chat_id)
    has_calendar = google_id is not None and _has_oauth_token(google_id, "google_calendar")
    has_gmail = google_id is not None and _has_oauth_token(google_id, "gmail")
    has_notion = bool(settings.notion_api_key and settings.notion_database_id)

    try:
        if has_calendar or has_gmail or has_notion:
            reply = _chat_with_integrations(messages, google_id, has_calendar, has_gmail, has_notion)
        else:
            reply = chat(messages=messages, system=SYSTEM_PROMPT)
    except Exception as e:
        print(f"[engine] LLM error for chat {chat_id} (provider: {settings.llm_provider}): {e}")
        reply = "sorry, hit a snag — try again in a sec"

    save_message(user_id, "user", body, embedding)
    reply_embedding = get_embedding(reply)
    save_message(user_id, "assistant", reply, reply_embedding)

    messenger.send_message(chat_id, reply)
    print(f"[engine] [{settings.llm_provider}] Replied to {chat_id}: {reply[:80]}...")


def _has_oauth_token(google_id: str, provider: str) -> bool:
    from db.connection import get_connection
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM oauth_tokens WHERE google_id = %s AND provider = %s",
        (google_id, provider),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row is not None


def _chat_with_integrations(
    messages: list[dict],
    google_id: str | None,
    has_calendar: bool,
    has_gmail: bool,
    has_notion: bool = False,
) -> str:
    """
    Call Gemini with whichever tools are available for this user.
    Handles one tool call round-trip (tool_call → execute → final reply).
    """
    tools = []
    if has_calendar:
        tools.append(CALENDAR_TOOL)
    if has_gmail:
        tools.append(GMAIL_TOOL)
    if has_notion:
        tools.append(NOTION_TOOL)

    result = chat_with_tools(messages=messages, system=SYSTEM_PROMPT, tools=tools)

    if result.get("type") != "tool_call":
        return result.get("text", "")

    tool_name = result["name"]
    tool_args = result.get("args", {})

    if tool_name == "get_calendar_events":
        days_ahead = tool_args.get("days_ahead", 7)
        events = get_calendar_events(google_id, days_ahead=days_ahead)
        if events:
            tool_output = "\n".join(
                f"- {e['title']} ({e['start']})" + (f" @ {e['location']}" if e["location"] else "")
                for e in events
            )
        else:
            tool_output = "No events found."

    elif tool_name == "search_emails":
        query = tool_args.get("query", "in:inbox")
        max_results = tool_args.get("max_results", 5)
        emails = search_emails(google_id, query=query, max_results=max_results)
        if emails:
            tool_output = "\n".join(
                f"- From: {e['from']} | Subject: {e['subject']} | {e['snippet'][:100]}"
                for e in emails
            )
        else:
            tool_output = "No emails found."

    elif tool_name == "add_to_notion_inbox":
        title = tool_args.get("title", "Untitled")
        content = tool_args.get("content", "")
        result_notion = add_to_inbox(title=title, content=content)
        tool_output = f"Added to Notion: {result_notion.get('url', '')}" if result_notion["ok"] else f"Failed: {result_notion.get('error')}"

    else:
        return result.get("text", "")

    final = chat_with_tools(
        messages=messages,
        system=SYSTEM_PROMPT,
        tools=tools,
        tool_result={"name": tool_name, "content": tool_output},
    )
    return final.get("text", "couldn't fetch that right now")
