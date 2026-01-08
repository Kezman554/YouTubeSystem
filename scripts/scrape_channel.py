"""
General YouTube channel scraper.

Scrapes any YouTube channel and saves to the database.

Usage:
    python scripts/scrape_channel.py <channel_id> [--niche-id NICHE_ID] [--max-videos MAX]

Examples:
    # Scrape with explicit niche ID
    python scripts/scrape_channel.py UCX7nBb2Pc0YILetEM4qz2LQ --niche-id 1

    # Scrape with URL
    python scripts/scrape_channel.py "https://youtube.com/@NerdoftheRings" --niche-id 1

    # Limit number of videos
    python scripts/scrape_channel.py UCX7nBb2Pc0YILetEM4qz2LQ --niche-id 1 --max-videos 50
"""

import sys
import argparse
import re
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scrapers.youtube import YouTubeScraper
from src.database.niches import get_all_niches, get_niche
from src.database.competitor_channels import (
    create_competitor_channel,
    get_competitor_channel_by_youtube_id,
    update_competitor_channel,
    mark_as_scraped
)
from src.database.competitor_videos import (
    create_competitor_video,
    get_competitor_video_by_youtube_id,
    update_competitor_video
)


def extract_channel_id(channel_input: str) -> str:
    """
    Extract channel ID from various input formats.

    Args:
        channel_input: Channel ID, URL, or handle

    Returns:
        Channel ID (starting with UC)

    Raises:
        ValueError: If channel ID cannot be extracted
    """
    # Already a channel ID
    if re.match(r'^UC[\w-]{22}$', channel_input):
        return channel_input

    # Extract from URL patterns
    patterns = [
        r'youtube\.com/channel/(UC[\w-]{22})',
        r'youtube\.com/@([\w-]+)',
        r'youtube\.com/c/([\w-]+)',
        r'youtube\.com/user/([\w-]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, channel_input)
        if match:
            # If it's a UC ID, return it
            if match.group(1).startswith('UC'):
                return match.group(1)
            # Otherwise it's a handle/username, can't resolve without API
            raise ValueError(
                f"Cannot resolve handle/username '{match.group(1)}' to channel ID. "
                "Please provide the full channel ID (starts with UC)."
            )

    raise ValueError(
        f"Could not extract channel ID from '{channel_input}'. "
        "Please provide a valid channel ID (starting with UC) or channel URL."
    )


def main():
    parser = argparse.ArgumentParser(
        description="Scrape a YouTube channel and save to database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        'channel',
        help='YouTube channel ID or URL'
    )
    parser.add_argument(
        '--niche-id',
        type=int,
        required=True,
        help='Niche ID to associate this channel with'
    )
    parser.add_argument(
        '--max-videos',
        type=int,
        default=None,
        help='Maximum number of videos to scrape (default: all)'
    )
    parser.add_argument(
        '--list-niches',
        action='store_true',
        help='List all available niches and exit'
    )

    args = parser.parse_args()

    # List niches if requested
    if args.list_niches:
        print("Available niches:")
        print()
        niches = get_all_niches()
        if not niches:
            print("  No niches found. Create one first!")
        for niche in niches:
            print(f"  ID {niche['id']}: {niche['name']} ({niche['slug']})")
        return

    print("=" * 80)
    print("YOUTUBE CHANNEL SCRAPER")
    print("=" * 80)
    print()

    # Extract channel ID
    try:
        channel_id = extract_channel_id(args.channel)
        print(f"Channel ID: {channel_id}")
    except ValueError as e:
        print(f"ERROR: {e}")
        return 1

    # Verify niche exists
    niche = get_niche(args.niche_id)
    if not niche:
        print(f"ERROR: Niche with ID {args.niche_id} not found")
        print()
        print("Available niches:")
        niches = get_all_niches()
        for n in niches:
            print(f"  ID {n['id']}: {n['name']}")
        print()
        print("Use --list-niches to see all niches")
        return 1

    print(f"Niche: {niche['name']}")
    print()

    # Initialize scraper
    scraper = YouTubeScraper()

    # Fetch channel info
    print("-" * 80)
    print("Fetching channel info...")
    try:
        channel_info = scraper.get_channel_info(channel_id)
    except Exception as e:
        print(f"ERROR: Failed to fetch channel info: {e}")
        return 1

    print(f"  Name: {channel_info['name']}")
    print(f"  Subscribers: {channel_info['subscriber_count']:,}")
    print(f"  Videos: {channel_info['video_count']:,}")
    print()

    # Save or update channel
    print("-" * 80)
    print("Saving channel to database...")
    existing_channel = get_competitor_channel_by_youtube_id(channel_id)

    if existing_channel:
        db_channel_id = existing_channel['id']
        print(f"  Channel already exists (DB ID: {db_channel_id})")
        print(f"  Updating channel info...")
        update_competitor_channel(
            db_channel_id,
            name=channel_info['name'],
            url=f"https://youtube.com/channel/{channel_id}",
            subscriber_count=channel_info['subscriber_count'],
            video_count=channel_info['video_count']
        )
    else:
        db_channel_id = create_competitor_channel(
            niche_id=args.niche_id,
            youtube_id=channel_id,
            name=channel_info['name'],
            url=f"https://youtube.com/channel/{channel_id}",
            subscriber_count=channel_info['subscriber_count'],
            video_count=channel_info['video_count']
        )
        print(f"  Created new channel (DB ID: {db_channel_id})")
    print()

    # Determine how many videos to fetch
    max_videos = args.max_videos if args.max_videos else channel_info['video_count']

    # Scrape videos
    print("-" * 80)
    print(f"Scraping videos (max: {max_videos})...")
    print("This may take a few minutes depending on the channel size...")
    print()

    try:
        videos = scraper.get_channel_videos(channel_id, max_results=max_videos)
    except Exception as e:
        print(f"ERROR: Failed to fetch videos: {e}")
        return 1

    print(f"Fetched {len(videos)} videos")
    print()

    # Save videos to database
    print("Saving videos to database...")
    new_count = 0
    updated_count = 0
    error_count = 0

    for i, video in enumerate(videos, 1):
        try:
            existing_video = get_competitor_video_by_youtube_id(video['video_id'])

            if existing_video:
                # Update existing video
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
                # Create new video
                create_competitor_video(
                    channel_id=db_channel_id,
                    niche_id=args.niche_id,
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

            # Progress indicator
            if i % 10 == 0:
                print(f"  Processed {i}/{len(videos)} videos...")

        except Exception as e:
            print(f"  ERROR saving video {video['video_id']}: {e}")
            error_count += 1

    # Mark channel as scraped
    mark_as_scraped(db_channel_id)

    # Summary
    print()
    print("=" * 80)
    print("SCRAPING COMPLETE")
    print("=" * 80)
    print()
    print(f"Channel: {channel_info['name']}")
    print(f"Niche: {niche['name']}")
    print()
    print(f"New videos saved:     {new_count}")
    print(f"Existing videos updated: {updated_count}")
    if error_count > 0:
        print(f"Errors:                {error_count}")
    print(f"TOTAL VIDEOS IN DB:    {new_count + updated_count}")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
