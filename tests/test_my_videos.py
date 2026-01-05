"""
Tests for my_videos CRUD operations.
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path

from src.database.schema import init_db
from src.database.niches import create_niche
from src.database.my_channels import create_my_channel
from src.database.my_videos import (
    create_my_video,
    get_my_video,
    get_my_video_by_youtube_id,
    get_videos_by_channel,
    get_videos_by_niche,
    get_videos_by_status,
    update_my_video,
    delete_my_video,
    update_status,
    mark_as_published
)


@pytest.fixture
def test_db():
    """Create a temporary test database for each test."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    temp_path = Path(temp_file.name)
    temp_file.close()

    # Initialize the database schema
    init_db(temp_path)

    yield temp_path

    # Cleanup
    temp_path.unlink()


@pytest.fixture
def test_niche(test_db):
    """Create a test niche for my video tests."""
    niche_id = create_niche(
        name="Middle-earth",
        slug="middle-earth",
        niche_type="fiction",
        db_path=test_db
    )
    return niche_id


@pytest.fixture
def test_channel(test_db, test_niche):
    """Create a test channel for video tests."""
    channel_id = create_my_channel(
        niche_id=test_niche,
        name="My Lore Channel",
        db_path=test_db
    )
    return channel_id


class TestCreateMyVideo:
    """Tests for create_my_video function."""

    def test_create_my_video_minimal(self, test_db, test_niche, test_channel):
        """Test creating a video with only required fields (idea stage)."""
        video_id = create_my_video(
            channel_id=test_channel,
            niche_id=test_niche,
            title="Video Idea",
            db_path=test_db
        )

        assert isinstance(video_id, int)
        assert video_id > 0

    def test_create_my_video_full(self, test_db, test_niche, test_channel):
        """Test creating a video with all fields (published video)."""
        video_id = create_my_video(
            channel_id=test_channel,
            niche_id=test_niche,
            title="Published Video",
            description="Full description",
            youtube_id="VIDpublished123",
            status="published",
            script_path="/path/to/script.md",
            notes="Production notes",
            published_at="2024-01-01 12:00:00",
            duration_seconds=600,
            view_count=10000,
            like_count=500,
            comment_count=50,
            ctr=0.05,
            avg_view_duration=300.5,
            avg_view_percentage=50.0,
            thumbnail_url="https://example.com/thumb.jpg",
            thumbnail_path="/path/to/thumb.jpg",
            db_path=test_db
        )

        assert isinstance(video_id, int)
        assert video_id > 0

    def test_create_my_video_invalid_channel(self, test_db, test_niche):
        """Test that creating a video with invalid channel_id raises IntegrityError."""
        with pytest.raises(sqlite3.IntegrityError):
            create_my_video(
                channel_id=9999,
                niche_id=test_niche,
                title="Test Video",
                db_path=test_db
            )

    def test_create_my_video_invalid_niche(self, test_db, test_channel):
        """Test that creating a video with invalid niche_id raises IntegrityError."""
        with pytest.raises(sqlite3.IntegrityError):
            create_my_video(
                channel_id=test_channel,
                niche_id=9999,
                title="Test Video",
                db_path=test_db
            )

    def test_create_my_video_default_status(self, test_db, test_niche, test_channel):
        """Test that default status is 'idea'."""
        video_id = create_my_video(
            channel_id=test_channel,
            niche_id=test_niche,
            title="Test Video",
            db_path=test_db
        )

        video = get_my_video(video_id, db_path=test_db)
        assert video["status"] == "idea"


class TestGetMyVideo:
    """Tests for get_my_video function."""

    def test_get_my_video_success(self, test_db, test_niche, test_channel):
        """Test retrieving an existing video."""
        video_id = create_my_video(
            channel_id=test_channel,
            niche_id=test_niche,
            title="Test Video",
            description="Test description",
            status="production",
            script_path="/path/to/script.md",
            notes="Test notes",
            db_path=test_db
        )

        video = get_my_video(video_id, db_path=test_db)

        assert video is not None
        assert video["id"] == video_id
        assert video["channel_id"] == test_channel
        assert video["niche_id"] == test_niche
        assert video["title"] == "Test Video"
        assert video["description"] == "Test description"
        assert video["status"] == "production"
        assert video["script_path"] == "/path/to/script.md"
        assert video["notes"] == "Test notes"
        assert video["youtube_id"] is None
        assert video["created_at"] is not None
        assert video["updated_at"] is not None

    def test_get_my_video_not_found(self, test_db):
        """Test retrieving a non-existent video."""
        video = get_my_video(9999, db_path=test_db)
        assert video is None

    def test_get_my_video_with_null_fields(self, test_db, test_niche, test_channel):
        """Test retrieving a video with null optional fields."""
        video_id = create_my_video(
            channel_id=test_channel,
            niche_id=test_niche,
            title="Minimal Video",
            db_path=test_db
        )

        video = get_my_video(video_id, db_path=test_db)

        assert video is not None
        assert video["description"] is None
        assert video["youtube_id"] is None
        assert video["script_path"] is None
        assert video["notes"] is None
        assert video["published_at"] is None
        assert video["view_count"] is None


class TestGetMyVideoByYoutubeId:
    """Tests for get_my_video_by_youtube_id function."""

    def test_get_my_video_by_youtube_id_success(self, test_db, test_niche, test_channel):
        """Test retrieving a video by YouTube ID."""
        create_my_video(
            channel_id=test_channel,
            niche_id=test_niche,
            title="Test Video",
            youtube_id="VIDtest123",
            db_path=test_db
        )

        video = get_my_video_by_youtube_id("VIDtest123", db_path=test_db)

        assert video is not None
        assert video["youtube_id"] == "VIDtest123"
        assert video["title"] == "Test Video"

    def test_get_my_video_by_youtube_id_not_found(self, test_db):
        """Test retrieving a non-existent video by YouTube ID."""
        video = get_my_video_by_youtube_id("VIDnonexistent", db_path=test_db)
        assert video is None


class TestGetVideosByChannel:
    """Tests for get_videos_by_channel function."""

    def test_get_videos_by_channel_empty(self, test_db, test_channel):
        """Test getting videos when channel has no videos."""
        videos = get_videos_by_channel(test_channel, db_path=test_db)
        assert videos == []

    def test_get_videos_by_channel_multiple(self, test_db, test_niche, test_channel):
        """Test getting multiple videos for a channel."""
        create_my_video(
            channel_id=test_channel,
            niche_id=test_niche,
            title="Video 1",
            db_path=test_db
        )
        create_my_video(
            channel_id=test_channel,
            niche_id=test_niche,
            title="Video 2",
            db_path=test_db
        )

        videos = get_videos_by_channel(test_channel, db_path=test_db)

        assert len(videos) == 2

    def test_get_videos_by_channel_with_limit(self, test_db, test_niche, test_channel):
        """Test getting videos with a limit."""
        for i in range(5):
            create_my_video(
                channel_id=test_channel,
                niche_id=test_niche,
                title=f"Video {i}",
                db_path=test_db
            )

        videos = get_videos_by_channel(test_channel, limit=3, db_path=test_db)

        assert len(videos) == 3


class TestGetVideosByNiche:
    """Tests for get_videos_by_niche function."""

    def test_get_videos_by_niche_empty(self, test_db, test_niche):
        """Test getting videos when niche has no videos."""
        videos = get_videos_by_niche(test_niche, db_path=test_db)
        assert videos == []

    def test_get_videos_by_niche_multiple(self, test_db, test_niche, test_channel):
        """Test getting multiple videos for a niche."""
        create_my_video(
            channel_id=test_channel,
            niche_id=test_niche,
            title="Video 1",
            db_path=test_db
        )
        create_my_video(
            channel_id=test_channel,
            niche_id=test_niche,
            title="Video 2",
            db_path=test_db
        )

        videos = get_videos_by_niche(test_niche, db_path=test_db)

        assert len(videos) == 2

    def test_get_videos_by_niche_with_limit(self, test_db, test_niche, test_channel):
        """Test getting videos with a limit."""
        for i in range(5):
            create_my_video(
                channel_id=test_channel,
                niche_id=test_niche,
                title=f"Video {i}",
                db_path=test_db
            )

        videos = get_videos_by_niche(test_niche, limit=2, db_path=test_db)

        assert len(videos) == 2


class TestGetVideosByStatus:
    """Tests for get_videos_by_status function."""

    def test_get_videos_by_status_empty(self, test_db):
        """Test getting videos when no videos have the status."""
        videos = get_videos_by_status("published", db_path=test_db)
        assert videos == []

    def test_get_videos_by_status_multiple(self, test_db, test_niche, test_channel):
        """Test getting multiple videos by status."""
        create_my_video(
            channel_id=test_channel,
            niche_id=test_niche,
            title="Idea 1",
            status="idea",
            db_path=test_db
        )
        create_my_video(
            channel_id=test_channel,
            niche_id=test_niche,
            title="Production 1",
            status="production",
            db_path=test_db
        )
        create_my_video(
            channel_id=test_channel,
            niche_id=test_niche,
            title="Idea 2",
            status="idea",
            db_path=test_db
        )

        ideas = get_videos_by_status("idea", db_path=test_db)
        production = get_videos_by_status("production", db_path=test_db)

        assert len(ideas) == 2
        assert len(production) == 1

    def test_get_videos_by_status_with_limit(self, test_db, test_niche, test_channel):
        """Test getting videos by status with a limit."""
        for i in range(5):
            create_my_video(
                channel_id=test_channel,
                niche_id=test_niche,
                title=f"Idea {i}",
                status="idea",
                db_path=test_db
            )

        videos = get_videos_by_status("idea", limit=3, db_path=test_db)

        assert len(videos) == 3


class TestUpdateMyVideo:
    """Tests for update_my_video function."""

    def test_update_my_video_single_field(self, test_db, test_niche, test_channel):
        """Test updating a single field."""
        video_id = create_my_video(
            channel_id=test_channel,
            niche_id=test_niche,
            title="Original Title",
            db_path=test_db
        )

        result = update_my_video(video_id, title="Updated Title", db_path=test_db)

        assert result is True
        video = get_my_video(video_id, db_path=test_db)
        assert video["title"] == "Updated Title"

    def test_update_my_video_multiple_fields(self, test_db, test_niche, test_channel):
        """Test updating multiple fields."""
        video_id = create_my_video(
            channel_id=test_channel,
            niche_id=test_niche,
            title="Original",
            db_path=test_db
        )

        result = update_my_video(
            video_id,
            title="Updated Title",
            status="production",
            script_path="/path/to/script.md",
            notes="New notes",
            db_path=test_db
        )

        assert result is True
        video = get_my_video(video_id, db_path=test_db)
        assert video["title"] == "Updated Title"
        assert video["status"] == "production"
        assert video["script_path"] == "/path/to/script.md"
        assert video["notes"] == "New notes"

    def test_update_my_video_not_found(self, test_db):
        """Test updating a non-existent video."""
        result = update_my_video(9999, title="New Title", db_path=test_db)
        assert result is False

    def test_update_my_video_no_fields(self, test_db, test_niche, test_channel):
        """Test updating with no fields provided."""
        video_id = create_my_video(
            channel_id=test_channel,
            niche_id=test_niche,
            title="Test",
            db_path=test_db
        )
        result = update_my_video(video_id, db_path=test_db)
        assert result is False

    def test_update_my_video_invalid_field(self, test_db, test_niche, test_channel):
        """Test updating with invalid field name."""
        video_id = create_my_video(
            channel_id=test_channel,
            niche_id=test_niche,
            title="Test",
            db_path=test_db
        )

        with pytest.raises(ValueError) as exc_info:
            update_my_video(video_id, invalid_field="value", db_path=test_db)

        assert "Invalid fields" in str(exc_info.value)


class TestDeleteMyVideo:
    """Tests for delete_my_video function."""

    def test_delete_my_video_success(self, test_db, test_niche, test_channel):
        """Test successfully deleting a video."""
        video_id = create_my_video(
            channel_id=test_channel,
            niche_id=test_niche,
            title="To Delete",
            db_path=test_db
        )

        result = delete_my_video(video_id, db_path=test_db)

        assert result is True
        # Verify it's gone
        video = get_my_video(video_id, db_path=test_db)
        assert video is None

    def test_delete_my_video_not_found(self, test_db):
        """Test deleting a non-existent video."""
        result = delete_my_video(9999, db_path=test_db)
        assert result is False

    def test_delete_my_video_with_foreign_key_constraint(self, test_db, test_niche, test_channel):
        """Test that deleting a video with related records fails."""
        video_id = create_my_video(
            channel_id=test_channel,
            niche_id=test_niche,
            title="Test",
            db_path=test_db
        )

        # Create a related record (asset_usage)
        from src.database.schema import get_connection
        conn = get_connection(test_db)
        cursor = conn.cursor()
        # First create an asset
        cursor.execute(
            """
            INSERT INTO assets (niche_id, file_path)
            VALUES (?, ?)
            """,
            (test_niche, "/path/to/asset.jpg")
        )
        asset_id = cursor.lastrowid
        # Then link it to the video
        cursor.execute(
            """
            INSERT INTO asset_usage (asset_id, video_id)
            VALUES (?, ?)
            """,
            (asset_id, video_id)
        )
        conn.commit()
        conn.close()

        # Try to delete the video - should fail
        with pytest.raises(sqlite3.IntegrityError) as exc_info:
            delete_my_video(video_id, db_path=test_db)

        assert "related records" in str(exc_info.value)


class TestUpdateStatus:
    """Tests for update_status function."""

    def test_update_status_success(self, test_db, test_niche, test_channel):
        """Test updating video status."""
        video_id = create_my_video(
            channel_id=test_channel,
            niche_id=test_niche,
            title="Test Video",
            status="idea",
            db_path=test_db
        )

        result = update_status(video_id, "production", db_path=test_db)

        assert result is True
        video = get_my_video(video_id, db_path=test_db)
        assert video["status"] == "production"

    def test_update_status_not_found(self, test_db):
        """Test updating status for non-existent video."""
        result = update_status(9999, "production", db_path=test_db)
        assert result is False


class TestMarkAsPublished:
    """Tests for mark_as_published function."""

    def test_mark_as_published_success(self, test_db, test_niche, test_channel):
        """Test marking a video as published."""
        video_id = create_my_video(
            channel_id=test_channel,
            niche_id=test_niche,
            title="Test Video",
            status="production",
            db_path=test_db
        )

        result = mark_as_published(
            video_id,
            youtube_id="VIDpublished123",
            published_at="2024-01-01 12:00:00",
            db_path=test_db
        )

        assert result is True
        video = get_my_video(video_id, db_path=test_db)
        assert video["status"] == "published"
        assert video["youtube_id"] == "VIDpublished123"
        assert video["published_at"] == "2024-01-01 12:00:00"

    def test_mark_as_published_not_found(self, test_db):
        """Test marking a non-existent video as published."""
        result = mark_as_published(
            9999,
            youtube_id="VIDtest",
            published_at="2024-01-01",
            db_path=test_db
        )
        assert result is False


class TestIntegration:
    """Integration tests for combined operations."""

    def test_full_production_lifecycle(self, test_db, test_niche, test_channel):
        """Test complete video production lifecycle."""
        # Create as idea
        video_id = create_my_video(
            channel_id=test_channel,
            niche_id=test_niche,
            title="New Video Idea",
            status="idea",
            notes="Initial concept",
            db_path=test_db
        )

        # Move to researching
        update_status(video_id, "researching", db_path=test_db)
        video = get_my_video(video_id, db_path=test_db)
        assert video["status"] == "researching"

        # Move to scripting and add script
        update_my_video(
            video_id,
            status="scripting",
            script_path="/path/to/script.md",
            db_path=test_db
        )
        video = get_my_video(video_id, db_path=test_db)
        assert video["status"] == "scripting"
        assert video["script_path"] == "/path/to/script.md"

        # Move to production
        update_status(video_id, "production", db_path=test_db)
        video = get_my_video(video_id, db_path=test_db)
        assert video["status"] == "production"

        # Publish
        mark_as_published(
            video_id,
            youtube_id="VIDfinal123",
            published_at="2024-01-01 12:00:00",
            db_path=test_db
        )
        video = get_my_video(video_id, db_path=test_db)
        assert video["status"] == "published"
        assert video["youtube_id"] == "VIDfinal123"

        # Update performance metrics
        update_my_video(
            video_id,
            view_count=5000,
            like_count=250,
            comment_count=30,
            ctr=0.06,
            avg_view_duration=280.0,
            avg_view_percentage=47.0,
            db_path=test_db
        )
        video = get_my_video(video_id, db_path=test_db)
        assert video["view_count"] == 5000
        assert video["like_count"] == 250

    def test_multiple_videos_different_statuses(self, test_db, test_niche, test_channel):
        """Test managing multiple videos at different production stages."""
        # Create videos in different stages
        create_my_video(
            channel_id=test_channel,
            niche_id=test_niche,
            title="Idea 1",
            status="idea",
            db_path=test_db
        )
        create_my_video(
            channel_id=test_channel,
            niche_id=test_niche,
            title="Researching 1",
            status="researching",
            db_path=test_db
        )
        create_my_video(
            channel_id=test_channel,
            niche_id=test_channel,
            title="Production 1",
            status="production",
            db_path=test_db
        )
        create_my_video(
            channel_id=test_channel,
            niche_id=test_niche,
            title="Published 1",
            status="published",
            youtube_id="VIDpub1",
            db_path=test_db
        )

        # Check counts by status
        ideas = get_videos_by_status("idea", db_path=test_db)
        researching = get_videos_by_status("researching", db_path=test_db)
        production = get_videos_by_status("production", db_path=test_db)
        published = get_videos_by_status("published", db_path=test_db)

        assert len(ideas) == 1
        assert len(researching) == 1
        assert len(production) == 1
        assert len(published) == 1

    def test_lookup_by_youtube_id(self, test_db, test_niche, test_channel):
        """Test looking up videos by YouTube ID."""
        create_my_video(
            channel_id=test_channel,
            niche_id=test_niche,
            title="Published Video",
            youtube_id="VIDlookup123",
            status="published",
            view_count=10000,
            db_path=test_db
        )

        # Lookup by YouTube ID
        video = get_my_video_by_youtube_id("VIDlookup123", db_path=test_db)
        assert video is not None
        assert video["title"] == "Published Video"
        assert video["view_count"] == 10000
