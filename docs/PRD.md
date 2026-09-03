# Product Requirements Document (PRD)
## Groww Mutual Fund FAQ Chatbot — RAG Prototype

---

### 1. Purpose
A facts-only FAQ chatbot that answers questions about HDFC Mutual Fund schemes
displayed on Groww. Built as a Learning in Public challenge prototype to demonstrate
W1 (thinking like a model), W2 (LLMs & prompting), and W3 (RAG).

### 2. Scope

**In scope**
- Product: Groww ([groww.in](https://groww.in/))
- AMC: HDFC Mutual Fund
- Schemes: 5 (Large Cap, Flexi Cap, ELSS, Small Cap, Balanced Advantage)
- Factual fields: expense ratio, exit load, minimum SIP, lock-in, riskometer, benchmark

**Out of scope**
- Investment advice, return comparisons, portfolio suggestions
- Any scheme not in the 5-URL corpus
- Capital-gains statement download steps (not available on scheme pages)
- Any logged-in Groww feature (reports, transactions, portfolio)

### 3. Corpus
Exactly 5 public Groww URLs — no other sources ingested into the vector store.

| # | Scheme | URL |
|---|--------|-----|
| 1 | HDFC Large Cap Fund Direct Growth | https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth |
| 2 | HDFC Flexi Cap Fund Direct Growth | https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth |
| 3 | HDFC ELSS Tax Saver Fund Direct Growth | https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth |
| 4 | HDFC Small Cap Fund Direct Growth | https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth |
| 5 | HDFC Balanced Advantage Fund Direct Growth | https://groww.in/mutual-funds/hdfc-balanced-advantage-fund-direct-growth |

### 4. Functional Requirements

| ID | Requirement |
|----|-------------|
| F1 | Answer factual queries using only retrieved chunks from the 5 corpus pages |
| F2 | Every answer includes exactly one source URL (the Groww scheme page used) |
| F3 | Answers ≤ 3 sentences + "Last updated from sources: YYYY-MM-DD" |
| F4 | Politely refuse advice questions (buy/sell/portfolio/best fund) |
| F5 | Politely refuse return/CAGR computation requests; cite the scheme page |
| F6 | Refuse to accept or store PII (PAN, Aadhaar, phone, email, OTP) |
| F7 | If query is out of corpus, say so and cite the closest scheme page |
| F8 | UI shows: welcome line, 3 example questions, facts-only disclaimer note |

### 5. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| N1 | Embeddings run locally (sentence-transformers, no API cost) |
| N2 | Vector DB persisted to disk (Chroma in data/vectordb) — no re-ingest on Render |
| N3 | LLM: Mistral API (MISTRAL_API_KEY in .env, never committed) |
| N4 | UI: Streamlit, Groww brand colors (green #00D09C, white) |
| N5 | No user accounts, no session storage, no logging of user queries |
| N6 | PYTHONPATH=code for all module imports |

### 6. Data Privacy
- No PII accepted in the input field.
- No query logs written to disk.
- .env file excluded from git via .gitignore.

### 7. Constraints
- Do not ingest SEBI, AMFI, Groww Help, or growwmf.in into the vector store.
- Do not hardcode live numbers (expense ratio, SIP, etc.) — scrape live pages.
- Groww pages may show performance data; the LLM must not quote or rank it.

### 8. Acceptance Criteria
- [ ] CLI query returns correct expense ratio for HDFC Large Cap citing the URL
- [ ] CLI query returns 3-year lock-in for HDFC ELSS citing the URL
- [ ] CLI query returns ₹100 min SIP for HDFC Small Cap citing the URL
- [ ] Advice query returns a polite refusal (no fund recommendation)
- [ ] PII input returns a refusal without echoing the PII
- [ ] Returns question returns a refusal pointing to the scheme page
- [ ] Streamlit UI loads, shows 3 examples, and answers a factual question with citation
