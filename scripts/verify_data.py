"""Verify scraped data in database."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.niches import get_all_niches
from src.database.competitor_channels import get_channels_by_niche
from src.database.competitor_videos import get_videos_by_channel

print("=" * 80)
print("DATABASE VERIFICATION")
print("=" * 80)
print()

# Check niches
niches = get_all_niches()
print(f"Niches in database: {len(niches)}")
for niche in niches:
    print(f"  - {niche['name']} (ID: {niche['id']}, slug: {niche['slug']})")
print()

# Check channels
for niche in niches:
    channels = get_channels_by_niche(niche['id'])
    print(f"Channels in {niche['name']}: {len(channels)}")

    for channel in channels:
        print(f"  - {channel['name']}")
        print(f"    YouTube ID: {channel['youtube_id']}")
        print(f"    Subscribers: {channel['subscriber_count']:,}")
        print(f"    Total videos on YouTube: {channel['video_count']:,}")

        # Count videos in database
        videos = get_videos_by_channel(channel['id'])
        print(f"    Videos in database: {len(videos)}")

        # Show some stats
        if videos:
            total_views = sum(v['view_count'] or 0 for v in videos)
            avg_views = total_views // len(videos) if videos else 0
            print(f"    Total views (scraped videos): {total_views:,}")
            print(f"    Average views per video: {avg_views:,}")
        print()

print("=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)
