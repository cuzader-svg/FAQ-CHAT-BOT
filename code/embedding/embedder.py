"""
Phase 3 — Embedding
Loads all chunks from data/chunks/ and encodes them with
sentence-transformers/all-MiniLM-L6-v2 (local, no API key).
Returns (chunks, embeddings) for use by the vector store phase.
"""
import json
import os

from sentence_transformers import SentenceTransformer

CHUNKS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "chunks")

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    """Lazy-load the embedding model (downloads on first call, cached after)."""
    global _model
    if _model is None:
        print(f"  Loading embedding model: {MODEL_NAME} ...")
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def load_chunks(chunks_dir: str = CHUNKS_DIR) -> list[dict]:
    """Load all chunk dicts from the chunks directory."""
    all_chunks = []
    for filename in sorted(os.listdir(chunks_dir)):
        if not filename.endswith(".json"):
            continue
        filepath = os.path.join(chunks_dir, filename)
        with open(filepath, encoding="utf-8") as fh:
            all_chunks.extend(json.load(fh))
    return all_chunks


def embed_chunks(chunks: list[dict]) -> list[list[float]]:
    """Encode the text field of each chunk. Returns list of float vectors."""
    model = get_model()
    texts = [c["text"] for c in chunks]
    print(f"  Embedding {len(texts)} chunks ...")
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)
    return embeddings.tolist()


def embed_query(query: str) -> list[float]:
    """Embed a single query string for retrieval."""
    model = get_model()
    return model.encode([query])[0].tolist()


if __name__ == "__main__":
    print("=== Phase 3: Embedding ===")
    chunks = load_chunks()
    if not chunks:
        print("No chunks found. Run Phase 2 first.")
    else:
        embeddings = embed_chunks(chunks)
        print(f"\nEmbedded {len(embeddings)} chunks. Vector dim: {len(embeddings[0])}")
