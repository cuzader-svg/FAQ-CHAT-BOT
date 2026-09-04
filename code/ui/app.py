"""
Streamlit UI — Groww MF FAQ Chatbot
Styled to match Groww's Mint Design System:
  Primary green  : #00D09C  (contentAccent)
  Dark navy      : #1A2236  (navbar bg)
  Body text      : #44475B
  Card bg        : #FFFFFF  with subtle shadow
  Page bg        : #F4F4F9
"""
import os
import sys

import streamlit as st

_CODE_DIR = os.path.join(os.path.dirname(__file__), "..")
if _CODE_DIR not in sys.path:
    sys.path.insert(0, _CODE_DIR)

from retrieval.retriever import ask

@st.cache_resource(show_spinner="Loading model…")
def _load_embedding_model():
    from embedding.embedder import get_model
    return get_model()

_load_embedding_model()

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Groww — HDFC MF FAQ",
    page_icon="https://groww.in/favicon.ico",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# CSS — Groww Mint Design System replica
# ---------------------------------------------------------------------------
st.markdown("""
<style>
  /* ── Import Google Font close to GrowwSans ── */
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

  /* ── Global reset ── */
  html, body, [class*="css"] {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
  }
  .stApp { background-color: #F4F4F9 !important; }

  /* ── Hide all Streamlit chrome ── */
  #MainMenu, footer, [data-testid="stToolbar"],
  [data-testid="stDecoration"], [data-testid="stStatusWidget"],
  .stDeployButton { display: none !important; }

  /* ── Top navbar ── */
  .groww-nav {
      background: #1A2236;
      padding: 0 24px;
      height: 56px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-radius: 0 0 0 0;
      margin: -1rem -1rem 0 -1rem;
  }
  .groww-logo {
      display: flex;
      align-items: center;
      gap: 8px;
  }
  .groww-logo-icon {
      width: 32px; height: 32px;
      background: #00D09C;
      border-radius: 8px;
      display: flex; align-items: center; justify-content: center;
      font-weight: 800; font-size: 18px; color: #1A2236;
  }
  .groww-logo-text {
      color: #FFFFFF;
      font-size: 20px;
      font-weight: 700;
      letter-spacing: -0.3px;
  }
  .groww-nav-links {
      display: flex; gap: 24px;
  }
  .groww-nav-link {
      color: #8E9BB0;
      font-size: 13px;
      font-weight: 500;
      text-decoration: none;
      padding: 4px 0;
      border-bottom: 2px solid transparent;
  }
  .groww-nav-link.active {
      color: #00D09C;
      border-bottom-color: #00D09C;
  }

  /* ── Page hero ── */
  .groww-hero {
      background: linear-gradient(135deg, #1A2236 0%, #243048 100%);
      padding: 28px 28px 24px;
      border-radius: 0 0 16px 16px;
      margin: 0 -1rem 20px -1rem;
  }
  .groww-hero-badge {
      display: inline-flex; align-items: center; gap: 6px;
      background: rgba(0,208,156,0.15);
      color: #00D09C;
      font-size: 11px; font-weight: 600;
      padding: 3px 10px; border-radius: 20px;
      margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.5px;
  }
  .groww-hero h1 {
      color: #FFFFFF; font-size: 22px; font-weight: 700;
      margin: 0 0 6px 0; line-height: 1.3;
  }
  .groww-hero p {
      color: #8E9BB0; font-size: 13px; margin: 0;
  }
  .groww-hero-divider {
      border: none; border-top: 1px solid rgba(255,255,255,0.08);
      margin: 16px 0 0 0;
  }

  /* ── Scheme pills ── */
  .scheme-pills { display: flex; gap: 8px; flex-wrap: wrap; margin: 16px 0 8px; }
  .scheme-pill {
      background: #FFFFFF;
      border: 1.5px solid #E2E8F0;
      color: #44475B;
      font-size: 12px; font-weight: 500;
      padding: 5px 12px; border-radius: 20px;
      cursor: default; white-space: nowrap;
  }
  .scheme-pill.active {
      background: #E6FAF5;
      border-color: #00D09C;
      color: #00B386;
  }

  /* ── Disclaimer ── */
  .groww-disclaimer {
      background: #FFFBEB;
      border: 1px solid #FDE68A;
      border-left: 3px solid #F59E0B;
      padding: 10px 14px;
      border-radius: 8px;
      font-size: 12px; color: #78350F;
      margin-bottom: 16px;
      display: flex; gap: 8px; align-items: flex-start;
  }

  /* ── Example question buttons ── */
  .stButton > button {
      background: #FFFFFF !important;
      color: #00B386 !important;
      border: 1.5px solid #00D09C !important;
      border-radius: 8px !important;
      font-size: 12px !important;
      font-weight: 500 !important;
      padding: 6px 10px !important;
      transition: all 0.15s ease !important;
      text-align: left !important;
      white-space: normal !important;
      line-height: 1.4 !important;
  }
  .stButton > button:hover {
      background: #00D09C !important;
      color: #FFFFFF !important;
      border-color: #00D09C !important;
      box-shadow: 0 2px 8px rgba(0,208,156,0.3) !important;
  }
  .stButton > button:active {
      background: #00B386 !important;
      color: #FFFFFF !important;
  }

  /* ── Chat input ── */
  [data-testid="stChatInput"] textarea {
      background: #FFFFFF !important;
      border: 1.5px solid #E2E8F0 !important;
      border-radius: 10px !important;
      font-size: 14px !important;
      color: #44475B !important;
  }
  [data-testid="stChatInput"] textarea:focus {
      border-color: #00D09C !important;
      box-shadow: 0 0 0 3px rgba(0,208,156,0.15) !important;
  }
  [data-testid="stChatInputSubmitButton"] {
      background: #00D09C !important;
      border-radius: 8px !important;
  }

  /* ── Chat messages ── */
  [data-testid="stChatMessage"] {
      background: transparent !important;
      border: none !important;
      padding: 0 !important;
  }

  /* ── Answer card ── */
  .groww-answer {
      background: #FFFFFF;
      border: 1px solid #E2E8F0;
      border-radius: 12px;
      padding: 16px 18px;
      box-shadow: 0 2px 8px rgba(26,34,54,0.06);
      margin-top: 4px;
  }
  .groww-answer-text {
      font-size: 14px; color: #1A2236;
      line-height: 1.7; margin-bottom: 10px;
  }
  .groww-answer-meta {
      display: flex; flex-direction: column; gap: 4px;
      padding-top: 10px;
      border-top: 1px solid #F1F5F9;
  }
  .groww-source {
      display: flex; align-items: center; gap: 6px;
      font-size: 12px; color: #00B386; font-weight: 500;
  }
  .groww-source a { color: #00B386 !important; text-decoration: none; }
  .groww-source a:hover { text-decoration: underline; }
  .groww-updated { font-size: 11px; color: #94A3B8; }

  .groww-refused {
      background: #FFFBEB;
      border-color: #FDE68A;
  }
  .groww-refused .groww-answer-text { color: #78350F; }

  /* ── Section label ── */
  .groww-section-label {
      font-size: 11px; font-weight: 600; color: #94A3B8;
      text-transform: uppercase; letter-spacing: 0.8px;
      margin: 0 0 10px 0;
  }

  /* ── Info chips in scope expander ── */
  .st-expander {
      background: #FFFFFF !important;
      border: 1px solid #E2E8F0 !important;
      border-radius: 10px !important;
  }
  details > summary {
      font-size: 13px !important;
      font-weight: 600 !important;
      color: #44475B !important;
      padding: 10px 14px !important;
  }
  details > summary:hover { color: #00B386 !important; }
  details[open] > summary { color: #00B386 !important; }

  /* ── Footer ── */
  .groww-footer {
      text-align: center;
      padding: 16px 0 8px;
      font-size: 11px; color: #94A3B8;
  }
  .groww-footer a { color: #00B386 !important; text-decoration: none; }
  .groww-footer a:hover { text-decoration: underline; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# TOP NAVBAR
# ---------------------------------------------------------------------------
st.markdown("""
<div class="groww-nav">
  <div class="groww-logo">
    <div class="groww-logo-icon">g</div>
    <span class="groww-logo-text">groww</span>
  </div>
  <div class="groww-nav-links">
    <span class="groww-nav-link">Stocks</span>
    <span class="groww-nav-link active">Mutual Funds</span>
    <span class="groww-nav-link">IPO</span>
    <span class="groww-nav-link">F&amp;O</span>
    <span class="groww-nav-link">US Stocks</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# HERO SECTION
# ---------------------------------------------------------------------------
st.markdown("""
<div class="groww-hero">
  <div class="groww-hero-badge">🤖 AI Assistant</div>
  <h1>HDFC Mutual Fund — FAQ</h1>
  <p>Get instant factual answers about HDFC schemes listed on Groww. Powered by RAG.</p>
  <hr class="groww-hero-divider"/>
  <div class="scheme-pills">
    <span class="scheme-pill active">HDFC Large Cap</span>
    <span class="scheme-pill active">HDFC Flexi Cap</span>
    <span class="scheme-pill active">HDFC ELSS Tax Saver</span>
    <span class="scheme-pill active">HDFC Small Cap</span>
    <span class="scheme-pill active">HDFC Balanced Advantage</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# DISCLAIMER
# ---------------------------------------------------------------------------
st.markdown("""
<div class="groww-disclaimer">
  <span>⚠️</span>
  <span>
    <strong>Facts-only. No investment advice.</strong>
    Answers are sourced from public Groww scheme pages only.
    This tool does not recommend, rank, or compare returns.
    Mutual Fund investments are subject to market risks.
    Please read all scheme-related documents carefully before investing.
  </span>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# SCOPE EXPANDER
# ---------------------------------------------------------------------------
with st.expander("📋 View 5 HDFC schemes in scope", expanded=False):
    st.markdown("""
| Scheme | Category | Link |
|--------|----------|------|
| HDFC Large Cap Fund Direct Growth | Equity – Large Cap | [groww.in ↗](https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth) |
| HDFC Flexi Cap Fund Direct Growth | Equity – Flexi Cap | [groww.in ↗](https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth) |
| HDFC ELSS Tax Saver Fund Direct Growth | Equity – ELSS | [groww.in ↗](https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth) |
| HDFC Small Cap Fund Direct Growth | Equity – Small Cap | [groww.in ↗](https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth) |
| HDFC Balanced Advantage Fund Direct Growth | Hybrid – Balanced Advantage | [groww.in ↗](https://groww.in/mutual-funds/hdfc-balanced-advantage-fund-direct-growth) |
    """)

# ---------------------------------------------------------------------------
# EXAMPLE QUESTIONS
# ---------------------------------------------------------------------------
st.markdown('<p class="groww-section-label">Try asking</p>', unsafe_allow_html=True)

EXAMPLES = [
    "What is the expense ratio of HDFC Large Cap Fund?",
    "What is the ELSS lock-in period for HDFC Tax Saver Fund?",
    "What is the minimum SIP for HDFC Small Cap Fund?",
]

cols = st.columns(len(EXAMPLES))
clicked_example = None
for col, ex in zip(cols, EXAMPLES):
    if col.button(ex, use_container_width=True):
        clicked_example = ex

st.markdown("<br/>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# CHAT INPUT
# ---------------------------------------------------------------------------
user_input = st.chat_input("Ask a factual question about these HDFC schemes…")
query = clicked_example or user_input

# ---------------------------------------------------------------------------
# SESSION HISTORY
# ---------------------------------------------------------------------------
if "history" not in st.session_state:
    st.session_state.history = []

if query:
    with st.spinner("Fetching facts from Groww sources…"):
        result = ask(query)
    st.session_state.history.append({
        "query":      query,
        "text":       result.text,
        "source_url": result.source_url,
        "fetched_at": result.fetched_at,
        "refused":    result.refused,
    })

# ---------------------------------------------------------------------------
# RENDER HISTORY (newest first)
# ---------------------------------------------------------------------------
if st.session_state.history:
    st.markdown('<p class="groww-section-label">Answers</p>', unsafe_allow_html=True)

for entry in reversed(st.session_state.history):
    with st.chat_message("user"):
        st.markdown(
            f"<span style='font-size:14px;font-weight:500;color:#1A2236'>{entry['query']}</span>",
            unsafe_allow_html=True,
        )

    with st.chat_message("assistant", avatar="https://groww.in/favicon.ico"):
        refused_class = "groww-refused" if entry["refused"] else ""
        source_html = (
            f'<a href="{entry["source_url"]}" target="_blank">{entry["source_url"]}</a>'
            if entry["source_url"] else ""
        )
        updated_html = (
            f'<span class="groww-updated">Last updated from sources: {entry["fetched_at"]}</span>'
            if entry["fetched_at"] else ""
        )
        st.markdown(f"""
<div class="groww-answer {refused_class}">
  <div class="groww-answer-text">{entry["text"]}</div>
  <div class="groww-answer-meta">
    {f'<div class="groww-source">🔗 &nbsp;<span>Source:</span> {source_html}</div>' if source_html else ""}
    {updated_html}
  </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# FOOTER
# ---------------------------------------------------------------------------
st.markdown("""
<div class="groww-footer">
  Prototype · Learning in Public challenge ·
  Facts sourced from public Groww scheme pages only ·
  <a href="https://groww.in/mutual-funds" target="_blank">groww.in/mutual-funds</a>
</div>
""", unsafe_allow_html=True)
