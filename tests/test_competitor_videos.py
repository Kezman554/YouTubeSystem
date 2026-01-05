"""
Tests for competitor_videos CRUD operations.
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path

from src.database.schema import init_db
from src.database.niches import create_niche
from src.database.competitor_channels import create_competitor_channel
from src.database.competitor_videos import (
    create_competitor_video,
    get_competitor_video,
    get_competitor_video_by_youtube_id,
    get_videos_by_channel,
    get_videos_by_niche,
    update_competitor_video,
    delete_competitor_video,
    mark_transcript_cleaned
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
    """Create a test niche for competitor video tests."""
    niche_id = create_niche(
        name="Middle-earth",
        slug="middle-earth",
        niche_type="fiction",
        db_path=test_db
    )
    return niche_id


@pytest.fixture
def test_channel(test_db, test_niche):
    """Create a test competitor channel for video tests."""
    channel_id = create_competitor_channel(
        niche_id=test_niche,
        youtube_id="UC123456789",
        name="Test Channel",
        db_path=test_db
    )
    return channel_id


class TestCreateCompetitorVideo:
    """Tests for create_competitor_video function."""

    def test_create_competitor_video_full(self, test_db, test_niche, test_channel):
        """Test creating a competitor video with all fields."""
        video_id = create_competitor_video(
            channel_id=test_channel,
            niche_id=test_niche,
            youtube_id="VID123",
            title="Test Video",
            description="Video description",
            published_at="2024-01-01 12:00:00",
            duration_seconds=600,
            view_count=10000,
            like_count=500,
            comment_count=50,
            thumbnail_url="https://example.com/thumb.jpg",
            thumbnail_path="/path/to/thumb.jpg",
            views_per_sub=0.02,
            topic_tags='["topic1", "topic2"]',
            has_transcript=True,
            transcript_cleaned=False,
            db_path=test_db
        )

        assert isinstance(video_id, int)
        assert video_id > 0

    def test_create_competitor_video_minimal(self, test_db, test_niche, test_channel):
        """Test creating a competitor video with only required fields."""
        video_id = create_competitor_video(
            channel_id=test_channel,
            niche_id=test_niche,
            youtube_id="VID456",
            title="Minimal Video",
            db_path=test_db
        )

        assert isinstance(video_id, int)
        assert video_id > 0

    def test_create_competitor_video_invalid_channel(self, test_db, test_niche):
        """Test that creating a video with invalid channel_id raises IntegrityError."""
        with pytest.raises(sqlite3.IntegrityError):
            create_competitor_video(
                channel_id=9999,
                niche_id=test_niche,
                youtube_id="VID123",
                title="Test Video",
                db_path=test_db
            )

    def test_create_competitor_video_invalid_niche(self, test_db, test_channel):
        """Test that creating a video with invalid niche_id raises IntegrityError."""
        with pytest.raises(sqlite3.IntegrityError):
            create_competitor_video(
                channel_id=test_channel,
                niche_id=9999,
                youtube_id="VID123",
                title="Test Video",
                db_path=test_db
            )

    def test_create_competitor_video_duplicate_youtube_id(self, test_db, test_niche, test_channel):
        """Test that creating a video with duplicate youtube_id raises IntegrityError."""
        create_competitor_video(
            channel_id=test_channel,
            niche_id=test_niche,
            youtube_id="VID123",
            title="First Video",
            db_path=test_db
        )

        with pytest.raises(sqlite3.IntegrityError) as exc_info:
            create_competitor_video(
                channel_id=test_channel,
                niche_id=test_niche,
                youtube_id="VID123",
                title="Second Video",
                db_path=test_db
            )

        assert "already exists" in str(exc_info.value)

    def test_create_competitor_video_default_booleans(self, test_db, test_niche, test_channel):
        """Test that default values for booleans are False."""
        video_id = create_competitor_video(
            channel_id=test_channel,
            niche_id=test_niche,
            youtube_id="VID123",
            title="Test Video",
            db_path=test_db
        )

        video = get_competitor_video(video_id, db_path=test_db)
        assert video["has_transcript"] is False
        assert video["transcript_cleaned"] is False


class TestGetCompetitorVideo:
    """Tests for get_competitor_video function."""

    def test_get_competitor_video_success(self, test_db, test_niche, test_channel):
        """Test retrieving an existing competitor video."""
        video_id = create_competitor_video(
            channel_id=test_channel,
            niche_id=test_niche,
            youtube_id="VID123",
            title="Test Video",
            description="Test description",
            published_at="2024-01-01 12:00:00",
            duration_seconds=600,
            view_count=10000,
            like_count=500,
            comment_count=50,
            thumbnail_url="https://example.com/thumb.jpg",
            views_per_sub=0.02,
            topic_tags='["topic1"]',
            has_transcript=True,
            transcript_cleaned=False,
            db_path=test_db
        )

        video = get_competitor_video(video_id, db_path=test_db)

        assert video is not None
        assert video["id"] == video_id
        assert video["channel_id"] == test_channel
        assert video["niche_id"] == test_niche
        assert video["youtube_id"] == "VID123"
        assert video["title"] == "Test Video"
        assert video["description"] == "Test description"
        assert video["duration_seconds"] == 600
        assert video["view_count"] == 10000
        assert video["like_count"] == 500
        assert video["comment_count"] == 50
        assert video["views_per_sub"] == 0.02
        assert video["topic_tags"] == '["topic1"]'
        assert video["has_transcript"] is True
        assert video["transcript_cleaned"] is False
        assert video["first_scraped"] is not None
        assert video["created_at"] is not None

    def test_get_competitor_video_not_found(self, test_db):
        """Test retrieving a non-existent competitor video."""
        video = get_competitor_video(9999, db_path=test_db)
        assert video is None

    def test_get_competitor_video_with_null_fields(self, test_db, test_niche, test_channel):
        """Test retrieving a competitor video with null optional fields."""
        video_id = create_competitor_video(
            channel_id=test_channel,
            niche_id=test_niche,
            youtube_id="VID123",
            title="Minimal Video",
            db_path=test_db
        )

        video = get_competitor_video(video_id, db_path=test_db)

        assert video is not None
        assert video["description"] is None
        assert video["published_at"] is None
        assert video["duration_seconds"] is None
        assert video["view_count"] is None
        assert video["like_count"] is None
        assert video["comment_count"] is None
        assert video["views_per_sub"] is None
        assert video["topic_tags"] is None


class TestGetCompetitorVideoByYoutubeId:
    """Tests for get_competitor_video_by_youtube_id function."""

    def test_get_competitor_video_by_youtube_id_success(self, test_db, test_niche, test_channel):
        """Test retrieving a competitor video by YouTube ID."""
        create_competitor_video(
            channel_id=test_channel,
            niche_id=test_niche,
            youtube_id="VID123",
            title="Test Video",
            db_path=test_db
        )

        video = get_competitor_video_by_youtube_id("VID123", db_path=test_db)

        assert video is not None
        assert video["youtube_id"] == "VID123"
        assert video["title"] == "Test Video"

    def test_get_competitor_video_by_youtube_id_not_found(self, test_db):
        """Test retrieving a non-existent video by YouTube ID."""
        video = get_competitor_video_by_youtube_id("VID999", db_path=test_db)
        assert video is None


class TestGetVideosByChannel:
    """Tests for get_videos_by_channel function."""

    def test_get_videos_by_channel_empty(self, test_db, test_channel):
        """Test getting videos when channel has no videos."""
        videos = get_videos_by_channel(test_channel, db_path=test_db)
        assert videos == []

    def test_get_videos_by_channel_multiple(self, test_db, test_niche, test_channel):
        """Test getting multiple videos for a channel."""
        create_competitor_video(
            channel_id=test_channel,
            niche_id=test_niche,
            youtube_id="VID1",
            title="Video 1",
            published_at="2024-01-01",
            db_path=test_db
        )
        create_competitor_video(
            channel_id=test_channel,
            niche_id=test_niche,
            youtube_id="VID2",
            title="Video 2",
            published_at="2024-01-03",
            db_path=test_db
        )
        create_competitor_video(
            channel_id=test_channel,
            niche_id=test_niche,
            youtube_id="VID3",
            title="Video 3",
            published_at="2024-01-02",
            db_path=test_db
        )

        videos = get_videos_by_channel(test_channel, db_path=test_db)

        assert len(videos) == 3
        # Should be ordered by published_at DESC (newest first)
        assert videos[0]["youtube_id"] == "VID2"  # 2024-01-03
        assert videos[1]["youtube_id"] == "VID3"  # 2024-01-02
        assert videos[2]["youtube_id"] == "VID1"  # 2024-01-01

    def test_get_videos_by_channel_with_limit(self, test_db, test_niche, test_channel):
        """Test getting videos with a limit."""
        for i in range(5):
            create_competitor_video(
                channel_id=test_channel,
                niche_id=test_niche,
                youtube_id=f"VID{i}",
                title=f"Video {i}",
                db_path=test_db
            )

        videos = get_videos_by_channel(test_channel, limit=3, db_path=test_db)

        assert len(videos) == 3

    def test_get_videos_by_channel_filters_correctly(self, test_db, test_niche):
        """Test that get_videos_by_channel only returns videos for specified channel."""
        channel1 = create_competitor_channel(
            niche_id=test_niche,
            youtube_id="CH1",
            name="Channel 1",
            db_path=test_db
        )
        channel2 = create_competitor_channel(
            niche_id=test_niche,
            youtube_id="CH2",
            name="Channel 2",
            db_path=test_db
        )

        create_competitor_video(
            channel_id=channel1,
            niche_id=test_niche,
            youtube_id="VID1",
            title="Video C1",
            db_path=test_db
        )
        create_competitor_video(
            channel_id=channel2,
            niche_id=test_niche,
            youtube_id="VID2",
            title="Video C2",
            db_path=test_db
        )

        videos_c1 = get_videos_by_channel(channel1, db_path=test_db)
        videos_c2 = get_videos_by_channel(channel2, db_path=test_db)

        assert len(videos_c1) == 1
        assert videos_c1[0]["youtube_id"] == "VID1"
        assert len(videos_c2) == 1
        assert videos_c2[0]["youtube_id"] == "VID2"


class TestGetVideosByNiche:
    """Tests for get_videos_by_niche function."""

    def test_get_videos_by_niche_empty(self, test_db, test_niche):
        """Test getting videos when niche has no videos."""
        videos = get_videos_by_niche(test_niche, db_path=test_db)
        assert videos == []

    def test_get_videos_by_niche_multiple(self, test_db, test_niche, test_channel):
        """Test getting multiple videos for a niche."""
        create_competitor_video(
            channel_id=test_channel,
            niche_id=test_niche,
            youtube_id="VID1",
            title="Video 1",
            db_path=test_db
        )
        create_competitor_video(
            channel_id=test_channel,
            niche_id=test_niche,
            youtube_id="VID2",
            title="Video 2",
            db_path=test_db
        )

        videos = get_videos_by_niche(test_niche, db_path=test_db)

        assert len(videos) == 2

    def test_get_videos_by_niche_with_limit(self, test_db, test_niche, test_channel):
        """Test getting videos with a limit."""
        for i in range(5):
            create_competitor_video(
                channel_id=test_channel,
                niche_id=test_niche,
                youtube_id=f"VID{i}",
                title=f"Video {i}",
                db_path=test_db
            )

        videos = get_videos_by_niche(test_niche, limit=2, db_path=test_db)

        assert len(videos) == 2

    def test_get_videos_by_niche_filters_correctly(self, test_db):
        """Test that get_videos_by_niche only returns videos for specified niche."""
        niche1 = create_niche("Niche 1", "niche-1", db_path=test_db)
        niche2 = create_niche("Niche 2", "niche-2", db_path=test_db)

        channel1 = create_competitor_channel(
            niche_id=niche1,
            youtube_id="CH1",
            name="Channel 1",
            db_path=test_db
        )
        channel2 = create_competitor_channel(
            niche_id=niche2,
            youtube_id="CH2",
            name="Channel 2",
            db_path=test_db
        )

        create_competitor_video(
            channel_id=channel1,
            niche_id=niche1,
            youtube_id="VID1",
            title="Video N1",
            db_path=test_db
        )
        create_competitor_video(
            channel_id=channel2,
            niche_id=niche2,
            youtube_id="VID2",
            title="Video N2",
            db_path=test_db
        )

        videos_n1 = get_videos_by_niche(niche1, db_path=test_db)
        videos_n2 = get_videos_by_niche(niche2, db_path=test_db)

        assert len(videos_n1) == 1
        assert videos_n1[0]["youtube_id"] == "VID1"
        assert len(videos_n2) == 1
        assert videos_n2[0]["youtube_id"] == "VID2"


class TestUpdateCompetitorVideo:
    """Tests for update_competitor_video function."""

    def test_update_competitor_video_single_field(self, test_db, test_niche, test_channel):
        """Test updating a single field."""
        video_id = create_competitor_video(
            channel_id=test_channel,
            niche_id=test_niche,
            youtube_id="VID123",
            title="Original Title",
            db_path=test_db
        )

        result = update_competitor_video(video_id, title="Updated Title", db_path=test_db)

        assert result is True
        video = get_competitor_video(video_id, db_path=test_db)
        assert video["title"] == "Updated Title"

    def test_update_competitor_video_multiple_fields(self, test_db, test_niche, test_channel):
        """Test updating multiple fields."""
        video_id = create_competitor_video(
            channel_id=test_channel,
            niche_id=test_niche,
            youtube_id="VID123",
            title="Original",
            db_path=test_db
        )

        result = update_competitor_video(
            video_id,
            title="Updated Title",
            view_count=50000,
            like_count=2000,
            has_transcript=True,
            db_path=test_db
        )

        assert result is True
        video = get_competitor_video(video_id, db_path=test_db)
        assert video["title"] == "Updated Title"
        assert video["view_count"] == 50000
        assert video["like_count"] == 2000
        assert video["has_transcript"] is True

    def test_update_competitor_video_not_found(self, test_db):
        """Test updating a non-existent competitor video."""
        result = update_competitor_video(9999, title="New Title", db_path=test_db)
        assert result is False

    def test_update_competitor_video_no_fields(self, test_db, test_niche, test_channel):
        """Test updating with no fields provided."""
        video_id = create_competitor_video(
            channel_id=test_channel,
            niche_id=test_niche,
            youtube_id="VID123",
            title="Test",
            db_path=test_db
        )
        result = update_competitor_video(video_id, db_path=test_db)
        assert result is False

    def test_update_competitor_video_invalid_field(self, test_db, test_niche, test_channel):
        """Test updating with invalid field name."""
        video_id = create_competitor_video(
            channel_id=test_channel,
            niche_id=test_niche,
            youtube_id="VID123",
            title="Test",
            db_path=test_db
        )

        with pytest.raises(ValueError) as exc_info:
            update_competitor_video(video_id, invalid_field="value", db_path=test_db)

        assert "Invalid fields" in str(exc_info.value)

    def test_update_competitor_video_duplicate_youtube_id(self, test_db, test_niche, test_channel):
        """Test updating youtube_id to a value that already exists."""
        create_competitor_video(
            channel_id=test_channel,
            niche_id=test_niche,
            youtube_id="VID1",
            title="First",
            db_path=test_db
        )
        video_id2 = create_competitor_video(
            channel_id=test_channel,
            niche_id=test_niche,
            youtube_id="VID2",
            title="Second",
            db_path=test_db
        )

        with pytest.raises(sqlite3.IntegrityError) as exc_info:
            update_competitor_video(video_id2, youtube_id="VID1", db_path=test_db)

        assert "already exists" in str(exc_info.value)


class TestDeleteCompetitorVideo:
    """Tests for delete_competitor_video function."""

    def test_delete_competitor_video_success(self, test_db, test_niche, test_channel):
        """Test successfully deleting a competitor video."""
        video_id = create_competitor_video(
            channel_id=test_channel,
            niche_id=test_niche,
            youtube_id="VID123",
            title="To Delete",
            db_path=test_db
        )

        result = delete_competitor_video(video_id, db_path=test_db)

        assert result is True
        # Verify it's gone
        video = get_competitor_video(video_id, db_path=test_db)
        assert video is None

    def test_delete_competitor_video_not_found(self, test_db):
        """Test deleting a non-existent competitor video."""
        result = delete_competitor_video(9999, db_path=test_db)
        assert result is False

    def test_delete_competitor_video_with_foreign_key_constraint(self, test_db, test_niche, test_channel):
        """Test that deleting a video with related records fails."""
        video_id = create_competitor_video(
            channel_id=test_channel,
            niche_id=test_niche,
            youtube_id="VID123",
            title="Test",
            db_path=test_db
        )

        # Create a related record (performance_snapshot)
        from src.database.schema import get_connection
        conn = get_connection(test_db)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO performance_snapshots (video_id, view_count)
            VALUES (?, ?)
            """,
            (video_id, 1000)
        )
        conn.commit()
        conn.close()

        # Try to delete the video - should fail
        with pytest.raises(sqlite3.IntegrityError) as exc_info:
            delete_competitor_video(video_id, db_path=test_db)

        assert "related records" in str(exc_info.value)


class TestMarkTranscriptCleaned:
    """Tests for mark_transcript_cleaned function."""

    def test_mark_transcript_cleaned_success(self, test_db, test_niche, test_channel):
        """Test marking a video's transcript as cleaned."""
        video_id = create_competitor_video(
            channel_id=test_channel,
            niche_id=test_niche,
            youtube_id="VID123",
            title="Test Video",
            has_transcript=True,
            db_path=test_db
        )

        # Initially not cleaned
        video = get_competitor_video(video_id, db_path=test_db)
        assert video["transcript_cleaned"] is False

        # Mark as cleaned
        result = mark_transcript_cleaned(video_id, db_path=test_db)
        assert result is True

        # Verify it's marked
        video = get_competitor_video(video_id, db_path=test_db)
        assert video["transcript_cleaned"] is True

    def test_mark_transcript_cleaned_not_found(self, test_db):
        """Test marking a non-existent video's transcript as cleaned."""
        result = mark_transcript_cleaned(9999, db_path=test_db)
        assert result is False

    def test_mark_transcript_cleaned_idempotent(self, test_db, test_niche, test_channel):
        """Test that marking as cleaned multiple times is safe."""
        video_id = create_competitor_video(
            channel_id=test_channel,
            niche_id=test_niche,
            youtube_id="VID123",
            title="Test Video",
            db_path=test_db
        )

        # Mark as cleaned twice
        result1 = mark_transcript_cleaned(video_id, db_path=test_db)
        result2 = mark_transcript_cleaned(video_id, db_path=test_db)

        assert result1 is True
        assert result2 is True

        # Should still be marked as cleaned
        video = get_competitor_video(video_id, db_path=test_db)
        assert video["transcript_cleaned"] is True


class TestIntegration:
    """Integration tests for combined operations."""

    def test_full_crud_lifecycle(self, test_db, test_niche, test_channel):
        """Test complete CRUD lifecycle."""
        # Create
        video_id = create_competitor_video(
            channel_id=test_channel,
            niche_id=test_niche,
            youtube_id="VID123",
            title="Test Video",
            view_count=10000,
            has_transcript=False,
            db_path=test_db
        )
        assert video_id > 0

        # Read
        video = get_competitor_video(video_id, db_path=test_db)
        assert video["title"] == "Test Video"
        assert video["transcript_cleaned"] is False

        # Update
        success = update_competitor_video(
            video_id,
            title="Updated Video",
            view_count=20000,
            has_transcript=True,
            db_path=test_db
        )
        assert success is True

        # Verify update
        video = get_competitor_video(video_id, db_path=test_db)
        assert video["title"] == "Updated Video"
        assert video["view_count"] == 20000
        assert video["has_transcript"] is True

        # Mark transcript cleaned
        success = mark_transcript_cleaned(video_id, db_path=test_db)
        assert success is True

        # Verify transcript cleaned
        video = get_competitor_video(video_id, db_path=test_db)
        assert video["transcript_cleaned"] is True

        # Delete
        success = delete_competitor_video(video_id, db_path=test_db)
        assert success is True

        # Verify deletion
        video = get_competitor_video(video_id, db_path=test_db)
        assert video is None

    def test_lookup_by_youtube_id(self, test_db, test_niche, test_channel):
        """Test looking up videos by YouTube ID."""
        create_competitor_video(
            channel_id=test_channel,
            niche_id=test_niche,
            youtube_id="VID123",
            title="Test Video",
            view_count=50000,
            db_path=test_db
        )

        # Lookup by YouTube ID
        video = get_competitor_video_by_youtube_id("VID123", db_path=test_db)
        assert video is not None
        assert video["title"] == "Test Video"
        assert video["view_count"] == 50000

    def test_multiple_channels_and_niches(self, test_db):
        """Test managing videos across multiple channels and niches."""
        niche1 = create_niche("Niche 1", "niche-1", db_path=test_db)
        niche2 = create_niche("Niche 2", "niche-2", db_path=test_db)

        channel1 = create_competitor_channel(
            niche_id=niche1,
            youtube_id="CH1",
            name="Channel 1",
            db_path=test_db
        )
        channel2 = create_competitor_channel(
            niche_id=niche2,
            youtube_id="CH2",
            name="Channel 2",
            db_path=test_db
        )

        # Create videos in different channels
        create_competitor_video(
            channel_id=channel1,
            niche_id=niche1,
            youtube_id="VID1",
            title="C1 Video",
            db_path=test_db
        )
        create_competitor_video(
            channel_id=channel2,
            niche_id=niche2,
            youtube_id="VID2",
            title="C2 Video",
            db_path=test_db
        )

        # Verify channel filtering
        c1_videos = get_videos_by_channel(channel1, db_path=test_db)
        c2_videos = get_videos_by_channel(channel2, db_path=test_db)

        assert len(c1_videos) == 1
        assert c1_videos[0]["youtube_id"] == "VID1"
        assert len(c2_videos) == 1
        assert c2_videos[0]["youtube_id"] == "VID2"

        # Verify niche filtering
        n1_videos = get_videos_by_niche(niche1, db_path=test_db)
        n2_videos = get_videos_by_niche(niche2, db_path=test_db)

        assert len(n1_videos) == 1
        assert n1_videos[0]["youtube_id"] == "VID1"
        assert len(n2_videos) == 1
        assert n2_videos[0]["youtube_id"] == "VID2"
