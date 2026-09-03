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

CHUNK_SIZE = 2000    # characters (~500 tokens for MiniLM-L6)
CHUNK_OVERLAP = 200  # characters


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

        print(f"  {scheme_slug}: {len(chunks)} chunks → {out_path}")
        all_chunks.extend(chunks)

    return all_chunks


if __name__ == "__main__":
    print("=== Phase 2: Chunking ===")
    chunks = chunk_all()
    print(f"\nTotal chunks: {len(chunks)}")
