# Makes `python -m retrieval` work from project root with PYTHONPATH=code
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from retrieval.retriever import ask

if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What is the expense ratio of HDFC Large Cap?"
    result = ask(query)
    print(f"\nQuery: {query}\n{'-' * 60}")
    print(result.text)
    if result.source_url:
        print(f"\nSource: {result.source_url}")
    if result.fetched_at:
        print(f"Last updated from sources: {result.fetched_at}")
