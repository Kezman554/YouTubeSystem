"""
YouTube scraper for competitor research.

Fetches channel info, video metadata, and thumbnails.
"""

import time
import requests
from typing import Optional
from pathlib import Path

from src.config import config


class YouTubeScraper:
    """
    YouTube scraper with rate limiting and error handling.

    Rate limit: 1 request per second for transcript API.
    YouTube Data API has 10,000 quota units/day.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize YouTube scraper.

        Args:
            api_key: YouTube Data API key (defaults to config)
        """
        self.api_key = api_key or config.youtube_api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.last_request_time = 0
        self.rate_limit_delay = 1.0  # seconds between requests

    def _rate_limit(self):
        """Enforce rate limiting (1 request per second)."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()

    def _retry_with_backoff(self, func, max_retries: int = 3, base_delay: float = 1.0):
        """
        Retry a function with exponential backoff.

        Args:
            func: Function to retry
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds (doubles each retry)

        Returns:
            Function result

        Raises:
            Exception: If all retries fail
        """
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)

    def get_channel_info(self, channel_id: str) -> dict:
        """
        Fetch channel information from YouTube Data API.

        Args:
            channel_id: YouTube channel ID

        Returns:
            Dictionary with channel data:
            - id: Channel ID
            - name: Channel name
            - subscriber_count: Number of subscribers
            - video_count: Total number of videos
            - description: Channel description
            - thumbnail_url: Channel thumbnail URL

        Raises:
            requests.HTTPError: If API request fails
            ValueError: If channel not found
        """
        self._rate_limit()

        def _fetch():
            url = f"{self.base_url}/channels"
            params = {
                "part": "snippet,statistics",
                "id": channel_id,
                "key": self.api_key
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if not data.get("items"):
                raise ValueError(f"Channel not found: {channel_id}")

            item = data["items"][0]
            snippet = item["snippet"]
            stats = item["statistics"]

            return {
                "id": channel_id,
                "name": snippet["title"],
                "subscriber_count": int(stats.get("subscriberCount", 0)),
                "video_count": int(stats.get("videoCount", 0)),
                "description": snippet.get("description", ""),
                "thumbnail_url": snippet["thumbnails"]["high"]["url"]
            }

        return self._retry_with_backoff(_fetch)

    def get_channel_videos(
        self,
        channel_id: str,
        max_results: int = 50
    ) -> list[dict]:
        """
        Fetch video list from a channel.

        Args:
            channel_id: YouTube channel ID
            max_results: Maximum number of videos to fetch (max 50 per request)

        Returns:
            List of dictionaries, each containing:
            - video_id: YouTube video ID
            - title: Video title
            - description: Video description
            - published_at: Publication date (ISO format)
            - thumbnail_url: Video thumbnail URL
            - view_count: Number of views
            - like_count: Number of likes
            - comment_count: Number of comments
            - duration: Video duration in seconds

        Raises:
            requests.HTTPError: If API request fails
            ValueError: If channel not found
        """
        videos = []
        page_token = None

        # First, get the uploads playlist ID (only done once)
        def _fetch_uploads():
            url = f"{self.base_url}/channels"
            params = {
                "part": "contentDetails",
                "id": channel_id,
                "key": self.api_key
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if not data.get("items"):
                raise ValueError(f"Channel not found: {channel_id}")

            return data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

        uploads_playlist_id = self._retry_with_backoff(_fetch_uploads)

        while len(videos) < max_results:
            self._rate_limit()

            # Fetch videos from uploads playlist
            def _fetch_page():
                url = f"{self.base_url}/playlistItems"
                params = {
                    "part": "snippet,contentDetails",
                    "playlistId": uploads_playlist_id,
                    "maxResults": min(50, max_results - len(videos)),
                    "key": self.api_key
                }

                if page_token:
                    params["pageToken"] = page_token

                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                return response.json()

            page_data = self._retry_with_backoff(_fetch_page)

            if not page_data.get("items"):
                break

            # Extract video IDs for detailed info
            video_ids = [
                item["contentDetails"]["videoId"]
                for item in page_data["items"]
            ]

            # Fetch detailed video info
            self._rate_limit()

            def _fetch_details():
                url = f"{self.base_url}/videos"
                params = {
                    "part": "snippet,statistics,contentDetails",
                    "id": ",".join(video_ids),
                    "key": self.api_key
                }

                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                return response.json()

            details_data = self._retry_with_backoff(_fetch_details)

            for item in details_data.get("items", []):
                snippet = item["snippet"]
                stats = item.get("statistics", {})
                content_details = item["contentDetails"]

                # Parse ISO 8601 duration (PT1H2M10S -> seconds)
                duration = self._parse_duration(content_details.get("duration", "PT0S"))

                videos.append({
                    "video_id": item["id"],
                    "title": snippet["title"],
                    "description": snippet.get("description", ""),
                    "published_at": snippet["publishedAt"],
                    "thumbnail_url": snippet["thumbnails"]["high"]["url"],
                    "view_count": int(stats.get("viewCount", 0)),
                    "like_count": int(stats.get("likeCount", 0)),
                    "comment_count": int(stats.get("commentCount", 0)),
                    "duration": duration
                })

            # Check for next page
            page_token = page_data.get("nextPageToken")
            if not page_token or len(videos) >= max_results:
                break

        return videos[:max_results]

    def _parse_duration(self, duration_str: str) -> int:
        """
        Parse ISO 8601 duration to seconds.

        Args:
            duration_str: ISO 8601 duration (e.g., "PT1H2M10S")

        Returns:
            Duration in seconds
        """
        import re

        # PT1H2M10S -> 1 hour, 2 minutes, 10 seconds
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
        if not match:
            return 0

        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)

        return hours * 3600 + minutes * 60 + seconds

    def get_video_transcript(self, video_id: str) -> Optional[str]:
        """
        Fetch transcript for a video.

        Args:
            video_id: YouTube video ID

        Returns:
            None - transcript fetching is currently disabled

        Note:
            TODO: Implement transcript fetching when YouTube API access is resolved.
            YouTube has blocked unauthenticated transcript requests.
            For now, transcripts will be gathered manually.
        """
        # Transcript fetching disabled - YouTube blocks unauthenticated requests
        return None

    def download_thumbnail(
        self,
        video_id: str,
        save_path: Path
    ) -> Optional[Path]:
        """
        Download video thumbnail to specified path.

        Args:
            video_id: YouTube video ID
            save_path: Path where thumbnail should be saved

        Returns:
            Path to saved thumbnail, or None if download fails

        Note:
            Tries high quality (maxresdefault) first, falls back to hqdefault.
        """
        self._rate_limit()

        # Create parent directory if needed
        save_path.parent.mkdir(parents=True, exist_ok=True)

        # Try high quality first, then fall back
        urls = [
            f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg",
            f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
        ]

        for url in urls:
            try:
                def _download():
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()

                    # Check if we got an actual image (not placeholder)
                    if len(response.content) < 1000:
                        # Likely a placeholder, try next quality
                        raise ValueError("Thumbnail too small")

                    with open(save_path, 'wb') as f:
                        f.write(response.content)

                    return save_path

                return self._retry_with_backoff(_download, max_retries=2)

            except Exception:
                # Try next quality level
                continue

        return None


# Convenience functions for one-off usage
def get_channel_info(channel_id: str) -> dict:
    """Fetch channel info using default scraper."""
    scraper = YouTubeScraper()
    return scraper.get_channel_info(channel_id)


def get_channel_videos(channel_id: str, max_results: int = 50) -> list[dict]:
    """Fetch channel videos using default scraper."""
    scraper = YouTubeScraper()
    return scraper.get_channel_videos(channel_id, max_results)


def get_video_transcript(video_id: str) -> Optional[str]:
    """Fetch video transcript using default scraper."""
    scraper = YouTubeScraper()
    return scraper.get_video_transcript(video_id)


def download_thumbnail(video_id: str, save_path: Path) -> Optional[Path]:
    """Download thumbnail using default scraper."""
    scraper = YouTubeScraper()
    return scraper.download_thumbnail(video_id, save_path)
