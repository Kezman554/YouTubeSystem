"""
Text chunking module.

Splits long texts into overlapping chunks at sentence boundaries
for optimal embedding and retrieval.
"""

import re
from typing import List


def chunk_text(
    text: str,
    chunk_size: int = 2000,  # characters (~500 tokens)
    overlap: int = 200       # characters (~50 tokens)
) -> List[str]:
    """
    Split text into overlapping chunks at sentence boundaries.

    Args:
        text: The text to chunk
        chunk_size: Target size in characters (default 2000 ≈ 500 tokens)
        overlap: Overlap size in characters (default 200 ≈ 50 tokens)

    Returns:
        List of text chunks

    Example:
        >>> text = "First sentence. Second sentence. Third sentence."
        >>> chunks = chunk_text(text, chunk_size=30, overlap=10)
        >>> len(chunks)
        2
    """
    if not text or not text.strip():
        return []

    # Split into sentences using regex
    # Matches periods, exclamation marks, question marks followed by space or end
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())

    if not sentences:
        return [text]

    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        sentence_length = len(sentence)

        # If adding this sentence exceeds chunk_size and we have content, save chunk
        if current_length + sentence_length + 1 > chunk_size and current_chunk:
            # Save current chunk
            chunks.append(' '.join(current_chunk))

            # Calculate overlap - keep last N characters worth of sentences
            if overlap > 0:
                overlap_sentences = []
                overlap_length = 0

                # Work backwards through current chunk to build overlap
                for s in reversed(current_chunk):
                    sentence_len = len(s) + 1  # +1 for space
                    if overlap_length + sentence_len <= overlap:
                        overlap_sentences.insert(0, s)
                        overlap_length += sentence_len
                    else:
                        break

                current_chunk = overlap_sentences
                current_length = sum(len(s) + 1 for s in overlap_sentences) - 1
            else:
                current_chunk = []
                current_length = 0

        # Add sentence to current chunk
        current_chunk.append(sentence)
        if current_length > 0:
            current_length += 1  # space before sentence
        current_length += sentence_length

    # Don't forget the last chunk
    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks


def chunk_with_metadata(
    text: str,
    chunk_size: int = 2000,
    overlap: int = 200,
    source_id: int = None,
    chapter: str = None,
    page: int = None
) -> List[dict]:
    """
    Chunk text and return with metadata for each chunk.

    Args:
        text: The text to chunk
        chunk_size: Target size in characters
        overlap: Overlap size in characters
        source_id: ID of the canon source
        chapter: Chapter or section name
        page: Starting page number

    Returns:
        List of dicts with 'text', 'chunk_index', and optional metadata

    Example:
        >>> chunks = chunk_with_metadata(
        ...     "Long text here...",
        ...     source_id=1,
        ...     chapter="The Shadow of the Past"
        ... )
        >>> chunks[0]['chunk_index']
        0
    """
    text_chunks = chunk_text(text, chunk_size, overlap)

    chunks_with_metadata = []
    for idx, chunk in enumerate(text_chunks):
        chunk_data = {
            'text': chunk,
            'chunk_index': idx,
            'char_count': len(chunk)
        }

        if source_id is not None:
            chunk_data['source_id'] = source_id

        if chapter:
            chunk_data['chapter'] = chapter

        if page is not None:
            chunk_data['page'] = page

        chunks_with_metadata.append(chunk_data)

    return chunks_with_metadata
