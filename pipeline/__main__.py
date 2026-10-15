"""Command-line entry point.

Usage:
    python -m pipeline run --years 2019-2024
    python -m pipeline check
"""
import argparse
import uuid
from pathlib import Path

from pipeline.db import get_connection, run_sql_file
from pipeline.extract import ONS_URL, PRICE_PAID_URL, download
from pipeline.load_raw import load_ons, load_price_paid

from pipeline.councils import build_district_map
from pipeline.transform import stage_sales

SEED_FILE = Path("seeds/district_to_council.csv")

RAW_DIR = Path("data/raw")
SQL_DIR = Path("sql")


def parse_years(text):
    """Turn "2019-2024" into [2019, 2020, 2021, 2022, 2023, 2024]."""
    parts = text.split("-")
    if len(parts) != 2 or not all(part.isdigit() for part in parts):
        raise ValueError(f"expected a range like 2019-2024, got {text!r}")
    start, end = int(parts[0]), int(parts[1])
    if start > end:
        raise ValueError(f"start year {start} is after end year {end}")
    return list(range(start, end + 1))


def run(years):
    run_id = uuid.uuid4()
    print(f"Run {run_id} for {years[0]}-{years[-1]}")

    price_files = [download(PRICE_PAID_URL.format(year=year), RAW_DIR / f"pp-{year}.csv") for year in years]
    ons_file = download(ONS_URL, RAW_DIR / "ons_affordability.xlsx")

    with get_connection() as conn:
        for name in ["001_schemas.sql", "010_raw.sql"]:
            run_sql_file(conn, SQL_DIR / name)
        for path in price_files:
            load_price_paid(conn, path, run_id)
        load_ons(conn, ons_file, run_id)
                run_sql_file(conn, SQL_DIR / "015_staging_ons.sql")
        unmatched = build_district_map(conn, SEED_FILE)
        if unmatched:
            print("These districts need a row in the seed file:")
            for district in unmatched:
                print(f"  {district}")
            raise SystemExit(1)

        stage_sales(conn, run_id, SQL_DIR / "020_staging.sql")


def main():
    parser = argparse.ArgumentParser(prog="pipeline", description="England housing affordability pipeline")
    commands = parser.add_subparsers(dest="command", required=True)

    run_parser = commands.add_parser("run", help="download, load and transform the data")
    run_parser.add_argument("--years", type=parse_years, required=True, help="a range such as 2019-2024")

    commands.add_parser("check", help="run the data checks")

    args = parser.parse_args()
    if args.command == "run":
        run(args.years)
    elif args.command == "check":
        print("No checks yet")


if __name__ == "__main__":
    main()