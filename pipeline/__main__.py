"""Command-line entry point.

Usage:
    python -m pipeline run --years 2019-2024
    python -m pipeline check
"""
import argparse


def parse_years(text):
    """Turn "2019-2024" into [2019, 2020, 2021, 2022, 2023, 2024]."""
    parts = text.split("-")
    if len(parts) != 2 or not all(part.isdigit() for part in parts):
        raise ValueError(f"expected a range like 2019-2024, got {text!r}")
    start, end = int(parts[0]), int(parts[1])
    if start > end:
        raise ValueError(f"start year {start} is after end year {end}")
    return list(range(start, end + 1))


def main():
    parser = argparse.ArgumentParser(prog="pipeline", description="England housing affordability pipeline")
    commands = parser.add_subparsers(dest="command", required=True)

    run = commands.add_parser("run", help="download, load and transform the data")
    run.add_argument("--years", type=parse_years, required=True, help="a range such as 2019-2024")

    commands.add_parser("check", help="run the data checks")

    args = parser.parse_args()
    if args.command == "run":
        print(f"Would run for years: {args.years}")
    elif args.command == "check":
        print("No checks yet")


if __name__ == "__main__":
    main()