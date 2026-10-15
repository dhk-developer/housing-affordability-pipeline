"""Match Land Registry district names to ONS council codes."""
import csv
import re
from pathlib import Path


def normalise_council_name(name):
    """Reduce a council name to a form both sources agree on.

    "Bristol, City of", "CITY OF BRISTOL" and " bristol " all become "BRISTOL".
    """
    name = name.upper().replace("&", " AND ")
    name = re.sub(r"[^A-Z ]", " ", name)  # commas, full stops, hyphens, apostrophes -> spaces
    name = " ".join(name.split())         # squash runs of spaces and trim the ends
    name = re.sub(r"^(CITY|COUNTY) OF ", "", name)
    name = re.sub(r" (CITY|COUNTY) OF$", "", name)
    return name


def read_seed(seed_path):
    """Read the hand-made mapping file into {district_name: (council_code, council_name)}."""
    with open(seed_path, newline="", encoding="utf-8") as f:
        return {
            row["district_name"].strip(): (row["council_code"].strip(), row["council_name"].strip())
            for row in csv.DictReader(f)
        }


def build_district_map(conn, seed_path):
    """Rebuild staging.district_map. Returns the districts that still have no council."""
    districts = [row[0] for row in conn.execute("SELECT DISTINCT district FROM raw.price_paid")]
    councils = conn.execute("SELECT DISTINCT la_code, la_name FROM staging.ons_ratio").fetchall()
    by_name = {normalise_council_name(name): (code, name) for code, name in councils}
    seed = read_seed(seed_path) if Path(seed_path).exists() else {}

    matched = []
    unmatched = []
    for district in districts:
        if district in seed:
            code, name = seed[district]
            matched.append((district, code, name, "manual"))
        elif normalise_council_name(district) in by_name:
            code, name = by_name[normalise_council_name(district)]
            matched.append((district, code, name, "auto"))
        else:
            unmatched.append(district)

    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS staging.district_map")
        cur.execute(
            """
            CREATE TABLE staging.district_map (
                district_name text PRIMARY KEY,
                council_code  text NOT NULL,
                council_name  text NOT NULL,
                match_type    text NOT NULL CHECK (match_type IN ('auto', 'manual'))
            )
            """
        )
        cur.executemany("INSERT INTO staging.district_map VALUES (%s, %s, %s, %s)", matched)
    conn.commit()

    print(f"district map: {len(matched)} matched, {len(unmatched)} unmatched")
    return sorted(unmatched)