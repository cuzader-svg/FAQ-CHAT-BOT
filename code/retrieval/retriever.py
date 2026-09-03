"""
Phase 5 — Retrieval Logic
Gates: PII → refuse | Advice → refuse | Returns → refuse | Facts → RAG + Mistral
"""
import os
import re
import sys
from dataclasses import dataclass

from dotenv import load_dotenv
from mistralai import Mistral

load_dotenv()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MISTRAL_MODEL = "mistral-small-latest"

_ADVICE_PATTERNS = re.compile(
    r"\b(should i|should we|buy|sell|invest in|worth buying|best fund|"
    r"recommend|portfolio|switch to|top fund|which fund|better fund)\b",
    re.IGNORECASE,
)
_RETURNS_PATTERNS = re.compile(
    r"\b(return[s]?|cagr|performance|outperform|grew by|profit|how much.{0,20}earn|"
    r"alpha|nav growth|past.{0,10}year)\b",
    re.IGNORECASE,
)
_PII_PATTERNS = re.compile(
    r"[A-Z]{5}[0-9]{4}[A-Z]"                            # PAN
    r"|\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b"               # Aadhaar
    r"|\b[6-9]\d{9}\b"                                   # Indian mobile
    r"|[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"  # email
    r"|\b\d{9,18}\b"                                     # account-like numbers
)

# Fallback URLs used in refusals
_SCHEME_URL_MAP = {
    "large_cap":   "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
    "flexi_cap":   "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth",
    "elss":        "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
    "small_cap":   "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
    "balanced":    "https://groww.in/mutual-funds/hdfc-balanced-advantage-fund-direct-growth",
}
_DEFAULT_SCHEME_URL = "https://groww.in/mutual-funds"

SYSTEM_PROMPT = """You are a facts-only mutual fund FAQ assistant for Groww.

Rules you must follow at all times:
1. Answer ONLY from the provided Context chunks. Do not use any prior knowledge.
2. Keep your answer to ≤ 3 sentences.
3. End every answer with exactly two lines:
   Source: <the source_url from the most relevant chunk>
   Last updated from sources: <the fetched_at date from that chunk>
4. If the answer is not in the context, say:
   "This information is not available in my current sources. Please visit the official scheme page."
   Then still add the Source and Last updated lines using the best matching chunk URL.
5. Never recommend, advise, or rank funds.
6. Never compute, quote, or compare returns, CAGR, or past performance.
7. Never repeat or acknowledge any personal data (PAN, Aadhaar, phone, email).
"""


@dataclass
class Answer:
    text: str
    source_url: str
    fetched_at: str
    refused: bool = False


def _detect_scheme_url(query: str) -> str:
    q = query.lower()
    if "large cap" in q or "large-cap" in q:
        return _SCHEME_URL_MAP["large_cap"]
    if "flexi" in q or "flexi cap" in q:
        return _SCHEME_URL_MAP["flexi_cap"]
    if "elss" in q or "tax saver" in q:
        return _SCHEME_URL_MAP["elss"]
    if "small cap" in q or "small-cap" in q:
        return _SCHEME_URL_MAP["small_cap"]
    if "balanced" in q or "advantage" in q:
        return _SCHEME_URL_MAP["balanced"]
    return _DEFAULT_SCHEME_URL


def ask(query: str) -> Answer:
    """
    Main entry point.
    1. Gate checks (PII → advice → returns).
    2. Retrieve top-4 chunks from Chroma.
    3. Call Mistral with grounded prompt.
    4. Return structured Answer.
    """
    # --- Gate 1: PII ---
    if _PII_PATTERNS.search(query):
        return Answer(
            text=(
                "I cannot process personal information. "
                "Please do not share PAN, Aadhaar, account numbers, phone numbers, "
                "or email addresses. Ask a factual question about the schemes instead."
            ),
            source_url=_DEFAULT_SCHEME_URL,
            fetched_at="",
            refused=True,
        )

    # --- Gate 2: Advice ---
    if _ADVICE_PATTERNS.search(query):
        url = _detect_scheme_url(query)
        return Answer(
            text=(
                "I can only share factual information about these HDFC schemes on Groww. "
                "For investment decisions, please consult a SEBI-registered financial advisor "
                "or visit the official scheme page."
            ),
            source_url=url,
            fetched_at="",
            refused=True,
        )

    # --- Gate 3: Returns ---
    if _RETURNS_PATTERNS.search(query):
        url = _detect_scheme_url(query)
        return Answer(
            text=(
                "I do not calculate or compare returns. "
                "Please refer to the official scheme page on Groww for performance data."
            ),
            source_url=url,
            fetched_at="",
            refused=True,
        )

    # --- Factual RAG path ---
    from embedding.embedder import embed_query
    from vectordb.store import query_collection

    query_vec = embed_query(query)
    results = query_collection(query_vec, n_results=4)

    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]

    if not docs:
        return Answer(
            text="No relevant information found in my sources. Please visit groww.in/mutual-funds.",
            source_url=_DEFAULT_SCHEME_URL,
            fetched_at="",
            refused=True,
        )

    # Build context block
    context_parts = []
    for i, (doc, meta) in enumerate(zip(docs, metas)):
        context_parts.append(
            f"[Chunk {i + 1}]\nScheme: {meta.get('title', '')}\n"
            f"Source URL: {meta.get('source_url', '')}\n"
            f"Fetched: {meta.get('fetched_at', '')}\n\n{doc}"
        )
    context = "\n\n---\n\n".join(context_parts)

    # Primary source = first (most relevant) chunk
    primary_meta = metas[0]
    source_url = primary_meta.get("source_url", _DEFAULT_SCHEME_URL)
    fetched_at = primary_meta.get("fetched_at", "")

    # Call Mistral
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        return Answer(
            text="MISTRAL_API_KEY is not set. Please add it to your .env file.",
            source_url=source_url,
            fetched_at=fetched_at,
            refused=True,
        )

    client = Mistral(api_key=api_key)
    user_message = f"{query}\n\nContext:\n{context}"

    response = client.chat.complete(
        model=MISTRAL_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        max_tokens=300,
        temperature=0.1,
    )

    answer_text = response.choices[0].message.content.strip()

    return Answer(text=answer_text, source_url=source_url, fetched_at=fetched_at)


# ---------------------------------------------------------------------------
# CLI entry point:  PYTHONPATH=code python -m retrieval "<query>"
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What is the expense ratio of HDFC Large Cap?"
    print(f"\nQuery: {query}\n{'-' * 60}")
    result = ask(query)
    print(result.text)
    if result.source_url:
        print(f"\nSource: {result.source_url}")
    if result.fetched_at:
        print(f"Last updated from sources: {result.fetched_at}")
