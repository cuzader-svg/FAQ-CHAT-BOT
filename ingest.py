"""
Ingest orchestrator — runs all 4 phases in sequence:
  Phase 1: Data Loading
  Phase 2: Chunking
  Phase 3: Embedding
  Phase 4: Vector Store

Usage:
    PYTHONPATH=code python ingest.py
"""
import sys
import os

# Ensure code/ is on path when run from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "code"))

from loading.loader import load_all
from chunking.chunker import chunk_all
from chunking.fact_synth import synthesize_all
from embedding.embedder import load_chunks, embed_chunks
from vectordb.store import upsert_chunks, collection_count, reset_collection


def run(skip_loading: bool = False):
    print("\n" + "=" * 50)
    print(" Groww MF FAQ — Full Ingest Pipeline")
    print("=" * 50)

    if not skip_loading:
        print("\n[Phase 1] Data Loading")
        records = load_all()
        if not records:
            print("ERROR: No pages loaded. Check your network and try again.")
            sys.exit(1)
        print(f"  → {len(records)} pages saved to data/raw/")
    else:
        print("\n[Phase 1] Skipped (using existing raw files)")

    print("\n[Phase 2] Chunking")
    chunk_all()

    print("\n[Phase 2b] Fact Synthesis")
    synthesize_all()

    print("\n[Phase 3 + 4] Embedding + Vector Store")
    # Reset first so old chunks with stale sizes don't persist
    reset_collection()
    chunks = load_chunks()
    if not chunks:
        print("ERROR: No chunks found.")
        sys.exit(1)
    embeddings = embed_chunks(chunks)
    upsert_chunks(chunks, embeddings)

    count = collection_count()
    print(f"\n{'=' * 50}")
    print(f" Ingest complete. {count} vectors stored in data/vectordb/")
    print(f"{'=' * 50}\n")


if __name__ == "__main__":
    skip = "--skip-loading" in sys.argv
    run(skip_loading=skip)
