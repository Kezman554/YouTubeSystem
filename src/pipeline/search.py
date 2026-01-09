"""
Semantic search module for canon sources and transcripts.

Provides high-level search functions for finding relevant content.
"""

from typing import List, Optional, Dict, Any
import lancedb
from pathlib import Path

from src.pipeline.embed import embed_text


# Database path configuration
LANCEDB_PATH = Path(__file__).parent.parent.parent / "data" / "vectors"


def get_db():
    """Get LanceDB connection."""
    LANCEDB_PATH.mkdir(parents=True, exist_ok=True)
    return lancedb.connect(str(LANCEDB_PATH))


def search_canon(
    query: str,
    niche_id: Optional[int] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Search canon passages using semantic similarity.

    Args:
        query: The search query (natural language)
        niche_id: Optional filter by niche (None = search all niches)
        limit: Maximum number of results to return

    Returns:
        List of matching passages, each containing:
        - text: The passage text
        - source_id: ID of the canon source
        - chapter: Chapter/section name
        - page: Page number
        - niche_id: Niche ID
        - _distance: Relevance score (lower = more similar)
        - All other metadata fields

    Example:
        >>> results = search_canon("Tell me about Gandalf", niche_id=1, limit=5)
        >>> for result in results:
        ...     print(f"Score: {result['_distance']:.3f}")
        ...     print(f"Text: {result['text'][:100]}...")
        ...     print()

    Note:
        Returns empty list if canon_passages table doesn't exist yet.
    """
    db = get_db()

    # Check if table exists
    try:
        table = db.open_table("canon_passages")
    except Exception as e:
        print(f"Table 'canon_passages' not found: {e}")
        print("Run 'python scripts/test_chunking.py' first to ingest canon sources")
        return []

    # Embed the query
    try:
        query_vector = embed_text(query)
    except Exception as e:
        print(f"Failed to embed query: {e}")
        return []

    # Build search
    search = table.search(query_vector).limit(limit)

    # Apply niche filter if specified
    if niche_id is not None:
        search = search.where(f"niche_id = {niche_id}")

    # Execute search
    try:
        results = search.to_list()
        return results
    except Exception as e:
        print(f"Search failed: {e}")
        return []


def search_transcripts(
    query: str,
    niche_id: Optional[int] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Search competitor transcript chunks using semantic similarity.

    Args:
        query: The search query (natural language)
        niche_id: Optional filter by niche (None = search all niches)
        limit: Maximum number of results to return

    Returns:
        List of matching transcript chunks, each containing:
        - text: The transcript chunk text
        - video_id: ID of the video
        - channel_id: ID of the channel
        - video_title: Title of the video
        - channel_name: Name of the channel
        - timestamp_start: Start time in video (seconds)
        - timestamp_end: End time in video (seconds)
        - view_count: Video view count
        - published_at: Video publication date
        - _distance: Relevance score (lower = more similar)

    Example:
        >>> results = search_transcripts(
        ...     "How did Gandalf defeat the Balrog?",
        ...     niche_id=1,
        ...     limit=5
        ... )
        >>> for result in results:
        ...     print(f"Video: {result['video_title']}")
        ...     print(f"Channel: {result['channel_name']}")
        ...     print(f"Score: {result['_distance']:.3f}")
        ...     print(f"Text: {result['text'][:100]}...")
        ...     print()

    Note:
        Returns empty list if transcript_chunks table doesn't exist yet.
        This table will be populated when transcripts are processed through
        the chunking and embedding pipeline.
    """
    db = get_db()

    # Check if table exists
    try:
        table = db.open_table("transcript_chunks")
    except Exception as e:
        print(f"Table 'transcript_chunks' not found: {e}")
        print("Transcript chunks haven't been processed yet.")
        print("This feature will be available after implementing transcript chunking.")
        return []

    # Embed the query
    try:
        query_vector = embed_text(query)
    except Exception as e:
        print(f"Failed to embed query: {e}")
        return []

    # Build search
    search = table.search(query_vector).limit(limit)

    # Apply niche filter if specified
    if niche_id is not None:
        search = search.where(f"niche_id = {niche_id}")

    # Execute search
    try:
        results = search.to_list()
        return results
    except Exception as e:
        print(f"Search failed: {e}")
        return []


def search_both(
    query: str,
    niche_id: Optional[int] = None,
    canon_limit: int = 5,
    transcript_limit: int = 5
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Search both canon passages and transcripts.

    Args:
        query: The search query
        niche_id: Optional filter by niche
        canon_limit: Max canon results
        transcript_limit: Max transcript results

    Returns:
        Dictionary with 'canon' and 'transcripts' keys, each containing
        a list of results

    Example:
        >>> results = search_both("ring of power", niche_id=1)
        >>> print(f"Found {len(results['canon'])} canon passages")
        >>> print(f"Found {len(results['transcripts'])} transcript chunks")
    """
    return {
        "canon": search_canon(query, niche_id, canon_limit),
        "transcripts": search_transcripts(query, niche_id, transcript_limit)
    }


def format_result(result: Dict[str, Any], result_type: str = "canon") -> str:
    """
    Format a search result for display.

    Args:
        result: Search result dictionary
        result_type: Either "canon" or "transcript"

    Returns:
        Formatted string for display
    """
    lines = []

    # Relevance score
    distance = result.get('_distance', 0)
    similarity = 1 - distance  # Convert distance to similarity (0-1)
    lines.append(f"Relevance: {similarity:.1%}")

    if result_type == "canon":
        # Canon passage formatting
        if 'chapter' in result and result['chapter']:
            lines.append(f"Source: {result['chapter']}")
        if 'page' in result and result['page']:
            lines.append(f"Page: {result['page']}")
        lines.append(f"Source ID: {result.get('source_id', 'N/A')}")

    elif result_type == "transcript":
        # Transcript formatting
        if 'video_title' in result:
            lines.append(f"Video: {result['video_title']}")
        if 'channel_name' in result:
            lines.append(f"Channel: {result['channel_name']}")
        if 'view_count' in result:
            lines.append(f"Views: {result['view_count']:,}")
        if 'timestamp_start' in result:
            mins = int(result['timestamp_start'] // 60)
            secs = int(result['timestamp_start'] % 60)
            lines.append(f"Timestamp: {mins}:{secs:02d}")

    # Text preview (first 200 chars)
    text = result.get('text', '')
    if text:
        preview = text[:200].replace('\n', ' ')
        lines.append(f"\n{preview}...")

    return '\n'.join(lines)
