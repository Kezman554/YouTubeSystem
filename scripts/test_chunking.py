"""
Test script for chunking and embedding pipeline.

Tests the complete flow:
1. Load a canon source from database
2. Extract text from PDF
3. Chunk the text
4. Generate embeddings
5. Store in LanceDB
6. Show statistics
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.canon_sources import get_sources_by_niche, mark_as_ingested
from src.database.niches import get_all_niches
from src.pipeline.ingest import extract_pdf
from src.pipeline.chunk import chunk_with_metadata
from src.pipeline.embed import embed_batch
from src.pipeline.vectorstore import store_canon_chunks, get_stats


def test_chunking_pipeline():
    """Test the complete chunking and embedding pipeline."""
    print("=" * 80)
    print("CHUNKING AND EMBEDDING TEST")
    print("=" * 80)
    print()

    # Get niches
    niches = get_all_niches()
    if not niches:
        print("ERROR: No niches found. Create one first.")
        return

    print(f"Found {len(niches)} niche(s):")
    for niche in niches:
        print(f"  - {niche['name']} (ID: {niche['id']})")
    print()

    # Get canon sources for first niche
    niche = niches[0]
    sources = get_sources_by_niche(niche['id'])

    if not sources:
        print(f"ERROR: No canon sources found for {niche['name']}")
        print("Run 'python scripts/test_ingest.py' first to add sources")
        return

    print(f"Canon sources for {niche['name']}:")
    for source in sources:
        status = "[INGESTED]" if source['ingested'] else "[NOT INGESTED]"
        print(f"  {status} {source['title']} by {source['author']}")
    print()

    # Find first non-ingested source
    source_to_process = None
    for source in sources:
        if not source['ingested']:
            source_to_process = source
            break

    if not source_to_process:
        print("All sources have been ingested!")
        print()
        # Show stats
        stats = get_stats()
        print("Vector database stats:")
        for table in stats['tables']:
            print(f"  Table '{table['name']}': {table['count']} records")
        return

    print("-" * 80)
    print(f"Processing: {source_to_process['title']}")
    print("-" * 80)
    print()

    # Step 1: Extract text from PDF
    print("Step 1: Extracting text from PDF...")
    file_path = source_to_process['file_path']

    if not file_path or not Path(file_path).exists():
        print(f"ERROR: File not found: {file_path}")
        return

    try:
        full_text, metadata = extract_pdf(file_path)
        print(f"  ✓ Extracted {metadata['page_count']} pages")
        print(f"  ✓ Total characters: {len(full_text):,}")
        print()
    except Exception as e:
        print(f"  ✗ Failed to extract: {e}")
        return

    # Step 2: Chunk the text
    print("Step 2: Chunking text...")
    try:
        chunks = chunk_with_metadata(
            text=full_text,
            chunk_size=2000,
            overlap=200,
            source_id=source_to_process['id']
        )
        print(f"  ✓ Created {len(chunks)} chunks")
        print(f"  ✓ Average chunk size: {sum(c['char_count'] for c in chunks) // len(chunks)} characters")
        print()

        # Show sample chunks
        print("  Sample chunks:")
        for i in range(min(3, len(chunks))):
            preview = chunks[i]['text'][:100].replace('\n', ' ')
            print(f"    Chunk {i}: {preview}...")
        print()

    except Exception as e:
        print(f"  ✗ Failed to chunk: {e}")
        return

    # Step 3: Generate embeddings
    print("Step 3: Generating embeddings...")
    print(f"  Processing {len(chunks)} chunks...")
    try:
        texts = [chunk['text'] for chunk in chunks]
        vectors = embed_batch(texts, batch_size=32)
        print(f"  ✓ Generated {len(vectors)} embedding vectors")
        print(f"  ✓ Vector dimension: {len(vectors[0])}")
        print()
    except Exception as e:
        print(f"  ✗ Failed to generate embeddings: {e}")
        return

    # Step 4: Store in LanceDB
    print("Step 4: Storing in LanceDB...")
    try:
        count = store_canon_chunks(
            chunks=chunks,
            niche_id=niche['id'],
            source_id=source_to_process['id'],
            vectors=vectors,
            chapter=source_to_process['title']
        )
        print(f"  ✓ Stored {count} chunks in vector database")
        print()
    except Exception as e:
        print(f"  ✗ Failed to store: {e}")
        return

    # Step 5: Mark as ingested
    print("Step 5: Marking source as ingested...")
    try:
        mark_as_ingested(source_to_process['id'])
        print(f"  ✓ Marked '{source_to_process['title']}' as ingested")
        print()
    except Exception as e:
        print(f"  ✗ Failed to mark as ingested: {e}")

    # Summary
    print("=" * 80)
    print("PIPELINE COMPLETE")
    print("=" * 80)
    print()
    print(f"Source: {source_to_process['title']}")
    print(f"Chunks created: {len(chunks)}")
    print(f"Vectors generated: {len(vectors)}")
    print(f"Stored in LanceDB: {count}")
    print()

    # Show overall stats
    stats = get_stats()
    print("Vector database stats:")
    for table in stats['tables']:
        print(f"  Table '{table['name']}': {table['count']} records")
    print()

    # Check for more sources to process
    remaining = [s for s in sources if not s['ingested'] and s['id'] != source_to_process['id']]
    if remaining:
        print(f"Note: {len(remaining)} more source(s) to process")
        print("Run this script again to process the next one")
    else:
        print("All sources have been processed!")


if __name__ == "__main__":
    test_chunking_pipeline()
