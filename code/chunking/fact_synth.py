"""
Fact Synthesizer — reads raw text files and produces one dense "fact sheet"
chunk per scheme, containing ONLY the key factual data points.

These synthetic chunks dramatically improve retrieval accuracy because they
are clean and semantically dense (no navigation noise).
"""
import json
import os
import re

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw")
CHUNKS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "chunks")


def _first_match(text: str, *patterns: str) -> str:
    """Return the first non-empty capture from any of the patterns."""
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return ""


def _parse_header(filepath: str) -> dict:
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
    with open(filepath, encoding="utf-8") as fh:
        content = fh.read()
    sep = "=" * 60
    idx = content.find(sep)
    return content[idx + len(sep):].strip() if idx != -1 else content


def extract_facts(scheme_slug: str, filepath: str) -> dict | None:
    """
    Extract key facts from a raw scheme text file.
    Returns a chunk dict or None if extraction fails.
    """
    meta = _parse_header(filepath)
    body = _read_body(filepath)
    title = meta["title"]

    # --- Expense ratio ---
    expense_ratio = _first_match(
        body,
        r"Expense ratio[:\s]+(\d[\d.]+%)",
        r"Expense ratio\s*\n([^\n]{2,20})",
    )

    # --- Minimum SIP ---
    min_sip = _first_match(
        body,
        r"Min(?:imum)?\.?\s+(?:for\s+)?SIP[:\s]+[^\d]*([\d,]+)",
        r"Minimum SIP[^\d]*([\d,]+)",
        r"Min\. for SIP\s*\n[^\d]*([\d,]+)",
        r"SIP\s+[\u20b9\u20B9]?\s*([\d,]+)",
    )

    # --- Exit load ---
    exit_load = _first_match(
        body,
        r"Exit load of ([^\n.;]+)",
        r"Exit Load[:\s]+([^\n]+)",
        r"exit load[:\s]+([^\n]+)",
    )

    # --- AUM ---
    aum = _first_match(
        body,
        r"(?:Fund size|AUM)\s*\(?AUM\)?\s*:?\s*[\u20b9\u20B9]?\s*([\d,]+(?:\.\d+)?\s*Cr)",
        r"AUM[:\s]+[\u20b9\u20B9]?\s*([\d,]+(?:\.\d+)?\s*Cr)",
        r"Asset Under Management\(AUM\) of [^\d]*([\d,]+(?:\.\d+)?\s*Cr)",
    )

    # --- Benchmark ---
    benchmark = _first_match(
        body,
        r"Fund benchmark\s*\n([^\n]+)",
        r"Benchmark[:\s]+([^\n]+)",
        r"benchmark(?:ed)? (?:against|is)[:\s]+([^\n]+)",
    )

    # --- Risk ---
    risk = _first_match(
        body,
        r"rated\s+(Very High|High|Moderate|Low to Moderate|Low)\s+risk",
        r"risk[:\s]+(Very High|High|Moderate|Low to Moderate|Low)",
        r"Riskometer[:\s]+(Very High|High|Moderate|Low to Moderate|Low)",
    )

    # --- NAV ---
    nav = _first_match(
        body,
        r"NAV[:\s]+(?:as of [^:]+:)?\s*[^\d]*([\d,]+(?:\.\d+)?)",
        r"Latest NAV[^\d]*([\d,]+(?:\.\d+)?)",
    )

    # --- Lock-in (ELSS only) ---
    lock_in = _first_match(
        body,
        r"lock.in(?:\s+period)?[:\s]+([^\n.;]+)",
        r"Lock.In Period[:\s]+([^\n]+)",
        r"(3.year lock.in)",
    )
    # ELSS funds always have a 3-year lock-in; mark it if detected
    if not lock_in and ("elss" in scheme_slug or "tax saver" in title.lower()):
        lock_in = "3 years (mandatory, ELSS)"

    # --- Minimum Lumpsum ---
    min_lumpsum = _first_match(
        body,
        r"Min(?:imum)?\.?\s+(?:for\s+)?Lumpsum[:\s]+[^\d]*([\d,]+)",
        r"Minimum Lumpsum[^\d]*([\d,]+)",
        r"Minimum Lumpsum Investment is [^\d]*([\d,]+)",
    )

    # --- Build fact sheet text ---
    facts_lines = [f"{title} — Key Facts"]
    if expense_ratio:
        facts_lines.append(f"Expense ratio: {expense_ratio}")
    if min_sip:
        facts_lines.append(f"Minimum SIP: Rs {min_sip}")
    if min_lumpsum:
        facts_lines.append(f"Minimum Lumpsum: Rs {min_lumpsum}")
    if exit_load:
        facts_lines.append(f"Exit load: {exit_load}")
    if aum:
        facts_lines.append(f"Fund size (AUM): Rs {aum}")
    if benchmark:
        facts_lines.append(f"Benchmark: {benchmark}")
    if risk:
        facts_lines.append(f"Risk level (Riskometer): {risk}")
    if nav:
        facts_lines.append(f"NAV (latest): Rs {nav}")
    if lock_in:
        facts_lines.append(f"Lock-in period: {lock_in}")

    if len(facts_lines) <= 1:
        return None  # nothing extracted

    facts_text = "\n".join(facts_lines)

    return {
        "id": f"{scheme_slug}_factsheet",
        "scheme": scheme_slug,
        "title": title,
        "source_url": meta["url"],
        "fetched_at": meta["fetched_at"],
        "chunk_index": -1,  # -1 = synthetic fact sheet
        "text": facts_text,
    }


def synthesize_all(raw_dir: str = RAW_DIR, chunks_dir: str = CHUNKS_DIR) -> list[dict]:
    """
    For each raw file, extract a fact-sheet chunk and PREPEND it to the
    existing chunks JSON (so it's always available for retrieval).
    Returns all synthetic fact-sheet chunks.
    """
    synth_chunks = []
    for filename in sorted(os.listdir(raw_dir)):
        if not filename.endswith(".txt"):
            continue
        scheme_slug = filename[:-4]
        filepath = os.path.join(raw_dir, filename)
        chunk = extract_facts(scheme_slug, filepath)
        if chunk:
            # Load existing chunks and prepend the fact sheet
            json_path = os.path.join(chunks_dir, f"{scheme_slug}.json")
            if os.path.exists(json_path):
                with open(json_path, encoding="utf-8") as fh:
                    existing = json.load(fh)
            else:
                existing = []
            # Remove old factsheet if re-running
            existing = [c for c in existing if c.get("chunk_index") != -1]
            combined = [chunk] + existing
            with open(json_path, "w", encoding="utf-8") as fh:
                json.dump(combined, fh, ensure_ascii=False, indent=2)
            synth_chunks.append(chunk)
            print(f"  Fact sheet for {scheme_slug}:")
            print(f"    {chunk['text'].replace(chr(10), ' | ')[:200]}")
    return synth_chunks


if __name__ == "__main__":
    print("=== Fact Synthesis ===")
    chunks = synthesize_all()
    print(f"\nCreated {len(chunks)} fact-sheet chunks.")
