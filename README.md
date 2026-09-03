# Groww MF FAQ Chatbot — README

A facts-only RAG chatbot for HDFC Mutual Fund schemes on Groww.
Built as a Learning in Public prototype.

---

## Scope

| Item | Value |
|------|-------|
| Product | [Groww](https://groww.in/) |
| AMC | HDFC Mutual Fund |
| Schemes | 5 (Large Cap, Flexi Cap, ELSS, Small Cap, Balanced Advantage) |
| Corpus | Exactly 5 public Groww scheme pages |
| LLM | Mistral (`mistral-small-latest`) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (local) |
| Vector DB | ChromaDB (persisted in `data/vectordb/`) |
| UI | Streamlit (Groww green/white) |

---

## Prerequisites

- **Python 3.11+** installed and on PATH
- **Mistral API key** — get one free at [console.mistral.ai](https://console.mistral.ai)
- Internet access to fetch the 5 Groww pages during ingest

---

## Setup

```bash
# 1. Clone the repo
git clone https://github.com/<your-username>/FAQ-CHAT-BOT.git
cd FAQ-CHAT-BOT

# 2. Create and activate a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set your Mistral API key
copy .env.example .env        # Windows
# cp .env.example .env        # macOS/Linux
# Then open .env and replace 'your_mistral_api_key_here' with your actual key

# 5. Run ingest (fetches the 5 Groww pages, embeds, persists Chroma)
PYTHONPATH=code python ingest.py
# On Windows PowerShell:
# $env:PYTHONPATH="code"; python ingest.py

# 6. Launch the app
PYTHONPATH=code streamlit run code/ui/app.py
# On Windows PowerShell:
# $env:PYTHONPATH="code"; streamlit run code/ui/app.py
```

---

## CLI Testing

After ingest, test the retrieval backend directly:

```bash
# Expense ratio
PYTHONPATH=code python -m retrieval "What is the expense ratio of HDFC Large Cap?"

# ELSS lock-in
PYTHONPATH=code python -m retrieval "What is the lock-in period for HDFC ELSS?"

# Minimum SIP
PYTHONPATH=code python -m retrieval "What is the minimum SIP for HDFC Small Cap?"

# Exit load
PYTHONPATH=code python -m retrieval "What is the exit load of HDFC Flexi Cap?"

# Advice refusal (should NOT give a recommendation)
PYTHONPATH=code python -m retrieval "Should I invest in HDFC Large Cap?"

# Returns refusal
PYTHONPATH=code python -m retrieval "What is the 3-year CAGR of HDFC Large Cap?"
```

---

## Deploying to Render

1. Push the repo to GitHub (with `data/vectordb/` committed — no re-ingest on Render).
2. Log in at [render.com](https://render.com) → New → Web Service → connect your repo.
3. Settings:

   | Field | Value |
   |-------|-------|
   | Runtime | Python 3 |
   | Build command | `pip install -r requirements.txt` |
   | Start command | `streamlit run code/ui/app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true --browser.gatherUsageStats false` |
   | Instance RAM | **≥ 1 GB** (2 GB safer; 512 MB will OOM) |

4. Add environment variables as secrets:

   | Key | Value |
   |-----|-------|
   | `MISTRAL_API_KEY` | your key (mark as secret) |
   | `PYTHONPATH` | `code` |

5. Deploy and open the Render URL.

---

## Known Limits

- **Corpus is frozen at ingest time.** Expense ratios, exit loads, and SIP minimums can change on Groww. Always verify on the cited scheme page.
- **Only 5 HDFC schemes.** Questions about other AMCs or other HDFC schemes will not be answered from context.
- **Capital-gains download steps** are not on the 5 scheme pages; the bot will say so honestly.
- **Returns data** on Groww pages is visible but the model is instructed not to quote or compare it.
- **First Render load** may be slow (~30–60 s) while Hugging Face downloads the MiniLM model.
- **Free Render tier** may sleep after inactivity; first hit after idle can take ~1 minute.
- **Source list note:** LIP challenge recommends 15–25 URLs. Per the project brief, the RAG corpus is intentionally locked to these 5 Groww scheme pages.

---

## Disclaimer

Facts-only. No investment advice. See [docs/disclaimer.md](docs/disclaimer.md).

Mutual Fund investments are subject to market risks. Read all scheme-related documents carefully before investing.
