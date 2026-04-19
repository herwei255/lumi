import psycopg2
from pgvector.psycopg2 import register_vector
from config import settings


def get_connection():
    """Open a new Postgres connection with pgvector support registered."""
    conn = psycopg2.connect(settings.database_url)
    register_vector(conn)
    return conn
