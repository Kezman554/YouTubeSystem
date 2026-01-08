"""
Import transcripts from text files into the database.

Scans data/transcripts/ for .txt files with content and imports them
into the competitor_videos table.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.competitor_videos import (
    get_competitor_video_by_youtube_id,
    update_competitor_video
)


def main():
    print("=" * 80)
    print("IMPORTING TRANSCRIPTS")
    print("=" * 80)
    print()

    # Locate transcripts directory
    transcripts_dir = Path(__file__).parent.parent / "data" / "transcripts"

    if not transcripts_dir.exists():
        print(f"ERROR: Transcripts directory not found: {transcripts_dir}")
        return

    print(f"Scanning: {transcripts_dir}")
    print()

    # Find all .txt files
    transcript_files = list(transcripts_dir.glob("*.txt"))
    print(f"Found {len(transcript_files)} transcript files")
    print()

    # Import transcripts
    print("Processing transcripts...")
    imported_count = 0
    skipped_empty = 0
    skipped_no_video = 0
    error_count = 0

    for i, file_path in enumerate(transcript_files, 1):
        # Extract video ID from filename (remove .txt extension)
        video_id = file_path.stem

        # Check if file has content
        try:
            content = file_path.read_text(encoding='utf-8').strip()
        except Exception as e:
            print(f"  ERROR reading {video_id}: {e}")
            error_count += 1
            continue

        if not content:
            skipped_empty += 1
            continue

        # Find matching video in database
        video = get_competitor_video_by_youtube_id(video_id)

        if not video:
            print(f"  WARNING: No video found for {video_id}")
            skipped_no_video += 1
            continue

        # Check if transcript already imported
        if video.get('transcript'):
            # Transcript already exists, skip
            continue

        # Import transcript
        try:
            update_competitor_video(
                video['id'],
                transcript=content,
                has_transcript=True
            )
            imported_count += 1

            # Progress indicator every 10 imports
            if imported_count % 10 == 0:
                print(f"  Imported {imported_count} transcripts...")

        except Exception as e:
            print(f"  ERROR importing {video_id}: {e}")
            error_count += 1

    print()
    print("=" * 80)
    print("IMPORT COMPLETE")
    print("=" * 80)
    print()
    print(f"Transcripts imported:     {imported_count}")
    print(f"Skipped (empty files):    {skipped_empty}")
    print(f"Skipped (no matching video): {skipped_no_video}")
    if error_count > 0:
        print(f"Errors:                   {error_count}")
    print()


if __name__ == "__main__":
    main()
