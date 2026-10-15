"""Database connection helpers.

The connection settings come from environment variables (PGHOST, PGPORT,
PGDATABASE, PGUSER, PGPASSWORD). load_dotenv() copies them in from .env.
"""
from pathlib import Path

from dotenv import load_dotenv
import psycopg
from sqlalchemy import create_engine

load_dotenv()


def get_connection():
    """Open a new connection to the housing database."""
    return psycopg.connect()


def get_engine():
    """A SQLAlchemy engine for pandas, using the same PG... settings."""
    return create_engine("postgresql+psycopg://")


def run_sql_file(conn, path):
    """Run every statement in a .sql file as one transaction."""
    sql = Path(path).read_text(encoding="utf-8")
    conn.execute(sql)
    conn.commit()


def log_step(conn, run_id, step, source, rows_in, rows_out, rows_rejected, started_at, status, message=""):
    """Write one row to etl.run_log."""
    conn.execute(
        """
        INSERT INTO etl.run_log
            (run_id, step, source, rows_in, rows_out, rows_rejected, started_at, status, message)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (run_id, step, source, rows_in, rows_out, rows_rejected, started_at, status, message),
    )
    conn.commit()


if __name__ == "__main__":
    with get_connection() as conn:
        version = conn.execute("select version()").fetchone()[0]
        print(version)