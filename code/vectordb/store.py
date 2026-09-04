"""
Phase 4 — Vector Store
Persists chunk embeddings into ChromaDB at data/vectordb/.
Also provides a query helper used by the retrieval phase.
"""
import os

import chromadb

VECTORDB_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "vectordb")
COLLECTION_NAME = "groww_mf_faq"

_client: chromadb.PersistentClient | None = None
_collection = None


def get_collection():
    """Return (creating if needed) the persisted Chroma collection."""
    global _client, _collection
    if _collection is None:
        os.makedirs(VECTORDB_DIR, exist_ok=True)
        _client = chromadb.PersistentClient(path=VECTORDB_DIR)
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def upsert_chunks(chunks: list[dict], embeddings: list[list[float]]) -> None:
    """Insert or update all chunks + embeddings into Chroma."""
    col = get_collection()
    ids = [c["id"] for c in chunks]
    documents = [c["text"] for c in chunks]
    metadatas = [
        {
            "scheme": c["scheme"],
            "title": c["title"],
            "source_url": c["source_url"],
            "fetched_at": c["fetched_at"],
            "chunk_index": c["chunk_index"],
        }
        for c in chunks
    ]

    # Chroma upsert in batches of 500
    batch = 500
    for start in range(0, len(ids), batch):
        col.upsert(
            ids=ids[start : start + batch],
            embeddings=embeddings[start : start + batch],
            documents=documents[start : start + batch],
            metadatas=metadatas[start : start + batch],
        )
    print(f"  Upserted {len(ids)} chunks into '{COLLECTION_NAME}'.")


def reset_collection() -> None:
    """Delete and recreate the collection (used before full re-ingest)."""
    global _client, _collection
    if _client is None:
        os.makedirs(VECTORDB_DIR, exist_ok=True)
        _client = chromadb.PersistentClient(path=VECTORDB_DIR)
    try:
        _client.delete_collection(COLLECTION_NAME)
        print(f"  Deleted old collection '{COLLECTION_NAME}'.")
    except Exception:
        pass  # didn't exist yet — fine
    _collection = None  # force re-create on next get_collection()


def query_collection(query_embedding: list[float], n_results: int = 4) -> dict:
    """Return top-n chunks for a query embedding."""
    col = get_collection()
    return col.query(
        query_embeddings=[query_embedding],
        n_results=min(n_results, col.count()),
        include=["documents", "metadatas", "distances"],
    )


def collection_count() -> int:
    return get_collection().count()


if __name__ == "__main__":
    from embedding.embedder import load_chunks, embed_chunks

    print("=== Phase 4: Vector Store ===")
    chunks = load_chunks()
    if not chunks:
        print("No chunks found. Run Phases 1-2 first (loader.py + chunker.py).")
    else:
        embeddings = embed_chunks(chunks)
        upsert_chunks(chunks, embeddings)
        print(f"  Total vectors stored: {collection_count()}")
