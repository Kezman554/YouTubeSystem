"""
Tests for my_channels CRUD operations.
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path

from src.database.schema import init_db
from src.database.niches import create_niche
from src.database.my_channels import (
    create_my_channel,
    get_my_channel,
    get_my_channel_by_youtube_id,
    get_channels_by_niche,
    get_all_my_channels,
    update_my_channel,
    delete_my_channel,
    update_subscriber_count
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
    """Create a test niche for my channel tests."""
    niche_id = create_niche(
        name="Middle-earth",
        slug="middle-earth",
        niche_type="fiction",
        db_path=test_db
    )
    return niche_id


class TestCreateMyChannel:
    """Tests for create_my_channel function."""

    def test_create_my_channel_full(self, test_db, test_niche):
        """Test creating a channel with all fields."""
        channel_id = create_my_channel(
            niche_id=test_niche,
            name="My Lore Channel",
            youtube_id="UCmyChannel123",
            url="https://youtube.com/@mylorechannel",
            subscriber_count=100,
            db_path=test_db
        )

        assert isinstance(channel_id, int)
        assert channel_id > 0

    def test_create_my_channel_minimal(self, test_db, test_niche):
        """Test creating a channel with only required fields."""
        channel_id = create_my_channel(
            niche_id=test_niche,
            name="Minimal Channel",
            db_path=test_db
        )

        assert isinstance(channel_id, int)
        assert channel_id > 0

    def test_create_my_channel_without_youtube_id(self, test_db, test_niche):
        """Test creating a channel without YouTube ID (not yet created on YouTube)."""
        channel_id = create_my_channel(
            niche_id=test_niche,
            name="Planned Channel",
            db_path=test_db
        )

        channel = get_my_channel(channel_id, db_path=test_db)
        assert channel["youtube_id"] is None

    def test_create_my_channel_invalid_niche(self, test_db):
        """Test that creating a channel with invalid niche_id raises IntegrityError."""
        with pytest.raises(sqlite3.IntegrityError):
            create_my_channel(
                niche_id=9999,
                name="Test Channel",
                db_path=test_db
            )

    def test_create_my_channel_duplicate_youtube_id(self, test_db, test_niche):
        """Test that creating a channel with duplicate youtube_id raises IntegrityError."""
        create_my_channel(
            niche_id=test_niche,
            name="First Channel",
            youtube_id="UCduplicate123",
            db_path=test_db
        )

        with pytest.raises(sqlite3.IntegrityError) as exc_info:
            create_my_channel(
                niche_id=test_niche,
                name="Second Channel",
                youtube_id="UCduplicate123",
                db_path=test_db
            )

        assert "already exists" in str(exc_info.value)

    def test_create_my_channel_default_subscriber_count(self, test_db, test_niche):
        """Test that default subscriber_count is 0."""
        channel_id = create_my_channel(
            niche_id=test_niche,
            name="Test Channel",
            db_path=test_db
        )

        channel = get_my_channel(channel_id, db_path=test_db)
        assert channel["subscriber_count"] == 0


class TestGetMyChannel:
    """Tests for get_my_channel function."""

    def test_get_my_channel_success(self, test_db, test_niche):
        """Test retrieving an existing channel."""
        channel_id = create_my_channel(
            niche_id=test_niche,
            name="Test Channel",
            youtube_id="UCtest123",
            url="https://youtube.com/@testchannel",
            subscriber_count=500,
            db_path=test_db
        )

        channel = get_my_channel(channel_id, db_path=test_db)

        assert channel is not None
        assert channel["id"] == channel_id
        assert channel["niche_id"] == test_niche
        assert channel["youtube_id"] == "UCtest123"
        assert channel["name"] == "Test Channel"
        assert channel["url"] == "https://youtube.com/@testchannel"
        assert channel["subscriber_count"] == 500
        assert channel["created_at"] is not None
        assert channel["updated_at"] is not None

    def test_get_my_channel_not_found(self, test_db):
        """Test retrieving a non-existent channel."""
        channel = get_my_channel(9999, db_path=test_db)
        assert channel is None

    def test_get_my_channel_with_null_fields(self, test_db, test_niche):
        """Test retrieving a channel with null optional fields."""
        channel_id = create_my_channel(
            niche_id=test_niche,
            name="Minimal Channel",
            db_path=test_db
        )

        channel = get_my_channel(channel_id, db_path=test_db)

        assert channel is not None
        assert channel["youtube_id"] is None
        assert channel["url"] is None
        assert channel["subscriber_count"] == 0


class TestGetMyChannelByYoutubeId:
    """Tests for get_my_channel_by_youtube_id function."""

    def test_get_my_channel_by_youtube_id_success(self, test_db, test_niche):
        """Test retrieving a channel by YouTube ID."""
        create_my_channel(
            niche_id=test_niche,
            name="Test Channel",
            youtube_id="UCtest123",
            db_path=test_db
        )

        channel = get_my_channel_by_youtube_id("UCtest123", db_path=test_db)

        assert channel is not None
        assert channel["youtube_id"] == "UCtest123"
        assert channel["name"] == "Test Channel"

    def test_get_my_channel_by_youtube_id_not_found(self, test_db):
        """Test retrieving a non-existent channel by YouTube ID."""
        channel = get_my_channel_by_youtube_id("UCnonexistent", db_path=test_db)
        assert channel is None


class TestGetChannelsByNiche:
    """Tests for get_channels_by_niche function."""

    def test_get_channels_by_niche_empty(self, test_db, test_niche):
        """Test getting channels when niche has no channels."""
        channels = get_channels_by_niche(test_niche, db_path=test_db)
        assert channels == []

    def test_get_channels_by_niche_multiple(self, test_db, test_niche):
        """Test getting multiple channels for a niche."""
        id1 = create_my_channel(
            niche_id=test_niche,
            name="Channel 1",
            db_path=test_db
        )
        id2 = create_my_channel(
            niche_id=test_niche,
            name="Channel 2",
            db_path=test_db
        )
        id3 = create_my_channel(
            niche_id=test_niche,
            name="Channel 3",
            db_path=test_db
        )

        channels = get_channels_by_niche(test_niche, db_path=test_db)

        assert len(channels) == 3
        # Verify all channel IDs are present
        channel_ids = {c["id"] for c in channels}
        assert channel_ids == {id1, id2, id3}

    def test_get_channels_by_niche_filters_correctly(self, test_db):
        """Test that get_channels_by_niche only returns channels for specified niche."""
        niche1 = create_niche("Niche 1", "niche-1", db_path=test_db)
        niche2 = create_niche("Niche 2", "niche-2", db_path=test_db)

        create_my_channel(
            niche_id=niche1,
            name="Channel N1",
            db_path=test_db
        )
        create_my_channel(
            niche_id=niche2,
            name="Channel N2",
            db_path=test_db
        )

        channels_n1 = get_channels_by_niche(niche1, db_path=test_db)
        channels_n2 = get_channels_by_niche(niche2, db_path=test_db)

        assert len(channels_n1) == 1
        assert channels_n1[0]["name"] == "Channel N1"
        assert len(channels_n2) == 1
        assert channels_n2[0]["name"] == "Channel N2"


class TestGetAllMyChannels:
    """Tests for get_all_my_channels function."""

    def test_get_all_my_channels_empty(self, test_db):
        """Test getting all channels when database is empty."""
        channels = get_all_my_channels(db_path=test_db)
        assert channels == []

    def test_get_all_my_channels_multiple(self, test_db, test_niche):
        """Test getting all channels across niches."""
        niche2 = create_niche("Niche 2", "niche-2", db_path=test_db)

        create_my_channel(niche_id=test_niche, name="Channel 1", db_path=test_db)
        create_my_channel(niche_id=niche2, name="Channel 2", db_path=test_db)
        create_my_channel(niche_id=test_niche, name="Channel 3", db_path=test_db)

        channels = get_all_my_channels(db_path=test_db)

        assert len(channels) == 3
        # All channels from all niches
        channel_names = {c["name"] for c in channels}
        assert channel_names == {"Channel 1", "Channel 2", "Channel 3"}


class TestUpdateMyChannel:
    """Tests for update_my_channel function."""

    def test_update_my_channel_single_field(self, test_db, test_niche):
        """Test updating a single field."""
        channel_id = create_my_channel(
            niche_id=test_niche,
            name="Original Name",
            db_path=test_db
        )

        result = update_my_channel(channel_id, name="Updated Name", db_path=test_db)

        assert result is True
        channel = get_my_channel(channel_id, db_path=test_db)
        assert channel["name"] == "Updated Name"

    def test_update_my_channel_multiple_fields(self, test_db, test_niche):
        """Test updating multiple fields."""
        channel_id = create_my_channel(
            niche_id=test_niche,
            name="Original",
            db_path=test_db
        )

        result = update_my_channel(
            channel_id,
            name="Updated Channel",
            youtube_id="UCupdated123",
            url="https://youtube.com/@updated",
            subscriber_count=1000,
            db_path=test_db
        )

        assert result is True
        channel = get_my_channel(channel_id, db_path=test_db)
        assert channel["name"] == "Updated Channel"
        assert channel["youtube_id"] == "UCupdated123"
        assert channel["url"] == "https://youtube.com/@updated"
        assert channel["subscriber_count"] == 1000

    def test_update_my_channel_not_found(self, test_db):
        """Test updating a non-existent channel."""
        result = update_my_channel(9999, name="New Name", db_path=test_db)
        assert result is False

    def test_update_my_channel_no_fields(self, test_db, test_niche):
        """Test updating with no fields provided."""
        channel_id = create_my_channel(
            niche_id=test_niche,
            name="Test",
            db_path=test_db
        )
        result = update_my_channel(channel_id, db_path=test_db)
        assert result is False

    def test_update_my_channel_invalid_field(self, test_db, test_niche):
        """Test updating with invalid field name."""
        channel_id = create_my_channel(
            niche_id=test_niche,
            name="Test",
            db_path=test_db
        )

        with pytest.raises(ValueError) as exc_info:
            update_my_channel(channel_id, invalid_field="value", db_path=test_db)

        assert "Invalid fields" in str(exc_info.value)

    def test_update_my_channel_duplicate_youtube_id(self, test_db, test_niche):
        """Test updating youtube_id to a value that already exists."""
        create_my_channel(
            niche_id=test_niche,
            name="First",
            youtube_id="UCfirst",
            db_path=test_db
        )
        channel_id2 = create_my_channel(
            niche_id=test_niche,
            name="Second",
            youtube_id="UCsecond",
            db_path=test_db
        )

        with pytest.raises(sqlite3.IntegrityError) as exc_info:
            update_my_channel(channel_id2, youtube_id="UCfirst", db_path=test_db)

        assert "already exists" in str(exc_info.value)

    def test_update_my_channel_invalid_niche(self, test_db, test_niche):
        """Test updating niche_id to non-existent niche."""
        channel_id = create_my_channel(
            niche_id=test_niche,
            name="Test",
            db_path=test_db
        )

        with pytest.raises(sqlite3.IntegrityError):
            update_my_channel(channel_id, niche_id=9999, db_path=test_db)


class TestDeleteMyChannel:
    """Tests for delete_my_channel function."""

    def test_delete_my_channel_success(self, test_db, test_niche):
        """Test successfully deleting a channel."""
        channel_id = create_my_channel(
            niche_id=test_niche,
            name="To Delete",
            db_path=test_db
        )

        result = delete_my_channel(channel_id, db_path=test_db)

        assert result is True
        # Verify it's gone
        channel = get_my_channel(channel_id, db_path=test_db)
        assert channel is None

    def test_delete_my_channel_not_found(self, test_db):
        """Test deleting a non-existent channel."""
        result = delete_my_channel(9999, db_path=test_db)
        assert result is False

    def test_delete_my_channel_with_foreign_key_constraint(self, test_db, test_niche):
        """Test that deleting a channel with related records fails."""
        channel_id = create_my_channel(
            niche_id=test_niche,
            name="Test",
            db_path=test_db
        )

        # Create a related record (my_video)
        from src.database.schema import get_connection
        conn = get_connection(test_db)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO my_videos (channel_id, niche_id, title)
            VALUES (?, ?, ?)
            """,
            (channel_id, test_niche, "Test Video")
        )
        conn.commit()
        conn.close()

        # Try to delete the channel - should fail
        with pytest.raises(sqlite3.IntegrityError) as exc_info:
            delete_my_channel(channel_id, db_path=test_db)

        assert "related records" in str(exc_info.value)


class TestUpdateSubscriberCount:
    """Tests for update_subscriber_count function."""

    def test_update_subscriber_count_success(self, test_db, test_niche):
        """Test updating subscriber count."""
        channel_id = create_my_channel(
            niche_id=test_niche,
            name="Test Channel",
            subscriber_count=100,
            db_path=test_db
        )

        result = update_subscriber_count(channel_id, 500, db_path=test_db)

        assert result is True
        channel = get_my_channel(channel_id, db_path=test_db)
        assert channel["subscriber_count"] == 500

    def test_update_subscriber_count_not_found(self, test_db):
        """Test updating subscriber count for non-existent channel."""
        result = update_subscriber_count(9999, 1000, db_path=test_db)
        assert result is False


class TestIntegration:
    """Integration tests for combined operations."""

    def test_full_crud_lifecycle(self, test_db, test_niche):
        """Test complete CRUD lifecycle."""
        # Create
        channel_id = create_my_channel(
            niche_id=test_niche,
            name="Test Channel",
            subscriber_count=0,
            db_path=test_db
        )
        assert channel_id > 0

        # Read
        channel = get_my_channel(channel_id, db_path=test_db)
        assert channel["name"] == "Test Channel"
        assert channel["youtube_id"] is None

        # Update - add YouTube ID (channel now created)
        success = update_my_channel(
            channel_id,
            youtube_id="UCnewchannel123",
            url="https://youtube.com/@newchannel",
            db_path=test_db
        )
        assert success is True

        # Verify update
        channel = get_my_channel(channel_id, db_path=test_db)
        assert channel["youtube_id"] == "UCnewchannel123"
        assert channel["url"] == "https://youtube.com/@newchannel"

        # Update subscriber count
        success = update_subscriber_count(channel_id, 1000, db_path=test_db)
        assert success is True

        # Verify subscriber count
        channel = get_my_channel(channel_id, db_path=test_db)
        assert channel["subscriber_count"] == 1000

        # Delete
        success = delete_my_channel(channel_id, db_path=test_db)
        assert success is True

        # Verify deletion
        channel = get_my_channel(channel_id, db_path=test_db)
        assert channel is None

    def test_channel_lifecycle_before_youtube_creation(self, test_db, test_niche):
        """Test typical workflow: plan channel, then add YouTube details after creation."""
        # Create channel before it exists on YouTube
        channel_id = create_my_channel(
            niche_id=test_niche,
            name="Future Channel",
            db_path=test_db
        )

        channel = get_my_channel(channel_id, db_path=test_db)
        assert channel["youtube_id"] is None
        assert channel["subscriber_count"] == 0

        # Later: channel is created on YouTube, add details
        update_my_channel(
            channel_id,
            youtube_id="UCnewlycreated",
            url="https://youtube.com/@newlycreated",
            db_path=test_db
        )

        # Verify it's now linked
        channel = get_my_channel_by_youtube_id("UCnewlycreated", db_path=test_db)
        assert channel is not None
        assert channel["name"] == "Future Channel"

    def test_multiple_niches_with_channels(self, test_db):
        """Test managing channels across multiple niches."""
        # Create two niches
        niche1 = create_niche("Niche 1", "niche-1", db_path=test_db)
        niche2 = create_niche("Niche 2", "niche-2", db_path=test_db)

        # Add channels to each
        create_my_channel(niche_id=niche1, name="N1 Channel 1", db_path=test_db)
        create_my_channel(niche_id=niche1, name="N1 Channel 2", db_path=test_db)
        create_my_channel(niche_id=niche2, name="N2 Channel 1", db_path=test_db)

        # Verify filtering works
        n1_channels = get_channels_by_niche(niche1, db_path=test_db)
        n2_channels = get_channels_by_niche(niche2, db_path=test_db)

        assert len(n1_channels) == 2
        assert len(n2_channels) == 1
        assert all(c["niche_id"] == niche1 for c in n1_channels)
        assert all(c["niche_id"] == niche2 for c in n2_channels)

        # Get all channels
        all_channels = get_all_my_channels(db_path=test_db)
        assert len(all_channels) == 3

    def test_lookup_by_youtube_id(self, test_db, test_niche):
        """Test looking up channels by YouTube ID."""
        create_my_channel(
            niche_id=test_niche,
            name="Test Channel",
            youtube_id="UCtest123",
            subscriber_count=500,
            db_path=test_db
        )

        # Lookup by YouTube ID
        channel = get_my_channel_by_youtube_id("UCtest123", db_path=test_db)
        assert channel is not None
        assert channel["name"] == "Test Channel"
        assert channel["subscriber_count"] == 500
