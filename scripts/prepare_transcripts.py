"""
Prepare transcript placeholder files for all videos in database.

Creates empty .txt files in data/transcripts/ for each video,
named by their YouTube video ID.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.competitor_videos import get_videos_by_niche
from src.database.niches import get_all_niches


def main():
    print("=" * 80)
    print("PREPARING TRANSCRIPT FILES")
    print("=" * 80)
    print()

    # Create transcripts directory
    transcripts_dir = Path(__file__).parent.parent / "data" / "transcripts"
    transcripts_dir.mkdir(parents=True, exist_ok=True)
    print(f"Transcripts directory: {transcripts_dir}")
    print()

    # Get all videos from all niches
    print("Loading videos from database...")
    all_videos = []
    niches = get_all_niches()

    for niche in niches:
        videos = get_videos_by_niche(niche['id'])
        all_videos.extend(videos)
        print(f"  {niche['name']}: {len(videos)} videos")

    print()
    print(f"Total videos in database: {len(all_videos)}")
    print()

    # Create transcript files
    print("Creating transcript files...")
    created_count = 0
    skipped_count = 0

    for video in all_videos:
        video_id = video['youtube_id']
        transcript_file = transcripts_dir / f"{video_id}.txt"

        if transcript_file.exists():
            skipped_count += 1
        else:
            # Create empty file
            transcript_file.touch()
            created_count += 1

        # Progress indicator every 50 videos
        total_processed = created_count + skipped_count
        if total_processed % 50 == 0:
            print(f"  Processed {total_processed}/{len(all_videos)} videos...")

    print()
    print("=" * 80)
    print("COMPLETE")
    print("=" * 80)
    print()
    print(f"Files created:  {created_count}")
    print(f"Files skipped:  {skipped_count} (already existed)")
    print(f"Total files:    {created_count + skipped_count}")
    print()
    print(f"Location: {transcripts_dir}")
    print()


if __name__ == "__main__":
    main()
