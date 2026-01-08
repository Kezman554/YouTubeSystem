"""
Find a YouTube channel by searching.

Usage:
    python scripts/find_channel.py "Nerd of the Rings"
"""

import sys
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import config


def search_channel(query: str):
    """Search for a YouTube channel by name."""
    api_key = config.youtube_api_key
    base_url = "https://www.googleapis.com/youtube/v3"

    print(f"Searching for: {query}")
    print()

    try:
        # Search for channels
        url = f"{base_url}/search"
        params = {
            "part": "snippet",
            "q": query,
            "type": "channel",
            "maxResults": 5,
            "key": api_key
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data.get("items"):
            print("No channels found.")
            return

        print(f"Found {len(data['items'])} channels:")
        print()

        for i, item in enumerate(data['items'], 1):
            channel_id = item['id']['channelId']
            title = item['snippet']['title']
            description = item['snippet']['description']

            print(f"{i}. {title}")
            print(f"   Channel ID: {channel_id}")
            print(f"   Description: {description[:100]}...")
            print()

            # Get detailed channel info
            detail_url = f"{base_url}/channels"
            detail_params = {
                "part": "statistics",
                "id": channel_id,
                "key": api_key
            }

            detail_response = requests.get(detail_url, params=detail_params, timeout=10)
            detail_response.raise_for_status()
            detail_data = detail_response.json()

            if detail_data.get("items"):
                stats = detail_data['items'][0]['statistics']
                print(f"   Subscribers: {int(stats.get('subscriberCount', 0)):,}")
                print(f"   Videos: {int(stats.get('videoCount', 0)):,}")
                print()

    except requests.HTTPError as e:
        print(f"ERROR: {e}")
        print()
        print("Make sure:")
        print("  1. Your YouTube API key is configured in .env")
        print("  2. YouTube Data API v3 is enabled")
    except Exception as e:
        print(f"ERROR: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/find_channel.py \"channel name\"")
        sys.exit(1)

    search_channel(" ".join(sys.argv[1:]))
