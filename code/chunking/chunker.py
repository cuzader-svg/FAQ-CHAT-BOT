"""
Phase 2 — Chunking
Reads raw text files, splits into overlapping chunks, attaches metadata,
and saves JSON to data/chunks/<scheme_slug>.json.
"""
import json
import os
import re

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw")
CHUNKS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "chunks")

CHUNK_SIZE = 500     # characters — small enough to isolate individual facts
CHUNK_OVERLAP = 75   # characters

# Lines that are obviously navigation/UI junk to drop
_JUNK_LINE = re.compile(
    r"^(1D|1M|6M|1Y|3Y|5Y|All|Blog|Credit|Pricing|Compare|"
    r"Start SIP|Invest now|View details|Education|Experience|"
    r"Return calculator|Lumpsum calculator|SWP calculator|Goal planner|SIP calculator|"
    r"Monthly SIP|One time|Monthly investment|Over the past|Total investment|"
    r"Would.ve become|Historic returns|Returns|Brokerage.*charges|"
    r"Filter based|Explore all|Download|Read more|Show more|Load more|"
    r"\+|\-|%|\d{1,2}$)$",
    re.IGNORECASE,
)

# Known fact labels whose next line is their value
_FACT_LABELS = {
    "expense ratio", "min. for sip", "minimum sip", "minimum lumpsum",
    "exit load", "fund size (aum)", "aum", "rating",
    "benchmark", "risk", "riskometer", "lock-in period", "lock in",
    "category", "fund type", "launch date", "fund manager",
    "nav", "min. for lumpsum",
}


def _clean_body(text: str) -> str:
    """
    Consolidate label-value pairs and drop navigation noise lines.
    E.g. 'Expense ratio\\n1.02%' → 'Expense ratio: 1.02%'
    """
    lines = text.split("\n")
    cleaned = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        # Drop obvious UI/nav junk
        if _JUNK_LINE.match(line):
            i += 1
            continue
        # Join label + value on next line
        if line.lower() in _FACT_LABELS and i + 1 < len(lines):
            val = lines[i + 1].strip()
            if val and len(val) < 120:
                cleaned.append(f"{line}: {val}")
                i += 2
                continue
        cleaned.append(line)
        i += 1
    result = "\n".join(cleaned)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


def _parse_header(filepath: str) -> dict:
    """Extract SOURCE_URL / SCHEME / FETCHED_AT header lines from raw file."""
    meta = {"url": "", "title": "", "fetched_at": ""}
    with open(filepath, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("SOURCE_URL:"):
                meta["url"] = line.split(":", 1)[1].strip()
            elif line.startswith("SCHEME:"):
                meta["title"] = line.split(":", 1)[1].strip()
            elif line.startswith("FETCHED_AT:"):
                meta["fetched_at"] = line.split(":", 1)[1].strip()
            elif line.startswith("=" * 10):
                break
    return meta


def _read_body(filepath: str) -> str:
    """Return the text body after the '======' separator."""
    with open(filepath, encoding="utf-8") as fh:
        content = fh.read()
    sep = "=" * 60
    idx = content.find(sep)
    if idx == -1:
        return content
    return content[idx + len(sep):].strip()


def _split_chunks(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Sliding-window character-level chunker."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end].strip())
        start += size - overlap
    # drop empty trailing chunks
    return [c for c in chunks if len(c) > 50]


def chunk_file(filepath: str, scheme_slug: str) -> list[dict]:
    """Return list of chunk dicts for a single raw file."""
    meta = _parse_header(filepath)
    body = _read_body(filepath)
    body = _clean_body(body)          # consolidate facts, drop nav noise
    raw_chunks = _split_chunks(body)

    chunks = []
    for i, text in enumerate(raw_chunks):
        chunks.append(
            {
                "id": f"{scheme_slug}_chunk_{i:04d}",
                "scheme": scheme_slug,
                "title": meta["title"],
                "source_url": meta["url"],
                "fetched_at": meta["fetched_at"],
                "chunk_index": i,
                "text": text,
            }
        )
    return chunks


def chunk_all(raw_dir: str = RAW_DIR, chunks_dir: str = CHUNKS_DIR) -> list[dict]:
    """Chunk all files in raw_dir and save to chunks_dir."""
    os.makedirs(chunks_dir, exist_ok=True)
    all_chunks = []

    for filename in sorted(os.listdir(raw_dir)):
        if not filename.endswith(".txt"):
            continue
        scheme_slug = filename[:-4]
        filepath = os.path.join(raw_dir, filename)
        chunks = chunk_file(filepath, scheme_slug)

        out_path = os.path.join(chunks_dir, f"{scheme_slug}.json")
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(chunks, fh, ensure_ascii=False, indent=2)

        print(f"  {scheme_slug}: {len(chunks)} chunks -> {out_path}")
        all_chunks.extend(chunks)

    return all_chunks


if __name__ == "__main__":
    print("=== Phase 2: Chunking ===")
    chunks = chunk_all()
    print(f"\nTotal chunks: {len(chunks)}")
