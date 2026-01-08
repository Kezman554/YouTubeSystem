"""
One-time script to populate test data.

Creates a Middle-earth niche and scrapes Nerd of the Rings channel.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scrapers.youtube import YouTubeScraper
from src.database.niches import get_all_niches, create_niche
from src.database.competitor_channels import (
    create_competitor_channel,
    get_competitor_channel_by_youtube_id,
    update_competitor_channel,
    mark_as_scraped
)
from src.database.competitor_videos import (
    create_competitor_video,
    get_competitor_video_by_youtube_id,
    update_competitor_video,
    get_videos_by_channel
)


def setup_middle_earth_niche():
    """Get or create Middle-earth niche."""
    print("=" * 80)
    print("SETTING UP MIDDLE-EARTH NICHE")
    print("=" * 80)
    print()

    niches = get_all_niches()
    for niche in niches:
        if niche['slug'] == 'middle-earth':
            print(f"Middle-earth niche already exists (ID: {niche['id']})")
            return niche['id']

    niche_id = create_niche(
        name="Middle-earth",
        slug="middle-earth",
        niche_type="fiction",
        description="J.R.R. Tolkien's fantasy universe - Lord of the Rings and related lore"
    )
    print(f"Created Middle-earth niche (ID: {niche_id})")
    return niche_id


def scrape_nerd_of_rings(niche_id: int, max_videos: int = 100):
    """Scrape Nerd of the Rings channel."""
    print()
    print("=" * 80)
    print("SCRAPING NERD OF THE RINGS")
    print("=" * 80)
    print()

    # Nerd of the Rings channel ID
    # This is the official channel ID for @NerdoftheRings
    channel_id = "UCW0gH2G-cMKAEjEkI4YhnPA"

    scraper = YouTubeScraper()

    # Fetch channel info
    print("Fetching channel info...")
    try:
        channel_info = scraper.get_channel_info(channel_id)
    except Exception as e:
        print(f"ERROR: Failed to fetch channel: {e}")
        print()
        print("Possible issues:")
        print("  1. YouTube API key not configured or invalid")
        print("  2. API quota exceeded")
        print("  3. Channel ID is incorrect")
        return 0

    print(f"  Name: {channel_info['name']}")
    print(f"  Subscribers: {channel_info['subscriber_count']:,}")
    print(f"  Videos: {channel_info['video_count']:,}")
    print()

    # Save or update channel
    print("Saving channel to database...")
    existing_channel = get_competitor_channel_by_youtube_id(channel_id)

    if existing_channel:
        db_channel_id = existing_channel['id']
        print(f"  Channel already exists (DB ID: {db_channel_id})")
        print(f"  Updating channel info...")
        update_competitor_channel(
            db_channel_id,
            name=channel_info['name'],
            subscriber_count=channel_info['subscriber_count'],
            video_count=channel_info['video_count']
        )
    else:
        db_channel_id = create_competitor_channel(
            niche_id=niche_id,
            youtube_id=channel_id,
            name=channel_info['name'],
            url=f"https://youtube.com/@NerdoftheRings",
            subscriber_count=channel_info['subscriber_count'],
            video_count=channel_info['video_count']
        )
        print(f"  Created new channel (DB ID: {db_channel_id})")
    print()

    # Scrape videos
    print(f"Scraping up to {max_videos} videos...")
    print("(This may take a few minutes...)")
    print()

    try:
        videos = scraper.get_channel_videos(channel_id, max_results=max_videos)
    except Exception as e:
        print(f"ERROR: Failed to fetch videos: {e}")
        return 0

    print(f"Fetched {len(videos)} videos")
    print()

    # Save videos to database
    print("Saving videos to database...")
    new_count = 0
    updated_count = 0

    for i, video in enumerate(videos, 1):
        try:
            existing_video = get_competitor_video_by_youtube_id(video['video_id'])

            if existing_video:
                update_competitor_video(
                    existing_video['id'],
                    title=video['title'],
                    description=video['description'],
                    view_count=video['view_count'],
                    like_count=video['like_count'],
                    comment_count=video['comment_count']
                )
                updated_count += 1
            else:
                create_competitor_video(
                    channel_id=db_channel_id,
                    niche_id=niche_id,
                    youtube_id=video['video_id'],
                    title=video['title'],
                    description=video['description'],
                    published_at=video['published_at'],
                    duration_seconds=video['duration'],
                    view_count=video['view_count'],
                    like_count=video['like_count'],
                    comment_count=video['comment_count'],
                    thumbnail_url=video['thumbnail_url']
                )
                new_count += 1

            if i % 10 == 0:
                print(f"  Processed {i}/{len(videos)} videos...")

        except Exception as e:
            print(f"  ERROR saving video {video.get('video_id', 'unknown')}: {e}")

    mark_as_scraped(db_channel_id)

    print()
    print(f"New videos saved:         {new_count}")
    print(f"Existing videos updated:  {updated_count}")
    print(f"Total videos in database: {new_count + updated_count}")

    return new_count + updated_count


def main():
    print()
    print("*" * 80)
    print("TEST DATA SETUP")
    print("*" * 80)
    print()

    # Step 1: Create niche
    niche_id = setup_middle_earth_niche()

    # Step 2: Scrape channel
    total_videos = scrape_nerd_of_rings(niche_id, max_videos=100)

    # Summary
    print()
    print("=" * 80)
    print("SETUP COMPLETE")
    print("=" * 80)
    print()
    print(f"[OK] Middle-earth niche created (ID: {niche_id})")
    print(f"[OK] Nerd of the Rings channel scraped")
    print(f"[OK] {total_videos} videos saved to database")
    print()


if __name__ == "__main__":
    main()
