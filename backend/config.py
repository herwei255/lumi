from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM provider — "gemini" or "groq"
    llm_provider: str = "gemini"

    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    # Groq + Llama 3
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # Telegram
    telegram_bot_token: str
    telegram_secret_token: str = ""

    # Redis (Celery broker + result backend)
    redis_url: str = "redis://localhost:6379/0"

    # Postgres (persistent memory)
    database_url: str = "postgresql://lumi:lumi@localhost:5432/lumi"

    # Google OAuth (used for Calendar + Gmail integrations)
    google_client_id: str = ""
    google_client_secret: str = ""

    # Notion integration (internal API key)
    notion_api_key: str = ""
    notion_database_id: str = ""

    # Set DEBUG=true locally to skip webhook signature validation
    debug: bool = False

    # FastAPI port (used internally for self-calls)
    port: int = 8000

    # Public URLs — override in production
    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"

    model_config = {"env_file": ".env"}


settings = Settings()
