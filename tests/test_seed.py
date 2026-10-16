import csv
import re
from pathlib import Path

SEED = Path("seeds/district_to_council.csv")
CODE = re.compile(r"^(E0[6-9]|W06)\d{6}$")


def read_rows():
    with open(SEED, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_header():
    with open(SEED, encoding="utf-8") as f:
        assert f.readline().strip() == "district_name,council_code,council_name,note"


def test_codes_look_like_english_council_codes():
    bad = [row["council_code"] for row in read_rows() if not CODE.match(row["council_code"])]
    assert bad == []


def test_no_district_twice():
    names = [row["district_name"] for row in read_rows()]
    assert len(names) == len(set(names))


def test_district_names_in_capitals():
    lower = [row["district_name"] for row in read_rows() if row["district_name"] != row["district_name"].upper()]
    assert lower == []