"""Verify imported transcripts."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.competitor_videos import get_videos_by_niche
from src.database.niches import get_all_niches

print("=" * 80)
print("TRANSCRIPT VERIFICATION")
print("=" * 80)
print()

niches = get_all_niches()

for niche in niches:
    videos = get_videos_by_niche(niche['id'])

    with_transcript = [v for v in videos if v.get('has_transcript')]
    without_transcript = [v for v in videos if not v.get('has_transcript')]

    print(f"Niche: {niche['name']}")
    print(f"  Total videos: {len(videos)}")
    print(f"  With transcripts: {len(with_transcript)}")
    print(f"  Without transcripts: {len(without_transcript)}")

    if with_transcript:
        print()
        print("  Sample transcript (first 200 chars):")
        sample = with_transcript[0]
        transcript_preview = sample.get('transcript', '')[:200]
        print(f"    Video: {sample['title'][:50]}...")
        print(f"    Transcript: {transcript_preview}...")
    print()

print("=" * 80)
