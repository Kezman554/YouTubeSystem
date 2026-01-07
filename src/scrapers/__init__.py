"""
Scrapers package for external data collection.
"""

from .youtube import (
    YouTubeScraper,
    get_channel_info,
    get_channel_videos,
    get_video_transcript,
    download_thumbnail
)

__all__ = [
    "YouTubeScraper",
    "get_channel_info",
    "get_channel_videos",
    "get_video_transcript",
    "download_thumbnail"
]
