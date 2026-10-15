"""Load downloaded files into the raw schema, unchanged, and reconcile the counts."""
import csv
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from pipeline.db import get_engine, log_step

COLUMNS = [
    "transaction_id", "price", "date_of_transfer", "postcode", "property_type",
    "old_new", "duration", "paon", "saon", "street", "locality", "town_city",
    "district", "county", "ppd_category", "record_status",
]

YEAR_PATTERN = r"(?:19|20)\d{2}"


def count_csv_rows(path):
    """Count data rows the way COPY will read them: quoted commas and all."""
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        return sum(1 for _ in csv.reader(f))


def load_price_paid(conn, path, run_id):
    """Replace one yearly file's rows in raw.price_paid, then check none were lost."""
    path = Path(path)
    started = datetime.now(timezone.utc)
    rows_in = count_csv_rows(path)
    column_list = ", ".join(COLUMNS)
    column_defs = ", ".join(f"{column} text" for column in COLUMNS)

    with conn.cursor() as cur:
        cur.execute("DELETE FROM raw.price_paid WHERE source_file = %s", (path.name,))
        cur.execute(f"CREATE TEMP TABLE incoming ({column_defs}) ON COMMIT DROP")
        with cur.copy(f"COPY incoming ({column_list}) FROM STDIN WITH (FORMAT csv)") as copy:
            with open(path, "rb") as f:
                while chunk := f.read(1024 * 1024):
                    copy.write(chunk)
        cur.execute(
            f"INSERT INTO raw.price_paid ({column_list}, source_file) SELECT {column_list}, %s FROM incoming",
            (path.name,),
        )
        rows_out = cur.execute(
            "SELECT count(*) FROM raw.price_paid WHERE source_file = %s", (path.name,)
        ).fetchone()[0]

    if rows_out != rows_in:
        conn.rollback()
        log_step(conn, run_id, "load_raw", path.name, rows_in, rows_out, 0, started, "failed",
                 "row count in table does not match the file")
        raise RuntimeError(f"{path.name}: file has {rows_in:,} rows but the table got {rows_out:,}")

    conn.commit()
    log_step(conn, run_id, "load_raw", path.name, rows_in, rows_out, 0, started, "ok")
    print(f"{path.name}: loaded {rows_out:,} rows")


def _header_row(raw):
    """Find the heading row: the first of the top 20 rows with a code column and at least 3 year columns."""
    for i, row in raw.head(20).iterrows():
        cells = [str(c) for c in row if pd.notna(c)]
        has_code = any("code" in c.lower() for c in cells)
        years = sum(1 for c in cells if re.search(YEAR_PATTERN, c))
        if has_code and years >= 3:
            return i
    return None


def _pick_column(headers, words):
    """The first heading containing all of the given words (case ignored)."""
    for h in headers:
        if all(w in str(h).lower() for w in words):
            return h
    return None


def find_ons_tables(path):
    """Look through every sheet and pick the three local-authority median tables.

    Returns {"ons_median_price": {...}, "ons_median_earnings": {...}, "ons_ratio": {...}},
    each with the sheet name, heading row, code column and name column.
    """
    found = {}
    for sheet, raw in pd.read_excel(path, sheet_name=None, header=None, dtype=str).items():
        header = _header_row(raw)
        if header is None:
            continue  # cover, contents and notes sheets have no data table
        title = " ".join(str(c) for c in raw.iloc[:header].stack()).lower()
        if "median" not in title or "lower quartile" in title:
            continue
        if "ratio" in title:
            kind = "ons_ratio"
        elif "earnings" in title:
            kind = "ons_median_earnings"
        elif "price" in title:
            kind = "ons_median_price"
        else:
            continue

        headers = list(raw.iloc[header])
        code = _pick_column(headers, ["local authority", "code"]) or _pick_column(headers, ["code"])
        name = _pick_column(headers, ["local authority", "name"]) or _pick_column(headers, ["name"])
        rows = raw.iloc[header + 1:].dropna(how="all")
        table = {"sheet": sheet, "skiprows": header, "code": code, "name": name, "rows": len(rows)}

        # Regional and local authority tables look alike; the local authority one has the most rows.
        if kind not in found or table["rows"] > found[kind]["rows"]:
            found[kind] = table

    missing = {"ons_median_price", "ons_median_earnings", "ons_ratio"} - set(found)
    if missing:
        raise RuntimeError(f"couldn't find these tables in {path}: {sorted(missing)}")
    return found


def load_ons(conn, path, run_id):
    """Reshape each ONS table from wide (a column per year) to long, and land it in raw."""
    path = Path(path)
    engine = get_engine()
    for table, spec in find_ons_tables(path).items():
        started = datetime.now(timezone.utc)
        print(f"{table}: using sheet {spec['sheet']!r}, headings on Excel row {spec['skiprows'] + 1}")
        wide = pd.read_excel(path, sheet_name=spec["sheet"], skiprows=spec["skiprows"], dtype=str)
        wide = wide.dropna(subset=[spec["code"]])
        year_columns = [c for c in wide.columns if re.search(YEAR_PATTERN, str(c))]

        long = wide.melt(
            id_vars=[spec["code"], spec["name"]],
            value_vars=year_columns,
            var_name="year_label",
            value_name="value",
        )
        long = long.rename(columns={spec["code"]: "la_code", spec["name"]: "la_name"})
        long["year"] = long["year_label"].astype(str).str.findall(YEAR_PATTERN).str[-1]
        long["source_file"] = f"{path.name}:{spec['sheet']}"

        long.to_sql(table, engine, schema="raw", if_exists="replace", index=False)

        rows_in = len(wide) * len(year_columns)
        log_step(conn, run_id, "load_raw", f"{path.name}:{spec['sheet']}", rows_in, len(long), 0, started, "ok")
        print(f"{table}: {len(wide)} councils x {len(year_columns)} years = {len(long):,} rows")