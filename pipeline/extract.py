"""Download source files safely: skip complete copies, write to .part, retry."""
import time
from pathlib import Path

import requests

PRICE_PAID_URL = "https://price-paid-data.publicdata.landregistry.gov.uk/pp-{year}.csv"
ONS_URL = (
    "https://www.ons.gov.uk/file?uri=/peoplepopulationandcommunity/housing/datasets/"
    "ratioofhousepricetoresidencebasedearningslowerquartileandmedian/current/"
    "aff2ratioofhousepricetoresidencebasedearnings.xlsx"
)

RETRY_WAITS = [2, 4, 8]  # seconds to wait after the 1st, 2nd and 3rd failure
CHUNK_SIZE = 1024 * 1024  # 1 MB


def remote_size(url):
    """Ask the server how big the file is without downloading it. None if it won't say."""
    try:
        response = requests.head(url, allow_redirects=True, timeout=30)
        response.raise_for_status()
    except requests.RequestException:
        return None
    size = response.headers.get("Content-Length")
    return int(size) if size else None


def download(url, dest):
    """Download url to dest unless a complete copy is already there. Returns dest."""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")

    expected = remote_size(url)
    if expected is not None and dest.exists() and dest.stat().st_size == expected:
        print(f"{dest.name}: already downloaded, skipping")
        return dest

    for attempt, wait in enumerate(RETRY_WAITS, start=1):
        try:
            with requests.get(url, stream=True, timeout=60) as response:
                response.raise_for_status()
                with open(part, "wb") as f:
                    for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                        f.write(chunk)
            if expected is not None and part.stat().st_size != expected:
                raise requests.ConnectionError("download ended early")
            part.replace(dest)
            print(f"{dest.name}: downloaded {dest.stat().st_size:,} bytes")
            return dest
        except requests.HTTPError as err:
            if err.response.status_code < 500:
                raise  # a 404 means the URL is wrong, so retrying won't help
            problem = err
        except (requests.ConnectionError, requests.Timeout) as err:
            problem = err
        print(f"{dest.name}: attempt {attempt} failed ({problem}), retrying in {wait}s")
        time.sleep(wait)

    raise RuntimeError(f"gave up on {url} after {len(RETRY_WAITS)} attempts")