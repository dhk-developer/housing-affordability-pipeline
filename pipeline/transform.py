"""Build staging.sales and prove no rows went missing on the way."""
from datetime import datetime, timezone

from pipeline.db import log_step, run_sql_file


def stage_sales(conn, run_id, sql_path):
    """Run the staging SQL, then check raw = kept + rejected for every file."""
    started = datetime.now(timezone.utc)
    run_sql_file(conn, sql_path)

    counts = conn.execute(
        """
        SELECT r.source_file,
               r.rows_in,
               coalesce(s.kept, 0)     AS kept,
               coalesce(x.rejected, 0) AS rejected
        FROM (SELECT source_file, count(*) AS rows_in FROM raw.price_paid GROUP BY 1) r
        LEFT JOIN (SELECT source_file, count(*) AS kept FROM staging.sales GROUP BY 1) s USING (source_file)
        LEFT JOIN (SELECT source_file, count(*) AS rejected FROM staging.sales_rejected GROUP BY 1) x USING (source_file)
        ORDER BY 1
        """
    ).fetchall()

    problems = []
    for source_file, rows_in, kept, rejected in counts:
        ok = rows_in == kept + rejected
        log_step(conn, run_id, "staging", source_file, rows_in, kept, rejected, started,
                 "ok" if ok else "failed", "" if ok else "raw does not equal kept plus rejected")
        print(f"{source_file}: {rows_in:,} in = {kept:,} kept + {rejected:,} rejected")
        if not ok:
            problems.append(source_file)

    if problems:
        raise RuntimeError(f"staging lost rows for: {', '.join(problems)}")