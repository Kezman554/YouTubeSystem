"""
Tests for YouTube scraper with mocked API responses.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound
)

from src.scrapers.youtube import YouTubeScraper


@pytest.fixture
def scraper():
    """Create a YouTube scraper instance with test API key."""
    return YouTubeScraper(api_key="test_api_key")


@pytest.fixture
def mock_channel_response():
    """Mock response for channel info API."""
    return {
        "items": [{
            "id": "UC_test_channel",
            "snippet": {
                "title": "Test Channel",
                "description": "A test channel description",
                "thumbnails": {
                    "high": {
                        "url": "https://example.com/channel_thumb.jpg"
                    }
                }
            },
            "statistics": {
                "subscriberCount": "150000",
                "videoCount": "250"
            }
        }]
    }


@pytest.fixture
def mock_playlist_response():
    """Mock response for uploads playlist."""
    return {
        "items": [{
            "contentDetails": {
                "relatedPlaylists": {
                    "uploads": "UU_test_playlist"
                }
            }
        }]
    }


@pytest.fixture
def mock_playlist_items_response():
    """Mock response for playlist items."""
    return {
        "items": [
            {
                "contentDetails": {
                    "videoId": "video_1"
                }
            },
            {
                "contentDetails": {
                    "videoId": "video_2"
                }
            }
        ]
    }


@pytest.fixture
def mock_videos_response():
    """Mock response for videos details."""
    return {
        "items": [
            {
                "id": "video_1",
                "snippet": {
                    "title": "Test Video 1",
                    "description": "Description 1",
                    "publishedAt": "2024-01-01T12:00:00Z",
                    "thumbnails": {
                        "high": {
                            "url": "https://example.com/thumb1.jpg"
                        }
                    }
                },
                "statistics": {
                    "viewCount": "10000",
                    "likeCount": "500",
                    "commentCount": "50"
                },
                "contentDetails": {
                    "duration": "PT10M30S"
                }
            },
            {
                "id": "video_2",
                "snippet": {
                    "title": "Test Video 2",
                    "description": "Description 2",
                    "publishedAt": "2024-01-02T12:00:00Z",
                    "thumbnails": {
                        "high": {
                            "url": "https://example.com/thumb2.jpg"
                        }
                    }
                },
                "statistics": {
                    "viewCount": "5000",
                    "likeCount": "200",
                    "commentCount": "25"
                },
                "contentDetails": {
                    "duration": "PT5M15S"
                }
            }
        ]
    }


class TestGetChannelInfo:
    """Test fetching channel information."""

    @patch('src.scrapers.youtube.requests.get')
    def test_get_channel_info_success(self, mock_get, scraper, mock_channel_response):
        """Successfully fetch channel info."""
        mock_response = Mock()
        mock_response.json.return_value = mock_channel_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = scraper.get_channel_info("UC_test_channel")

        assert result["id"] == "UC_test_channel"
        assert result["name"] == "Test Channel"
        assert result["subscriber_count"] == 150000
        assert result["video_count"] == 250
        assert result["description"] == "A test channel description"
        assert "channel_thumb.jpg" in result["thumbnail_url"]

    @patch('src.scrapers.youtube.requests.get')
    def test_get_channel_info_not_found(self, mock_get, scraper):
        """Handle channel not found."""
        mock_response = Mock()
        mock_response.json.return_value = {"items": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with pytest.raises(ValueError, match="Channel not found"):
            scraper.get_channel_info("invalid_channel")

    @patch('src.scrapers.youtube.requests.get')
    @patch('src.scrapers.youtube.time.sleep')
    def test_get_channel_info_with_retry(self, mock_sleep, mock_get, scraper, mock_channel_response):
        """Retry on failure then succeed."""
        # First call fails, second succeeds
        mock_response_fail = Mock()
        mock_response_fail.raise_for_status.side_effect = Exception("API Error")

        mock_response_success = Mock()
        mock_response_success.json.return_value = mock_channel_response
        mock_response_success.raise_for_status = Mock()

        mock_get.side_effect = [mock_response_fail, mock_response_success]

        result = scraper.get_channel_info("UC_test_channel")

        assert result["name"] == "Test Channel"
        assert mock_get.call_count == 2
        assert mock_sleep.called


class TestGetChannelVideos:
    """Test fetching channel videos."""

    @patch('src.scrapers.youtube.requests.get')
    def test_get_channel_videos_success(
        self,
        mock_get,
        scraper,
        mock_playlist_response,
        mock_playlist_items_response,
        mock_videos_response
    ):
        """Successfully fetch channel videos."""
        # Mock sequence: channels (for playlist), playlistItems, videos
        # Each operation may be retried, so we provide responses that always succeed

        def create_mock_response(json_data):
            mock_response = Mock()
            mock_response.json.return_value = json_data
            mock_response.raise_for_status = Mock()
            return mock_response

        # Provide enough responses for all calls (including potential retries)
        # But since our responses succeed, no retries should happen
        mock_get.side_effect = [
            create_mock_response(mock_playlist_response),  # Get uploads playlist ID
            create_mock_response(mock_playlist_items_response),  # Get video IDs from playlist
            create_mock_response(mock_videos_response)  # Get video details
        ]

        result = scraper.get_channel_videos("UC_test_channel", max_results=10)

        assert len(result) == 2
        assert result[0]["video_id"] == "video_1"
        assert result[0]["title"] == "Test Video 1"
        assert result[0]["view_count"] == 10000
        assert result[0]["duration"] == 630  # 10 minutes 30 seconds

        assert result[1]["video_id"] == "video_2"
        assert result[1]["title"] == "Test Video 2"
        assert result[1]["duration"] == 315  # 5 minutes 15 seconds

    @patch('src.scrapers.youtube.requests.get')
    def test_get_channel_videos_empty_channel(self, mock_get, scraper, mock_playlist_response):
        """Handle channel with no videos."""
        def create_mock_response(json_data):
            mock_response = Mock()
            mock_response.json.return_value = json_data
            mock_response.raise_for_status = Mock()
            return mock_response

        mock_get.side_effect = [
            create_mock_response(mock_playlist_response),  # Get uploads playlist ID
            create_mock_response({"items": []})  # No videos in playlist
        ]

        result = scraper.get_channel_videos("UC_test_channel")

        assert result == []


class TestParseDuration:
    """Test ISO 8601 duration parsing."""

    def test_parse_duration_hours_minutes_seconds(self, scraper):
        """Parse duration with hours, minutes, and seconds."""
        assert scraper._parse_duration("PT1H2M10S") == 3730

    def test_parse_duration_minutes_seconds(self, scraper):
        """Parse duration with minutes and seconds only."""
        assert scraper._parse_duration("PT5M30S") == 330

    def test_parse_duration_seconds_only(self, scraper):
        """Parse duration with seconds only."""
        assert scraper._parse_duration("PT45S") == 45

    def test_parse_duration_hours_only(self, scraper):
        """Parse duration with hours only."""
        assert scraper._parse_duration("PT2H") == 7200

    def test_parse_duration_invalid(self, scraper):
        """Handle invalid duration format."""
        assert scraper._parse_duration("invalid") == 0


class TestGetVideoTranscript:
    """Test fetching video transcripts."""

    @patch('youtube_transcript_api.YouTubeTranscriptApi.fetch')
    def test_get_transcript_success(self, mock_fetch, scraper):
        """Successfully fetch transcript."""
        mock_fetch.return_value = [
            {"text": "Hello", "start": 0.0, "duration": 1.0},
            {"text": "world", "start": 1.0, "duration": 1.0},
            {"text": "from", "start": 2.0, "duration": 1.0},
            {"text": "YouTube", "start": 3.0, "duration": 1.0}
        ]

        result = scraper.get_video_transcript("test_video")

        assert result == "Hello world from YouTube"
        assert mock_fetch.called

    @patch('youtube_transcript_api.YouTubeTranscriptApi.fetch')
    def test_get_transcript_disabled(self, mock_fetch, scraper):
        """Handle transcripts disabled."""
        mock_fetch.side_effect = TranscriptsDisabled("video_id")

        result = scraper.get_video_transcript("test_video")

        assert result is None

    @patch('youtube_transcript_api.YouTubeTranscriptApi.fetch')
    def test_get_transcript_not_found(self, mock_fetch, scraper):
        """Handle transcript not found."""
        mock_fetch.side_effect = NoTranscriptFound("video_id", [], [])

        result = scraper.get_video_transcript("test_video")

        assert result is None

    @patch('youtube_transcript_api.YouTubeTranscriptApi.fetch')
    @patch('src.scrapers.youtube.time.sleep')
    def test_get_transcript_with_retry(self, mock_sleep, mock_fetch, scraper):
        """Retry on transient failure."""
        # First call fails, second succeeds
        mock_fetch.side_effect = [
            Exception("Transient error"),
            [{"text": "Success", "start": 0.0, "duration": 1.0}]
        ]

        result = scraper.get_video_transcript("test_video")

        assert result == "Success"
        assert mock_fetch.call_count == 2


class TestDownloadThumbnail:
    """Test downloading video thumbnails."""

    @patch('src.scrapers.youtube.requests.get')
    def test_download_thumbnail_success(self, mock_get, scraper, tmp_path):
        """Successfully download thumbnail."""
        save_path = tmp_path / "thumbnails" / "test_video.jpg"

        mock_response = Mock()
        mock_response.content = b"fake_image_data" * 100  # Make it > 1000 bytes
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = scraper.download_thumbnail("test_video", save_path)

        assert result == save_path
        assert save_path.exists()
        assert save_path.read_bytes() == b"fake_image_data" * 100

    @patch('src.scrapers.youtube.requests.get')
    def test_download_thumbnail_fallback_quality(self, mock_get, scraper, tmp_path):
        """Fall back to lower quality thumbnail."""
        save_path = tmp_path / "thumbnails" / "test_video.jpg"

        # First (maxres) fails, second (hq) succeeds
        mock_response_fail = Mock()
        mock_response_fail.raise_for_status.side_effect = Exception("404")

        mock_response_success = Mock()
        mock_response_success.content = b"fake_image_data" * 100
        mock_response_success.raise_for_status = Mock()

        mock_get.side_effect = [mock_response_fail, mock_response_success]

        result = scraper.download_thumbnail("test_video", save_path)

        assert result == save_path
        assert save_path.exists()
        assert mock_get.call_count == 2

    @patch('src.scrapers.youtube.requests.get')
    def test_download_thumbnail_all_fail(self, mock_get, scraper, tmp_path):
        """Handle all thumbnail qualities failing."""
        save_path = tmp_path / "thumbnails" / "test_video.jpg"

        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("404")
        mock_get.return_value = mock_response

        result = scraper.download_thumbnail("test_video", save_path)

        assert result is None
        assert not save_path.exists()

    @patch('src.scrapers.youtube.requests.get')
    def test_download_thumbnail_creates_directory(self, mock_get, scraper, tmp_path):
        """Create parent directory if it doesn't exist."""
        save_path = tmp_path / "nested" / "dir" / "test_video.jpg"

        mock_response = Mock()
        mock_response.content = b"fake_image_data" * 100
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = scraper.download_thumbnail("test_video", save_path)

        assert result == save_path
        assert save_path.parent.exists()


class TestRateLimiting:
    """Test rate limiting behavior."""

    @patch('src.scrapers.youtube.time.sleep')
    @patch('src.scrapers.youtube.time.time')
    @patch('src.scrapers.youtube.requests.get')
    def test_rate_limiting_enforced(self, mock_get, mock_time, mock_sleep, scraper, mock_channel_response):
        """Rate limiting enforces delay between requests."""
        # Simulate time progression
        mock_time.side_effect = [0, 0, 0.5, 1.0]  # First call, rate limit check, after sleep, next call

        mock_response = Mock()
        mock_response.json.return_value = mock_channel_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Make two requests
        scraper.get_channel_info("UC_test_channel")
        scraper.get_channel_info("UC_test_channel")

        # Should have slept to enforce rate limit
        assert mock_sleep.called


class TestConvenienceFunctions:
    """Test module-level convenience functions."""

    @patch('src.scrapers.youtube.YouTubeScraper.get_channel_info')
    def test_get_channel_info_function(self, mock_method):
        """Test convenience function for get_channel_info."""
        from src.scrapers.youtube import get_channel_info

        mock_method.return_value = {"name": "Test"}

        result = get_channel_info("UC_test")

        assert result == {"name": "Test"}
        mock_method.assert_called_once()

    @patch('src.scrapers.youtube.YouTubeScraper.get_video_transcript')
    def test_get_transcript_function(self, mock_method):
        """Test convenience function for get_video_transcript."""
        from src.scrapers.youtube import get_video_transcript

        mock_method.return_value = "Test transcript"

        result = get_video_transcript("video_123")

        assert result == "Test transcript"
        mock_method.assert_called_once()
