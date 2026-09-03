"""
Streamlit UI — Groww MF FAQ Chatbot
Groww brand colors: green #00D09C, background #F8F9FA
"""
import os
import sys

import streamlit as st

# Ensure code/ is on the path when Streamlit launches from project root
_CODE_DIR = os.path.join(os.path.dirname(__file__), "..")
if _CODE_DIR not in sys.path:
    sys.path.insert(0, _CODE_DIR)

from retrieval.retriever import ask

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Groww MF FAQ",
    page_icon="📊",
    layout="centered",
)

# ---------------------------------------------------------------------------
# Custom CSS — Groww palette
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Background */
    .stApp { background-color: #F8F9FA; }

    /* Header bar */
    .groww-header {
        background: linear-gradient(90deg, #00D09C 0%, #00B386 100%);
        padding: 1rem 1.5rem;
        border-radius: 12px;
        margin-bottom: 1rem;
    }
    .groww-header h1 { color: #FFFFFF; margin: 0; font-size: 1.6rem; }
    .groww-header p  { color: #E0FFF8; margin: 0.3rem 0 0 0; font-size: 0.9rem; }

    /* Disclaimer banner */
    .disclaimer-banner {
        background-color: #FFF8E1;
        border-left: 4px solid #FFC107;
        padding: 0.6rem 1rem;
        border-radius: 4px;
        font-size: 0.82rem;
        color: #5D4037;
        margin-bottom: 1rem;
    }

    /* Example question chips */
    .chip-row { display: flex; gap: 0.5rem; flex-wrap: wrap; margin: 0.5rem 0 1rem; }
    .chip {
        background-color: #E8F5E9;
        color: #00796B;
        border: 1px solid #00D09C;
        border-radius: 20px;
        padding: 0.3rem 0.8rem;
        font-size: 0.82rem;
        cursor: pointer;
    }

    /* Answer card */
    .answer-card {
        background: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-top: 0.5rem;
    }
    .answer-text { font-size: 0.95rem; color: #1A1A2E; line-height: 1.6; }
    .source-line { font-size: 0.78rem; color: #00796B; margin-top: 0.6rem; }
    .updated-line { font-size: 0.75rem; color: #9E9E9E; margin-top: 0.2rem; }

    /* Hide Streamlit branding */
    #MainMenu, footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="groww-header">
      <h1>📊 Groww MF FAQ</h1>
      <p>Factual answers about HDFC Mutual Fund schemes on Groww. No investment advice.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Disclaimer banner
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="disclaimer-banner">
      ⚠️ <strong>Facts-only. No investment advice.</strong>
      This tool answers factual questions about selected HDFC schemes on Groww.
      It does not recommend, advise, or compare returns.
      Mutual Fund investments are subject to market risks.
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# In-scope schemes
# ---------------------------------------------------------------------------
with st.expander("📋 Schemes in scope (HDFC on Groww)", expanded=False):
    st.markdown(
        """
        | Scheme | Link |
        |--------|------|
        | HDFC Large Cap Fund Direct Growth | [View on Groww](https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth) |
        | HDFC Flexi Cap Fund Direct Growth | [View on Groww](https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth) |
        | HDFC ELSS Tax Saver Fund Direct Growth | [View on Groww](https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth) |
        | HDFC Small Cap Fund Direct Growth | [View on Groww](https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth) |
        | HDFC Balanced Advantage Fund Direct Growth | [View on Groww](https://groww.in/mutual-funds/hdfc-balanced-advantage-fund-direct-growth) |
        """
    )

# ---------------------------------------------------------------------------
# Example questions
# ---------------------------------------------------------------------------
st.markdown("**Try an example:**")

EXAMPLES = [
    "What is the expense ratio of HDFC Large Cap Fund?",
    "What is the lock-in period for HDFC ELSS Tax Saver Fund?",
    "What is the minimum SIP amount for HDFC Small Cap Fund?",
]

cols = st.columns(len(EXAMPLES))
clicked_example = None
for col, ex in zip(cols, EXAMPLES):
    if col.button(ex, use_container_width=True):
        clicked_example = ex

# ---------------------------------------------------------------------------
# Chat input
# ---------------------------------------------------------------------------
user_input = st.chat_input("Ask a factual question about these HDFC schemes…")

query = clicked_example or user_input

# ---------------------------------------------------------------------------
# Session history
# ---------------------------------------------------------------------------
if "history" not in st.session_state:
    st.session_state.history = []

if query:
    with st.spinner("Looking up facts…"):
        result = ask(query)

    st.session_state.history.append(
        {
            "query": query,
            "text": result.text,
            "source_url": result.source_url,
            "fetched_at": result.fetched_at,
            "refused": result.refused,
        }
    )

# ---------------------------------------------------------------------------
# Render history (newest first)
# ---------------------------------------------------------------------------
for entry in reversed(st.session_state.history):
    with st.chat_message("user"):
        st.write(entry["query"])

    with st.chat_message("assistant"):
        card_color = "#FFF3E0" if entry["refused"] else "#FFFFFF"
        source_html = (
            f'<a href="{entry["source_url"]}" target="_blank">{entry["source_url"]}</a>'
            if entry["source_url"]
            else ""
        )
        updated_html = (
            f'<div class="updated-line">Last updated from sources: {entry["fetched_at"]}</div>'
            if entry["fetched_at"]
            else ""
        )
        st.markdown(
            f"""
            <div class="answer-card" style="background:{card_color}">
              <div class="answer-text">{entry["text"]}</div>
              {f'<div class="source-line">🔗 Source: {source_html}</div>' if source_html else ""}
              {updated_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    "<p style='font-size:0.75rem; color:#9E9E9E; text-align:center;'>"
    "Prototype · Learning in Public · Facts sourced from public Groww scheme pages only · "
    "<a href='https://groww.in/mutual-funds' target='_blank'>groww.in/mutual-funds</a>"
    "</p>",
    unsafe_allow_html=True,
)
