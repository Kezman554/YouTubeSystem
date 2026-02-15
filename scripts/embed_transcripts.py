"""
Chunk and embed all competitor video transcripts into LanceDB.

Reads transcripts from SQLite, chunks them, generates embeddings,
and stores them in the transcript_chunks LanceDB table.

Usage:
    python scripts/embed_transcripts.py
"""
import sys
import io
import time
from pathlib import Path

# Handle Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.schema import get_connection
from src.pipeline.chunk import chunk_text
from src.pipeline.embed import embed_batch
from src.pipeline.vectorstore import get_db, store_transcript_chunks


def get_videos_with_transcripts():
    """Fetch all videos that have transcript text from SQLite."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT v.id, v.channel_id, v.niche_id, v.youtube_id, v.title,
                   v.transcript, v.view_count, v.published_at,
                   c.name as channel_name
            FROM competitor_videos v
            JOIN competitor_channels c ON v.channel_id = c.id
            WHERE v.has_transcript = 1
              AND v.transcript IS NOT NULL
              AND LENGTH(v.transcript) > 0
            ORDER BY v.id
        """)
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    finally:
        conn.close()


def main():
    start_time = time.time()

    print("=" * 60)
    print("Transcript Chunking & Embedding Pipeline")
    print("=" * 60)

    # 1. Fetch videos with transcripts
    print("\n[1/4] Fetching videos with transcripts from SQLite...")
    videos = get_videos_with_transcripts()
    print(f"  Found {len(videos)} videos with transcripts")

    if not videos:
        print("  Nothing to process. Import transcripts first.")
        return

    # 2. Chunk all transcripts
    print("\n[2/4] Chunking transcripts (2000 char chunks, 200 char overlap)...")
    all_chunks = []     # (chunk_text, video_info) pairs
    video_chunk_map = [] # tracks which chunks belong to which video

    for video in videos:
        text_chunks = chunk_text(video['transcript'], chunk_size=2000, overlap=200)
        chunk_dicts = [{"text": t, "chunk_index": i} for i, t in enumerate(text_chunks)]

        video_chunk_map.append({
            "video": video,
            "chunks": chunk_dicts
        })
        all_chunks.extend([c["text"] for c in chunk_dicts])

    total_chunks = len(all_chunks)
    print(f"  Created {total_chunks} chunks from {len(videos)} videos")

    if total_chunks == 0:
        print("  No chunks created. Transcripts may be too short.")
        return

    # 3. Embed all chunks in one batch
    print(f"\n[3/4] Embedding {total_chunks} chunks (all-MiniLM-L6-v2)...")
    print("  This may take a moment on CPU...")
    embed_start = time.time()
    all_vectors = embed_batch(all_chunks, batch_size=32)
    embed_time = time.time() - embed_start
    print(f"  Embedded {len(all_vectors)} chunks in {embed_time:.1f}s ({total_chunks / embed_time:.0f} chunks/sec)")

    # 4. Store in LanceDB
    print("\n[4/4] Storing chunks in LanceDB (transcript_chunks table)...")
    db = get_db()
    total_stored = 0
    vector_offset = 0

    for entry in video_chunk_map:
        video = entry["video"]
        chunks = entry["chunks"]
        num_chunks = len(chunks)
        vectors = all_vectors[vector_offset:vector_offset + num_chunks]
        vector_offset += num_chunks

        stored = store_transcript_chunks(
            chunks=chunks,
            video_id=video['id'],
            niche_id=video['niche_id'],
            channel_id=video['channel_id'],
            vectors=vectors,
            video_title=video['title'],
            channel_name=video['channel_name'],
            published_at=video['published_at'] or "",
            view_count=video['view_count'] or 0,
            db=db
        )
        total_stored += stored

    elapsed = time.time() - start_time

    # Summary
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"  Videos processed:  {len(videos)}")
    print(f"  Chunks created:    {total_chunks}")
    print(f"  Chunks stored:     {total_stored}")
    print(f"  Embedding time:    {embed_time:.1f}s")
    print(f"  Total time:        {elapsed:.1f}s")
    print(f"  LanceDB table:     transcript_chunks")
    print("=" * 60)

    # Verify
    try:
        table = db.open_table("transcript_chunks")
        row_count = table.count_rows()
        print(f"\n  Verification: transcript_chunks has {row_count} rows in LanceDB")
    except Exception as e:
        print(f"\n  Verification error: {e}")


if __name__ == "__main__":
    main()
