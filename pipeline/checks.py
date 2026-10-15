"""Run every data check in sql/checks. A check passes when its query returns no rows."""
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from pipeline.db import get_connection, log_step

CHECKS_DIR = Path("sql/checks")


def run_checks():
    run_id = uuid.uuid4()
    failures = 0
    with get_connection() as conn:
        for path in sorted(CHECKS_DIR.glob("*.sql")):
            started = datetime.now(timezone.utc)
            rows = conn.execute(path.read_text(encoding="utf-8")).fetchall()
            conn.rollback()  # checks only read, so end the transaction without saving anything
            if rows:
                failures += 1
                print(f"FAIL ({len(rows)} rows)  {path.name}")
                for row in rows[:5]:
                    print(f"    {row}")
                log_step(conn, run_id, "check", path.name, None, len(rows), None, started, "failed",
                         f"{len(rows)} problem rows")
            else:
                print(f"PASS  {path.name}")
                log_step(conn, run_id, "check", path.name, None, 0, None, started, "ok")

    if failures:
        print(f"{failures} check(s) failed")
        sys.exit(1)
    print("All checks passed")