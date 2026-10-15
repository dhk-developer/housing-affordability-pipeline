"""Time COPY against pandas to_sql on the same 100,000 rows.

Usage (from the project folder): python -m scripts.time_load data/raw/pp-2023.csv
"""
import sys
import time
from itertools import islice
from pathlib import Path

import pandas as pd

from pipeline.db import get_connection, get_engine
from pipeline.load_raw import COLUMNS

ROWS = 100_000


def main(source):
    sample = Path("data/sample_100k.csv")
    with open(source, encoding="utf-8", errors="replace") as f, open(sample, "w", encoding="utf-8") as out:
        out.writelines(islice(f, ROWS))

    column_defs = ", ".join(f"{column} text" for column in COLUMNS)
    with get_connection() as conn:
        conn.execute("DROP TABLE IF EXISTS raw.timing_copy, raw.timing_to_sql")
        conn.execute(f"CREATE TABLE raw.timing_copy ({column_defs})")
        conn.commit()

        start = time.perf_counter()
        with conn.cursor() as cur:
            with cur.copy("COPY raw.timing_copy FROM STDIN WITH (FORMAT csv)") as copy:
                copy.write(sample.read_bytes())
        conn.commit()
        copy_seconds = time.perf_counter() - start

    df = pd.read_csv(sample, header=None, names=COLUMNS, dtype=str, keep_default_na=False)
    start = time.perf_counter()
    df.to_sql("timing_to_sql", get_engine(), schema="raw", index=False, chunksize=10_000)
    to_sql_seconds = time.perf_counter() - start

    print(f"COPY:   {copy_seconds:6.2f} s")
    print(f"to_sql: {to_sql_seconds:6.2f} s  ({to_sql_seconds / copy_seconds:.0f}x slower)")

    with get_connection() as conn:
        conn.execute("DROP TABLE raw.timing_copy, raw.timing_to_sql")
    sample.unlink()


if __name__ == "__main__":
    main(sys.argv[1])