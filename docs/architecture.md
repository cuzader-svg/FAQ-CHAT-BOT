# Architecture — Groww MF FAQ RAG Chatbot

## Overview

A 6-phase pipeline: fetch public pages → chunk text → embed locally → persist in
Chroma → retrieve relevant chunks at query time → generate grounded answer via Mistral.

```
[5 Groww HTML pages]
        │
        ▼
 Phase 1: Data Loading      code/loading/loader.py
        │  fetch HTML, extract visible text, save to data/raw/
        ▼
 Phase 2: Chunking          code/chunking/chunker.py
        │  split into ~500-token chunks with 50-token overlap
        │  attach metadata: source_url, scheme, title, fetched_at
        │  save JSON to data/chunks/
        ▼
 Phase 3: Embedding         code/embedding/embedder.py
        │  sentence-transformers/all-MiniLM-L6-v2 (local, no API)
        │  produces 384-dim vectors
        ▼
 Phase 4: Vector Store      code/vectordb/store.py
        │  persist to data/vectordb/ via ChromaDB
        │  collection: "groww_mf_faq"
        ▼
 Phase 5: Retrieval Logic   code/retrieval/retriever.py
        │  embed query → cosine similarity → top-4 chunks
        │  pre-filter gates:
        │    • PII gate  → refuse, no retrieval
        │    • Advice gate (buy/sell/should I/best fund/portfolio) → polite refuse
        │    • Returns gate (CAGR/returns/outperform) → point to scheme page
        │  grounded Mistral prompt:
        │    answer ONLY from retrieved chunks, ≤3 sentences,
        │    one Source: URL, Last updated from sources: YYYY-MM-DD
        ▼
 Phase 6: Retrieval Testing  (CLI + Streamlit UI)
        │  code/ui/app.py   → Streamlit frontend
        └─ PYTHONPATH=code python -m retrieval "<query>"  → CLI
```

---

## Phase 1 — Data Loading

**File:** `code/loading/loader.py`

- Input: list of 5 (scheme_name, url) tuples from a config
- Fetch each URL with `requests` + `BeautifulSoup`; extract text from `<body>`
- Strip nav, footer, script, style tags
- Save plaintext to `data/raw/<scheme_slug>.txt` with header metadata
- Output: list of `{scheme, url, fetched_at, text}` dicts

---

## Phase 2 — Chunking

**File:** `code/chunking/chunker.py`

- Input: files from `data/raw/`
- Chunk strategy: character-based split at ~2000 chars, 200-char overlap
  (maps to ~500 tokens for MiniLM's 512-token limit)
- Each chunk: `{id, scheme, source_url, title, fetched_at, text}`
- Save as `data/chunks/<scheme_slug>.json`

---

## Phase 3 — Embedding

**File:** `code/embedding/embedder.py`

- Model: `sentence-transformers/all-MiniLM-L6-v2` (downloaded on first run, cached)
- Encode all chunk texts → 384-dim float32 vectors
- Output stored via ChromaDB (Phase 4 owns persistence)

---

## Phase 4 — Vector Store

**File:** `code/vectordb/store.py`

- ChromaDB client with `persist_directory="data/vectordb"`
- Collection: `"groww_mf_faq"`
- Upsert: `{id, embedding, document (chunk text), metadata}`
- Metadata keys stored: `scheme`, `source_url`, `title`, `fetched_at`
- Committed to git so Render never needs to re-ingest

---

## Phase 5 — Retrieval Logic

**File:** `code/retrieval/retriever.py`

```
query
  │
  ├─ PII regex check  (PAN: [A-Z]{5}[0-9]{4}[A-Z], Aadhaar: \b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b, phone, email)
  │     → "I cannot process personal information. Please do not share PAN, Aadhaar,
  │        account numbers, or contact details."
  │
  ├─ Advice keyword check  (buy, sell, should i, best fund, recommend, portfolio, invest in)
  │     → "I can only share factual information about these schemes. For investment
  │        decisions, please consult a SEBI-registered financial advisor.
  │        Source: <closest scheme URL>"
  │
  ├─ Returns keyword check  (returns?, cagr, performance, outperform, grew by, profit)
  │     → "I don't calculate or compare returns. Please refer to the official scheme
  │        page for performance data.  Source: <scheme URL>"
  │
  └─ Factual path
       embed query → Chroma top-4
       → Mistral API (mistral-small-latest)
            system prompt: answer only from context, ≤3 sentences,
                           Source: <URL>, Last updated from sources: <date>
            user: "<query>\n\nContext:\n<chunks>"
       → return answer + source_url + fetched_at
```

**Mistral model:** `mistral-small-latest` (cheapest, fast enough for a prototype)

---

## Phase 6 — Retrieval Testing & UI

**CLI:**
```
PYTHONPATH=code python -m retrieval "What is the expense ratio of HDFC Large Cap?"
```

**Streamlit UI:** `code/ui/app.py`
- Groww colors: green `#00D09C`, background `#F8F9FA`, text `#1A1A2E`
- Header: "Groww MF FAQ — Facts Only"
- Welcome text + 3 clickable example questions
- Chat input → retriever → formatted answer block with Source link
- "Facts-only. No investment advice." banner always visible

---

## Environment

```
MISTRAL_API_KEY=<your key>    # .env only, never committed
PYTHONPATH=code               # set in shell or Render env
```

## Render Deploy

```
Build:  pip install -r requirements.txt
Start:  streamlit run code/ui/app.py \
          --server.port $PORT \
          --server.address 0.0.0.0 \
          --server.headless true \
          --browser.gatherUsageStats false
RAM:    ≥ 1 GB (2 GB recommended — torch + MiniLM + Chroma)
Secrets: MISTRAL_API_KEY, PYTHONPATH=code
```

`data/vectordb` is committed so Render serves immediately without re-ingesting.
