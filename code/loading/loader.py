"""
Phase 1 — Data Loading
Fetches each of the 5 public Groww HDFC scheme pages, extracts visible text,
and saves plaintext to data/raw/<scheme_slug>.txt.
"""
import os
import re
import time
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Corpus — exactly 5 public Groww URLs. Do not add any others.
# ---------------------------------------------------------------------------
CORPUS = [
    {
        "scheme": "hdfc_large_cap",
        "title": "HDFC Large Cap Fund Direct Growth",
        "url": "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
    },
    {
        "scheme": "hdfc_flexi_cap",
        "title": "HDFC Flexi Cap Fund Direct Growth",
        "url": "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth",
    },
    {
        "scheme": "hdfc_elss",
        "title": "HDFC ELSS Tax Saver Fund Direct Plan Growth",
        "url": "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
    },
    {
        "scheme": "hdfc_small_cap",
        "title": "HDFC Small Cap Fund Direct Growth",
        "url": "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
    },
    {
        "scheme": "hdfc_balanced_advantage",
        "title": "HDFC Balanced Advantage Fund Direct Growth",
        "url": "https://groww.in/mutual-funds/hdfc-balanced-advantage-fund-direct-growth",
    },
]

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# Tags to remove before extracting text
_REMOVE_TAGS = {"script", "style", "nav", "footer", "header", "noscript", "iframe", "svg"}


def _extract_text(html: str) -> str:
    """Return visible text from HTML, stripping nav/script/style."""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup.find_all(_REMOVE_TAGS):
        tag.decompose()
    text = soup.get_text(separator="\n")
    # collapse excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def load_all(raw_dir: str = RAW_DIR, delay: float = 1.5) -> list[dict]:
    """
    Fetch all corpus pages and save to raw_dir.
    Returns list of {scheme, title, url, fetched_at, filepath}.
    """
    os.makedirs(raw_dir, exist_ok=True)
    results = []
    for entry in CORPUS:
        print(f"  Fetching: {entry['title']} ...")
        try:
            resp = requests.get(entry["url"], headers=HEADERS, timeout=20)
            resp.raise_for_status()
        except requests.RequestException as exc:
            print(f"    ERROR: {exc}")
            continue

        fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        text = _extract_text(resp.text)

        filename = f"{entry['scheme']}.txt"
        filepath = os.path.join(raw_dir, filename)
        with open(filepath, "w", encoding="utf-8") as fh:
            fh.write(f"SOURCE_URL: {entry['url']}\n")
            fh.write(f"SCHEME: {entry['title']}\n")
            fh.write(f"FETCHED_AT: {fetched_at}\n")
            fh.write("=" * 60 + "\n\n")
            fh.write(text)

        results.append(
            {
                "scheme": entry["scheme"],
                "title": entry["title"],
                "url": entry["url"],
                "fetched_at": fetched_at,
                "filepath": filepath,
            }
        )
        print(f"    Saved → {filepath}  ({len(text):,} chars)")
        time.sleep(delay)

    return results


if __name__ == "__main__":
    print("=== Phase 1: Data Loading ===")
    records = load_all()
    print(f"\nLoaded {len(records)}/{len(CORPUS)} pages.")
