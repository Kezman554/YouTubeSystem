"""
Vector storage module using LanceDB.

Stores text chunks with embeddings for semantic search.
"""

import lancedb
from pathlib import Path
from typing import List, Optional
import uuid


# Database path configuration
LANCEDB_PATH = Path(__file__).parent.parent.parent / "data" / "vectors"


def get_db():
    """
    Get LanceDB connection.

    Returns:
        LanceDB connection object
    """
    LANCEDB_PATH.mkdir(parents=True, exist_ok=True)
    return lancedb.connect(str(LANCEDB_PATH))


def create_canon_passages_table(db=None):
    """
    Create the canon_passages table if it doesn't exist.

    Schema matches docs/DATA_MODEL.md:
    - id: Unique identifier (UUID)
    - niche_id: Links to SQLite niches table
    - source_id: Links to SQLite canon_sources table
    - text: The actual passage text
    - chapter: Book chapter/section
    - page: Page number
    - chunk_index: Position within source
    - characters: List of character names mentioned
    - locations: List of locations mentioned
    - themes: List of themes
    - era: Time period/era
    - vector: Embedding vector (384 dims for all-MiniLM-L6-v2)

    Args:
        db: LanceDB connection (optional, will create if not provided)

    Returns:
        LanceDB table object
    """
    if db is None:
        db = get_db()

    # Check if table exists
    try:
        table = db.open_table("canon_passages")
        print("Table 'canon_passages' already exists")
        return table
    except Exception:
        # Table doesn't exist, will create it when first data is added
        print("Table 'canon_passages' will be created on first insert")
        return None


def store_canon_chunks(
    chunks: List[dict],
    niche_id: int,
    source_id: int,
    vectors: List[List[float]],
    chapter: Optional[str] = None,
    page: Optional[int] = None,
    db=None
) -> int:
    """
    Store text chunks with embeddings in LanceDB.

    Args:
        chunks: List of chunk dicts with 'text' and 'chunk_index'
        niche_id: ID of the niche
        source_id: ID of the canon source
        vectors: List of embedding vectors (one per chunk)
        chapter: Optional chapter/section name
        page: Optional starting page number
        db: LanceDB connection (optional)

    Returns:
        Number of chunks stored

    Raises:
        ValueError: If chunks and vectors lengths don't match

    Example:
        >>> chunks = [
        ...     {"text": "First chunk...", "chunk_index": 0},
        ...     {"text": "Second chunk...", "chunk_index": 1}
        ... ]
        >>> vectors = [[0.1, 0.2, ...], [0.3, 0.4, ...]]
        >>> count = store_canon_chunks(chunks, niche_id=1, source_id=1, vectors=vectors)
        >>> print(f"Stored {count} chunks")
    """
    if len(chunks) != len(vectors):
        raise ValueError(f"Chunks ({len(chunks)}) and vectors ({len(vectors)}) must have same length")

    if not chunks:
        return 0

    if db is None:
        db = get_db()

    # Prepare data for LanceDB
    records = []
    for chunk, vector in zip(chunks, vectors):
        record = {
            "id": str(uuid.uuid4()),
            "niche_id": niche_id,
            "source_id": source_id,
            "text": chunk["text"],
            "chunk_index": chunk["chunk_index"],
            "chapter": chapter or "",
            "page": page or 0,
            "characters": [],  # TODO: Extract with NER or tagging
            "locations": [],   # TODO: Extract with NER or tagging
            "themes": [],      # TODO: Extract with LLM or classifier
            "era": "",         # TODO: Extract or manually tag
            "vector": vector
        }
        records.append(record)

    # Create or append to table
    try:
        table = db.open_table("canon_passages")
        table.add(records)
        print(f"Added {len(records)} chunks to existing table")
    except Exception:
        # Table doesn't exist, create it
        table = db.create_table("canon_passages", data=records)
        print(f"Created table 'canon_passages' with {len(records)} chunks")

    return len(records)


def search_canon(
    query: str,
    query_vector: List[float],
    niche_id: Optional[int] = None,
    limit: int = 10,
    db=None
) -> List[dict]:
    """
    Semantic search across canon passages.

    Args:
        query: The search query (for reference)
        query_vector: Embedding vector of the query
        niche_id: Optional filter by niche
        limit: Maximum number of results
        db: LanceDB connection (optional)

    Returns:
        List of matching passages with scores

    Example:
        >>> from src.pipeline.embed import embed_text
        >>> query_vec = embed_text("Tell me about Gandalf")
        >>> results = search_canon("Gandalf", query_vec, niche_id=1, limit=5)
        >>> for result in results:
        ...     print(result['text'][:100])
    """
    if db is None:
        db = get_db()

    try:
        table = db.open_table("canon_passages")
    except Exception as e:
        print(f"Table 'canon_passages' not found: {e}")
        return []

    # Build search
    search = table.search(query_vector).limit(limit)

    # Apply filter if niche_id specified
    if niche_id is not None:
        search = search.where(f"niche_id = {niche_id}")

    # Execute search
    results = search.to_list()

    return results


def get_stats(db=None) -> dict:
    """
    Get statistics about the vector database.

    Args:
        db: LanceDB connection (optional)

    Returns:
        Dictionary with stats (table count, record counts, etc.)
    """
    if db is None:
        db = get_db()

    stats = {
        "tables": [],
        "total_chunks": 0
    }

    try:
        # Get all tables
        table_names = db.table_names()

        for name in table_names:
            table = db.open_table(name)
            count = table.count_rows()

            stats["tables"].append({
                "name": name,
                "count": count
            })

            if name == "canon_passages":
                stats["total_chunks"] += count

    except Exception as e:
        print(f"Error getting stats: {e}")

    return stats
