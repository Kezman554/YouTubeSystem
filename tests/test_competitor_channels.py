"""
Tests for competitor_channels CRUD operations.
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path

from src.database.schema import init_db
from src.database.niches import create_niche
from src.database.competitor_channels import (
    create_competitor_channel,
    get_competitor_channel,
    get_competitor_channel_by_youtube_id,
    get_channels_by_niche,
    update_competitor_channel,
    delete_competitor_channel,
    mark_as_scraped
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
    """Create a test niche for competitor channel tests."""
    niche_id = create_niche(
        name="Middle-earth",
        slug="middle-earth",
        niche_type="fiction",
        db_path=test_db
    )
    return niche_id


class TestCreateCompetitorChannel:
    """Tests for create_competitor_channel function."""

    def test_create_competitor_channel_full(self, test_db, test_niche):
        """Test creating a competitor channel with all fields."""
        channel_id = create_competitor_channel(
            niche_id=test_niche,
            youtube_id="UC123456789",
            name="Nerd of the Rings",
            url="https://youtube.com/@nerdoftherings",
            subscriber_count=500000,
            video_count=250,
            style="AI voiceover",
            quality_tier="top",
            notes="Excellent lore content",
            is_active=True,
            db_path=test_db
        )

        assert isinstance(channel_id, int)
        assert channel_id > 0

    def test_create_competitor_channel_minimal(self, test_db, test_niche):
        """Test creating a competitor channel with only required fields."""
        channel_id = create_competitor_channel(
            niche_id=test_niche,
            youtube_id="UC987654321",
            name="Test Channel",
            db_path=test_db
        )

        assert isinstance(channel_id, int)
        assert channel_id > 0

    def test_create_competitor_channel_invalid_niche(self, test_db):
        """Test that creating a channel with invalid niche_id raises IntegrityError."""
        with pytest.raises(sqlite3.IntegrityError):
            create_competitor_channel(
                niche_id=9999,
                youtube_id="UC123456789",
                name="Test Channel",
                db_path=test_db
            )

    def test_create_competitor_channel_duplicate_youtube_id(self, test_db, test_niche):
        """Test that creating a channel with duplicate youtube_id raises IntegrityError."""
        create_competitor_channel(
            niche_id=test_niche,
            youtube_id="UC123456789",
            name="First Channel",
            db_path=test_db
        )

        with pytest.raises(sqlite3.IntegrityError) as exc_info:
            create_competitor_channel(
                niche_id=test_niche,
                youtube_id="UC123456789",
                name="Second Channel",
                db_path=test_db
            )

        assert "already exists" in str(exc_info.value)

    def test_create_competitor_channel_default_is_active(self, test_db, test_niche):
        """Test that default is_active is True."""
        channel_id = create_competitor_channel(
            niche_id=test_niche,
            youtube_id="UC123456789",
            name="Test Channel",
            db_path=test_db
        )

        channel = get_competitor_channel(channel_id, db_path=test_db)
        assert channel["is_active"] is True


class TestGetCompetitorChannel:
    """Tests for get_competitor_channel function."""

    def test_get_competitor_channel_success(self, test_db, test_niche):
        """Test retrieving an existing competitor channel."""
        channel_id = create_competitor_channel(
            niche_id=test_niche,
            youtube_id="UC123456789",
            name="Nerd of the Rings",
            url="https://youtube.com/@nerdoftherings",
            subscriber_count=500000,
            video_count=250,
            style="AI voiceover",
            quality_tier="top",
            notes="Excellent content",
            is_active=True,
            db_path=test_db
        )

        channel = get_competitor_channel(channel_id, db_path=test_db)

        assert channel is not None
        assert channel["id"] == channel_id
        assert channel["niche_id"] == test_niche
        assert channel["youtube_id"] == "UC123456789"
        assert channel["name"] == "Nerd of the Rings"
        assert channel["url"] == "https://youtube.com/@nerdoftherings"
        assert channel["subscriber_count"] == 500000
        assert channel["video_count"] == 250
        assert channel["style"] == "AI voiceover"
        assert channel["quality_tier"] == "top"
        assert channel["notes"] == "Excellent content"
        assert channel["is_active"] is True
        assert channel["last_scraped"] is None
        assert channel["created_at"] is not None
        assert channel["updated_at"] is not None

    def test_get_competitor_channel_not_found(self, test_db):
        """Test retrieving a non-existent competitor channel."""
        channel = get_competitor_channel(9999, db_path=test_db)
        assert channel is None

    def test_get_competitor_channel_with_null_fields(self, test_db, test_niche):
        """Test retrieving a competitor channel with null optional fields."""
        channel_id = create_competitor_channel(
            niche_id=test_niche,
            youtube_id="UC123456789",
            name="Minimal Channel",
            db_path=test_db
        )

        channel = get_competitor_channel(channel_id, db_path=test_db)

        assert channel is not None
        assert channel["url"] is None
        assert channel["subscriber_count"] is None
        assert channel["video_count"] is None
        assert channel["style"] is None
        assert channel["quality_tier"] is None
        assert channel["notes"] is None


class TestGetCompetitorChannelByYoutubeId:
    """Tests for get_competitor_channel_by_youtube_id function."""

    def test_get_competitor_channel_by_youtube_id_success(self, test_db, test_niche):
        """Test retrieving a competitor channel by YouTube ID."""
        create_competitor_channel(
            niche_id=test_niche,
            youtube_id="UC123456789",
            name="Test Channel",
            db_path=test_db
        )

        channel = get_competitor_channel_by_youtube_id("UC123456789", db_path=test_db)

        assert channel is not None
        assert channel["youtube_id"] == "UC123456789"
        assert channel["name"] == "Test Channel"

    def test_get_competitor_channel_by_youtube_id_not_found(self, test_db):
        """Test retrieving a non-existent channel by YouTube ID."""
        channel = get_competitor_channel_by_youtube_id("UC999999999", db_path=test_db)
        assert channel is None


class TestGetChannelsByNiche:
    """Tests for get_channels_by_niche function."""

    def test_get_channels_by_niche_empty(self, test_db, test_niche):
        """Test getting channels when niche has no channels."""
        channels = get_channels_by_niche(test_niche, db_path=test_db)
        assert channels == []

    def test_get_channels_by_niche_multiple(self, test_db, test_niche):
        """Test getting multiple channels for a niche."""
        create_competitor_channel(
            niche_id=test_niche,
            youtube_id="UC111",
            name="Channel A",
            subscriber_count=10000,
            db_path=test_db
        )
        create_competitor_channel(
            niche_id=test_niche,
            youtube_id="UC222",
            name="Channel B",
            subscriber_count=50000,
            db_path=test_db
        )
        create_competitor_channel(
            niche_id=test_niche,
            youtube_id="UC333",
            name="Channel C",
            subscriber_count=30000,
            db_path=test_db
        )

        channels = get_channels_by_niche(test_niche, db_path=test_db)

        assert len(channels) == 3
        # Should be ordered by subscriber_count DESC
        assert channels[0]["youtube_id"] == "UC222"  # 50000
        assert channels[1]["youtube_id"] == "UC333"  # 30000
        assert channels[2]["youtube_id"] == "UC111"  # 10000

    def test_get_channels_by_niche_active_only(self, test_db, test_niche):
        """Test filtering to only active channels."""
        create_competitor_channel(
            niche_id=test_niche,
            youtube_id="UC111",
            name="Active Channel",
            is_active=True,
            db_path=test_db
        )
        create_competitor_channel(
            niche_id=test_niche,
            youtube_id="UC222",
            name="Inactive Channel",
            is_active=False,
            db_path=test_db
        )

        # Get all channels
        all_channels = get_channels_by_niche(test_niche, db_path=test_db)
        assert len(all_channels) == 2

        # Get active only
        active_channels = get_channels_by_niche(test_niche, active_only=True, db_path=test_db)
        assert len(active_channels) == 1
        assert active_channels[0]["youtube_id"] == "UC111"

    def test_get_channels_by_niche_filters_correctly(self, test_db):
        """Test that get_channels_by_niche only returns channels for specified niche."""
        niche1 = create_niche("Niche 1", "niche-1", db_path=test_db)
        niche2 = create_niche("Niche 2", "niche-2", db_path=test_db)

        create_competitor_channel(
            niche_id=niche1,
            youtube_id="UC111",
            name="Channel N1",
            db_path=test_db
        )
        create_competitor_channel(
            niche_id=niche2,
            youtube_id="UC222",
            name="Channel N2",
            db_path=test_db
        )

        channels_n1 = get_channels_by_niche(niche1, db_path=test_db)
        channels_n2 = get_channels_by_niche(niche2, db_path=test_db)

        assert len(channels_n1) == 1
        assert channels_n1[0]["youtube_id"] == "UC111"
        assert len(channels_n2) == 1
        assert channels_n2[0]["youtube_id"] == "UC222"


class TestUpdateCompetitorChannel:
    """Tests for update_competitor_channel function."""

    def test_update_competitor_channel_single_field(self, test_db, test_niche):
        """Test updating a single field."""
        channel_id = create_competitor_channel(
            niche_id=test_niche,
            youtube_id="UC123456789",
            name="Original Name",
            db_path=test_db
        )

        result = update_competitor_channel(channel_id, name="Updated Name", db_path=test_db)

        assert result is True
        channel = get_competitor_channel(channel_id, db_path=test_db)
        assert channel["name"] == "Updated Name"

    def test_update_competitor_channel_multiple_fields(self, test_db, test_niche):
        """Test updating multiple fields."""
        channel_id = create_competitor_channel(
            niche_id=test_niche,
            youtube_id="UC123456789",
            name="Original",
            db_path=test_db
        )

        result = update_competitor_channel(
            channel_id,
            name="Updated Channel",
            subscriber_count=100000,
            quality_tier="top",
            is_active=False,
            db_path=test_db
        )

        assert result is True
        channel = get_competitor_channel(channel_id, db_path=test_db)
        assert channel["name"] == "Updated Channel"
        assert channel["subscriber_count"] == 100000
        assert channel["quality_tier"] == "top"
        assert channel["is_active"] is False

    def test_update_competitor_channel_not_found(self, test_db):
        """Test updating a non-existent competitor channel."""
        result = update_competitor_channel(9999, name="New Name", db_path=test_db)
        assert result is False

    def test_update_competitor_channel_no_fields(self, test_db, test_niche):
        """Test updating with no fields provided."""
        channel_id = create_competitor_channel(
            niche_id=test_niche,
            youtube_id="UC123456789",
            name="Test",
            db_path=test_db
        )
        result = update_competitor_channel(channel_id, db_path=test_db)
        assert result is False

    def test_update_competitor_channel_invalid_field(self, test_db, test_niche):
        """Test updating with invalid field name."""
        channel_id = create_competitor_channel(
            niche_id=test_niche,
            youtube_id="UC123456789",
            name="Test",
            db_path=test_db
        )

        with pytest.raises(ValueError) as exc_info:
            update_competitor_channel(channel_id, invalid_field="value", db_path=test_db)

        assert "Invalid fields" in str(exc_info.value)

    def test_update_competitor_channel_duplicate_youtube_id(self, test_db, test_niche):
        """Test updating youtube_id to a value that already exists."""
        create_competitor_channel(
            niche_id=test_niche,
            youtube_id="UC111",
            name="First",
            db_path=test_db
        )
        channel_id2 = create_competitor_channel(
            niche_id=test_niche,
            youtube_id="UC222",
            name="Second",
            db_path=test_db
        )

        with pytest.raises(sqlite3.IntegrityError) as exc_info:
            update_competitor_channel(channel_id2, youtube_id="UC111", db_path=test_db)

        assert "already exists" in str(exc_info.value)

    def test_update_competitor_channel_invalid_niche(self, test_db, test_niche):
        """Test updating niche_id to non-existent niche."""
        channel_id = create_competitor_channel(
            niche_id=test_niche,
            youtube_id="UC123456789",
            name="Test",
            db_path=test_db
        )

        with pytest.raises(sqlite3.IntegrityError):
            update_competitor_channel(channel_id, niche_id=9999, db_path=test_db)


class TestDeleteCompetitorChannel:
    """Tests for delete_competitor_channel function."""

    def test_delete_competitor_channel_success(self, test_db, test_niche):
        """Test successfully deleting a competitor channel."""
        channel_id = create_competitor_channel(
            niche_id=test_niche,
            youtube_id="UC123456789",
            name="To Delete",
            db_path=test_db
        )

        result = delete_competitor_channel(channel_id, db_path=test_db)

        assert result is True
        # Verify it's gone
        channel = get_competitor_channel(channel_id, db_path=test_db)
        assert channel is None

    def test_delete_competitor_channel_not_found(self, test_db):
        """Test deleting a non-existent competitor channel."""
        result = delete_competitor_channel(9999, db_path=test_db)
        assert result is False

    def test_delete_competitor_channel_with_foreign_key_constraint(self, test_db, test_niche):
        """Test that deleting a channel with related records fails."""
        channel_id = create_competitor_channel(
            niche_id=test_niche,
            youtube_id="UC123456789",
            name="Test",
            db_path=test_db
        )

        # Create a related record (competitor_video)
        from src.database.schema import get_connection
        conn = get_connection(test_db)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO competitor_videos (channel_id, niche_id, youtube_id, title)
            VALUES (?, ?, ?, ?)
            """,
            (channel_id, test_niche, "VID123", "Test Video")
        )
        conn.commit()
        conn.close()

        # Try to delete the channel - should fail
        with pytest.raises(sqlite3.IntegrityError) as exc_info:
            delete_competitor_channel(channel_id, db_path=test_db)

        assert "related records" in str(exc_info.value)


class TestMarkAsScraped:
    """Tests for mark_as_scraped function."""

    def test_mark_as_scraped_success(self, test_db, test_niche):
        """Test marking a channel as scraped."""
        channel_id = create_competitor_channel(
            niche_id=test_niche,
            youtube_id="UC123456789",
            name="Test Channel",
            db_path=test_db
        )

        # Initially not scraped
        channel = get_competitor_channel(channel_id, db_path=test_db)
        assert channel["last_scraped"] is None

        # Mark as scraped
        result = mark_as_scraped(channel_id, db_path=test_db)
        assert result is True

        # Verify it's marked
        channel = get_competitor_channel(channel_id, db_path=test_db)
        assert channel["last_scraped"] is not None

    def test_mark_as_scraped_not_found(self, test_db):
        """Test marking a non-existent channel as scraped."""
        result = mark_as_scraped(9999, db_path=test_db)
        assert result is False

    def test_mark_as_scraped_idempotent(self, test_db, test_niche):
        """Test that marking as scraped multiple times is safe."""
        channel_id = create_competitor_channel(
            niche_id=test_niche,
            youtube_id="UC123456789",
            name="Test Channel",
            db_path=test_db
        )

        # Mark as scraped twice
        result1 = mark_as_scraped(channel_id, db_path=test_db)
        result2 = mark_as_scraped(channel_id, db_path=test_db)

        assert result1 is True
        assert result2 is True

        # Should still be marked as scraped
        channel = get_competitor_channel(channel_id, db_path=test_db)
        assert channel["last_scraped"] is not None


class TestIntegration:
    """Integration tests for combined operations."""

    def test_full_crud_lifecycle(self, test_db, test_niche):
        """Test complete CRUD lifecycle."""
        # Create
        channel_id = create_competitor_channel(
            niche_id=test_niche,
            youtube_id="UC123456789",
            name="Test Channel",
            subscriber_count=50000,
            is_active=True,
            db_path=test_db
        )
        assert channel_id > 0

        # Read
        channel = get_competitor_channel(channel_id, db_path=test_db)
        assert channel["name"] == "Test Channel"
        assert channel["last_scraped"] is None

        # Update
        success = update_competitor_channel(
            channel_id,
            name="Updated Channel",
            subscriber_count=75000,
            db_path=test_db
        )
        assert success is True

        # Verify update
        channel = get_competitor_channel(channel_id, db_path=test_db)
        assert channel["name"] == "Updated Channel"
        assert channel["subscriber_count"] == 75000

        # Mark as scraped
        success = mark_as_scraped(channel_id, db_path=test_db)
        assert success is True

        # Verify scraped
        channel = get_competitor_channel(channel_id, db_path=test_db)
        assert channel["last_scraped"] is not None

        # Delete
        success = delete_competitor_channel(channel_id, db_path=test_db)
        assert success is True

        # Verify deletion
        channel = get_competitor_channel(channel_id, db_path=test_db)
        assert channel is None

    def test_multiple_niches_with_channels(self, test_db):
        """Test managing channels across multiple niches."""
        # Create two niches
        niche1 = create_niche("Niche 1", "niche-1", db_path=test_db)
        niche2 = create_niche("Niche 2", "niche-2", db_path=test_db)

        # Add channels to each
        create_competitor_channel(
            niche_id=niche1,
            youtube_id="UC111",
            name="N1 Channel 1",
            db_path=test_db
        )
        create_competitor_channel(
            niche_id=niche1,
            youtube_id="UC112",
            name="N1 Channel 2",
            db_path=test_db
        )
        create_competitor_channel(
            niche_id=niche2,
            youtube_id="UC221",
            name="N2 Channel 1",
            db_path=test_db
        )

        # Verify filtering works
        n1_channels = get_channels_by_niche(niche1, db_path=test_db)
        n2_channels = get_channels_by_niche(niche2, db_path=test_db)

        assert len(n1_channels) == 2
        assert len(n2_channels) == 1
        assert all(c["niche_id"] == niche1 for c in n1_channels)
        assert all(c["niche_id"] == niche2 for c in n2_channels)

    def test_lookup_by_youtube_id(self, test_db, test_niche):
        """Test looking up channels by YouTube ID."""
        create_competitor_channel(
            niche_id=test_niche,
            youtube_id="UC123456789",
            name="Test Channel",
            subscriber_count=100000,
            db_path=test_db
        )

        # Lookup by YouTube ID
        channel = get_competitor_channel_by_youtube_id("UC123456789", db_path=test_db)
        assert channel is not None
        assert channel["name"] == "Test Channel"
        assert channel["subscriber_count"] == 100000
