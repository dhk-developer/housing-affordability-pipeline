"""Database connection helpers.

The connection settings come from environment variables (PGHOST, PGPORT,
PGDATABASE, PGUSER, PGPASSWORD). load_dotenv() copies them in from .env.
"""
from dotenv import load_dotenv
import psycopg

load_dotenv()


def get_connection():
    """Open a new connection to the housing database."""
    return psycopg.connect()


if __name__ == "__main__":
    with get_connection() as conn:
        version = conn.execute("select version()").fetchone()[0]
        print(version)