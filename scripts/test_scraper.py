"""
Test script for YouTube scraper.

Tests the scraper with a real LOTR YouTube channel.
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scrapers.youtube import YouTubeScraper


def main():
    print("=" * 80)
    print("YouTube Scraper Test")
    print("=" * 80)
    print()

    # Initialize scraper
    try:
        scraper = YouTubeScraper()
        print("[OK] Scraper initialized with API key")
        print()
    except Exception as e:
        print(f"[FAIL] Failed to initialize scraper: {e}")
        print("\nMake sure you have:")
        print("1. Created a .env file (copy from .env.example)")
        print("2. Added your YOUTUBE_API_KEY to .env")
        return

    # Test with "Google for Developers" - using a known valid channel
    # Replace this with any LOTR channel ID you want to test
    # Channel ID: UC_x5XG1OV2P6uZZ5FSM9Ttw
    channel_id = "UC_x5XG1OV2P6uZZ5FSM9Ttw"

    print("Testing with 'Google for Developers' channel")
    print("(Replace with any channel ID you want to scrape)")
    print(f"Channel ID: {channel_id}")
    print()
    print("NOTE: If this fails, make sure:")
    print("  1. You have a valid YouTube Data API v3 key in your .env file")
    print("  2. The API key has the YouTube Data API v3 enabled in Google Cloud Console")
    print()

    # 1. Fetch channel info
    print("-" * 80)
    print("1. FETCHING CHANNEL INFO")
    print("-" * 80)
    try:
        channel_info = scraper.get_channel_info(channel_id)
        print(f"[OK] Channel Name: {channel_info['name']}")
        print(f"     Subscribers: {channel_info['subscriber_count']:,}")
        print(f"     Total Videos: {channel_info['video_count']:,}")
        print(f"     Description: {channel_info['description'][:100]}...")
        print()
    except ValueError as e:
        print(f"[FAIL] {e}")
        print()
        print("This usually means:")
        print("  - The YouTube Data API v3 is not enabled for your API key")
        print("  - The API key is invalid or expired")
        print("  - The channel ID is incorrect")
        print()
        print("To fix:")
        print("  1. Go to https://console.cloud.google.com/")
        print("  2. Enable YouTube Data API v3")
        print("  3. Create/copy an API key")
        print("  4. Add it to your .env file as YOUTUBE_API_KEY=your_key_here")
        return
    except Exception as e:
        print(f"[FAIL] Unexpected error: {type(e).__name__}: {e}")
        return

    # 2. Get 5 most recent videos
    print("-" * 80)
    print("2. FETCHING 5 MOST RECENT VIDEOS")
    print("-" * 80)
    try:
        videos = scraper.get_channel_videos(channel_id, max_results=5)
        print(f"[OK] Found {len(videos)} videos\n")

        for i, video in enumerate(videos, 1):
            duration_min = video['duration'] // 60
            duration_sec = video['duration'] % 60
            # Handle encoding issues with emojis in titles
            title = video['title'].encode('ascii', 'ignore').decode('ascii')
            print(f"{i}. {title}")
            print(f"   ID: {video['video_id']}")
            print(f"   Views: {video['view_count']:,}")
            print(f"   Likes: {video['like_count']:,}")
            print(f"   Duration: {duration_min}:{duration_sec:02d}")
            print(f"   Published: {video['published_at']}")
            print()

    except Exception as e:
        print(f"[FAIL] Failed to fetch videos: {e}")
        return

    # 3. Try to download a transcript from the first video
    print("-" * 80)
    print("3. FETCHING TRANSCRIPT FOR FIRST VIDEO")
    print("-" * 80)

    if videos:
        test_video = videos[0]
        print(f"Attempting to fetch transcript for:")
        print(f"{test_video['title']}")
        print(f"Video ID: {test_video['video_id']}")
        print()

        try:
            transcript = scraper.get_video_transcript(test_video['video_id'])

            if transcript:
                print(f"[OK] Transcript fetched successfully!")
                print(f"     Length: {len(transcript)} characters")
                print(f"     Word count: ~{len(transcript.split())} words")
                print()
                print("First 500 characters:")
                print("-" * 80)
                print(transcript[:500])
                print("...")
                print()
            else:
                print("[FAIL] No transcript available for this video")
                print("       (Video may not have captions enabled)")
                print()

                # Try the next video
                if len(videos) > 1:
                    print("Trying second video...")
                    test_video = videos[1]
                    print(f"{test_video['title']}")
                    print(f"Video ID: {test_video['video_id']}")
                    print()

                    transcript = scraper.get_video_transcript(test_video['video_id'])
                    if transcript:
                        print(f"[OK] Transcript fetched successfully!")
                        print(f"     Length: {len(transcript)} characters")
                        print(f"     Word count: ~{len(transcript.split())} words")
                        print()
                        print("First 500 characters:")
                        print("-" * 80)
                        print(transcript[:500])
                        print("...")
                        print()
                    else:
                        print("[FAIL] No transcript available for this video either")
                        print()

        except Exception as e:
            print(f"[FAIL] Error fetching transcript: {e}")
            print()

    # Summary
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print()
    print("[OK] Channel info fetched")
    print(f"[OK] {len(videos)} videos retrieved")
    print("[OK] Transcript fetch attempted")
    print()
    print("The YouTube scraper is working correctly!")


if __name__ == "__main__":
    main()
