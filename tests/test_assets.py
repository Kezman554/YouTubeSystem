"""
Tests for assets CRUD operations.
"""

import pytest
import sqlite3
from pathlib import Path

from src.database.schema import init_db
from src.database.niches import create_niche
from src.database.my_channels import create_my_channel
from src.database.my_videos import create_my_video
from src.database.assets import (
    create_asset,
    get_asset,
    get_assets_by_niche,
    get_assets_by_type,
    get_assets_by_source,
    update_asset,
    delete_asset,
    record_usage
)


@pytest.fixture
def test_db(tmp_path):
    """Create a temporary test database."""
    db_path = tmp_path / "test.db"
    init_db(db_path)
    return db_path


@pytest.fixture
def test_niche(test_db):
    """Create a test niche."""
    return create_niche(
        name="LOTR",
        slug="lotr",
        niche_type="education",
        description="Lord of the Rings content",
        db_path=test_db
    )


@pytest.fixture
def test_channel(test_db, test_niche):
    """Create a test channel."""
    return create_my_channel(
        niche_id=test_niche,
        name="LOTR Facts",
        db_path=test_db
    )


@pytest.fixture
def test_video(test_db, test_channel, test_niche):
    """Create a test video."""
    return create_my_video(
        channel_id=test_channel,
        niche_id=test_niche,
        title="Test Video",
        status="published",
        db_path=test_db
    )


class TestCreateAsset:
    """Test creating assets."""

    def test_create_asset_minimal(self, test_db, test_niche):
        """Create an asset with minimal required fields."""
        asset_id = create_asset(
            niche_id=test_niche,
            file_path="/path/to/image.png",
            db_path=test_db
        )
        assert asset_id > 0

        # Verify it was created
        asset = get_asset(asset_id, test_db)
        assert asset is not None
        assert asset["niche_id"] == test_niche
        assert asset["file_path"] == "/path/to/image.png"
        assert asset["times_used"] == 0

    def test_create_asset_full(self, test_db, test_niche):
        """Create an asset with all fields."""
        asset_id = create_asset(
            niche_id=test_niche,
            file_path="/path/to/gandalf.png",
            file_type="image",
            source="stable_diffusion",
            prompt="gandalf the grey holding staff",
            description="Gandalf with his staff",
            subject_tags='["gandalf", "staff", "magic"]',
            mood_tags='["dramatic", "mystical"]',
            style_tags='["painted", "cinematic"]',
            db_path=test_db
        )
        assert asset_id > 0

        # Verify all fields
        asset = get_asset(asset_id, test_db)
        assert asset["file_type"] == "image"
        assert asset["source"] == "stable_diffusion"
        assert asset["prompt"] == "gandalf the grey holding staff"
        assert asset["description"] == "Gandalf with his staff"
        assert asset["subject_tags"] == '["gandalf", "staff", "magic"]'
        assert asset["mood_tags"] == '["dramatic", "mystical"]'
        assert asset["style_tags"] == '["painted", "cinematic"]'

    def test_create_asset_invalid_niche(self, test_db):
        """Creating an asset with invalid niche_id should raise IntegrityError."""
        with pytest.raises(sqlite3.IntegrityError):
            create_asset(
                niche_id=999,
                file_path="/path/to/image.png",
                db_path=test_db
            )


class TestGetAsset:
    """Test retrieving assets."""

    def test_get_asset_success(self, test_db, test_niche):
        """Get an existing asset."""
        asset_id = create_asset(
            niche_id=test_niche,
            file_path="/path/to/image.png",
            file_type="image",
            db_path=test_db
        )

        asset = get_asset(asset_id, test_db)
        assert asset is not None
        assert asset["id"] == asset_id
        assert asset["niche_id"] == test_niche
        assert asset["file_path"] == "/path/to/image.png"
        assert asset["file_type"] == "image"

    def test_get_asset_not_found(self, test_db):
        """Get a non-existent asset should return None."""
        asset = get_asset(999, test_db)
        assert asset is None

    def test_get_asset_with_null_fields(self, test_db, test_niche):
        """Get an asset with NULL optional fields."""
        asset_id = create_asset(
            niche_id=test_niche,
            file_path="/path/to/image.png",
            db_path=test_db
        )

        asset = get_asset(asset_id, test_db)
        assert asset["file_type"] is None
        assert asset["source"] is None
        assert asset["prompt"] is None
        assert asset["last_used_in"] is None
        assert asset["last_used_at"] is None


class TestGetAssetsByNiche:
    """Test retrieving assets by niche."""

    def test_get_assets_by_niche_empty(self, test_db, test_niche):
        """Get assets for a niche with no assets."""
        assets = get_assets_by_niche(test_niche, test_db)
        assert assets == []

    def test_get_assets_by_niche_multiple(self, test_db, test_niche):
        """Get multiple assets for a niche."""
        id1 = create_asset(
            niche_id=test_niche,
            file_path="/path/to/image1.png",
            db_path=test_db
        )
        id2 = create_asset(
            niche_id=test_niche,
            file_path="/path/to/image2.png",
            db_path=test_db
        )
        id3 = create_asset(
            niche_id=test_niche,
            file_path="/path/to/image3.png",
            db_path=test_db
        )

        assets = get_assets_by_niche(test_niche, test_db)
        assert len(assets) == 3
        # Should be ordered by created_at DESC (newest first)
        assert {assets[0]["id"], assets[1]["id"], assets[2]["id"]} == {id1, id2, id3}


class TestGetAssetsByType:
    """Test retrieving assets by file type."""

    def test_get_assets_by_type_empty(self, test_db):
        """Get assets for a type with no assets."""
        assets = get_assets_by_type("image", test_db)
        assert assets == []

    def test_get_assets_by_type_multiple(self, test_db, test_niche):
        """Get multiple assets of the same type."""
        id1 = create_asset(
            niche_id=test_niche,
            file_path="/path/to/image1.png",
            file_type="image",
            db_path=test_db
        )
        id2 = create_asset(
            niche_id=test_niche,
            file_path="/path/to/video.mp4",
            file_type="video",
            db_path=test_db
        )
        id3 = create_asset(
            niche_id=test_niche,
            file_path="/path/to/image2.png",
            file_type="image",
            db_path=test_db
        )

        images = get_assets_by_type("image", test_db)
        assert len(images) == 2
        assert {images[0]["id"], images[1]["id"]} == {id1, id3}

        videos = get_assets_by_type("video", test_db)
        assert len(videos) == 1
        assert videos[0]["id"] == id2


class TestGetAssetsBySource:
    """Test retrieving assets by source."""

    def test_get_assets_by_source_empty(self, test_db):
        """Get assets for a source with no assets."""
        assets = get_assets_by_source("stable_diffusion", test_db)
        assert assets == []

    def test_get_assets_by_source_multiple(self, test_db, test_niche):
        """Get multiple assets from the same source."""
        id1 = create_asset(
            niche_id=test_niche,
            file_path="/path/to/image1.png",
            source="stable_diffusion",
            db_path=test_db
        )
        id2 = create_asset(
            niche_id=test_niche,
            file_path="/path/to/image2.png",
            source="midjourney",
            db_path=test_db
        )
        id3 = create_asset(
            niche_id=test_niche,
            file_path="/path/to/image3.png",
            source="stable_diffusion",
            db_path=test_db
        )

        sd_assets = get_assets_by_source("stable_diffusion", test_db)
        assert len(sd_assets) == 2
        assert {sd_assets[0]["id"], sd_assets[1]["id"]} == {id1, id3}

        mj_assets = get_assets_by_source("midjourney", test_db)
        assert len(mj_assets) == 1
        assert mj_assets[0]["id"] == id2


class TestUpdateAsset:
    """Test updating assets."""

    def test_update_asset_single_field(self, test_db, test_niche):
        """Update a single field."""
        asset_id = create_asset(
            niche_id=test_niche,
            file_path="/path/to/image.png",
            db_path=test_db
        )

        result = update_asset(asset_id, test_db, description="Updated description")
        assert result is True

        asset = get_asset(asset_id, test_db)
        assert asset["description"] == "Updated description"

    def test_update_asset_multiple_fields(self, test_db, test_niche):
        """Update multiple fields."""
        asset_id = create_asset(
            niche_id=test_niche,
            file_path="/path/to/image.png",
            db_path=test_db
        )

        result = update_asset(
            asset_id,
            test_db,
            file_type="image",
            source="stable_diffusion",
            description="AI generated image",
            subject_tags='["fantasy", "magic"]'
        )
        assert result is True

        asset = get_asset(asset_id, test_db)
        assert asset["file_type"] == "image"
        assert asset["source"] == "stable_diffusion"
        assert asset["description"] == "AI generated image"
        assert asset["subject_tags"] == '["fantasy", "magic"]'

    def test_update_asset_not_found(self, test_db):
        """Update a non-existent asset should return False."""
        result = update_asset(999, test_db, description="Test")
        assert result is False

    def test_update_asset_no_fields(self, test_db, test_niche):
        """Update with no fields should return False."""
        asset_id = create_asset(
            niche_id=test_niche,
            file_path="/path/to/image.png",
            db_path=test_db
        )

        result = update_asset(asset_id, test_db)
        assert result is False

    def test_update_asset_invalid_field(self, test_db, test_niche):
        """Update with invalid field should raise ValueError."""
        asset_id = create_asset(
            niche_id=test_niche,
            file_path="/path/to/image.png",
            db_path=test_db
        )

        with pytest.raises(ValueError):
            update_asset(asset_id, test_db, invalid_field="value")

    def test_update_asset_invalid_niche(self, test_db, test_niche):
        """Update with invalid niche_id should raise IntegrityError."""
        asset_id = create_asset(
            niche_id=test_niche,
            file_path="/path/to/image.png",
            db_path=test_db
        )

        with pytest.raises(sqlite3.IntegrityError):
            update_asset(asset_id, test_db, niche_id=999)


class TestDeleteAsset:
    """Test deleting assets."""

    def test_delete_asset_success(self, test_db, test_niche):
        """Delete an existing asset."""
        asset_id = create_asset(
            niche_id=test_niche,
            file_path="/path/to/image.png",
            db_path=test_db
        )

        result = delete_asset(asset_id, test_db)
        assert result is True

        # Verify it's gone
        asset = get_asset(asset_id, test_db)
        assert asset is None

    def test_delete_asset_not_found(self, test_db):
        """Delete a non-existent asset should return False."""
        result = delete_asset(999, test_db)
        assert result is False


class TestRecordUsage:
    """Test recording asset usage."""

    def test_record_usage_success(self, test_db, test_niche, test_video):
        """Record asset usage in a video."""
        asset_id = create_asset(
            niche_id=test_niche,
            file_path="/path/to/image.png",
            db_path=test_db
        )

        result = record_usage(asset_id, test_video, test_db)
        assert result is True

        # Verify usage was recorded
        asset = get_asset(asset_id, test_db)
        assert asset["times_used"] == 1
        assert asset["last_used_in"] == test_video
        assert asset["last_used_at"] is not None

    def test_record_usage_multiple_times(self, test_db, test_niche, test_video):
        """Record multiple usages of the same asset."""
        asset_id = create_asset(
            niche_id=test_niche,
            file_path="/path/to/image.png",
            db_path=test_db
        )

        # Use it 3 times
        record_usage(asset_id, test_video, test_db)
        record_usage(asset_id, test_video, test_db)
        record_usage(asset_id, test_video, test_db)

        asset = get_asset(asset_id, test_db)
        assert asset["times_used"] == 3
        assert asset["last_used_in"] == test_video

    def test_record_usage_asset_not_found(self, test_db, test_video):
        """Record usage for non-existent asset should return False."""
        result = record_usage(999, test_video, test_db)
        assert result is False

    def test_record_usage_invalid_video(self, test_db, test_niche):
        """Record usage with invalid video_id should raise IntegrityError."""
        asset_id = create_asset(
            niche_id=test_niche,
            file_path="/path/to/image.png",
            db_path=test_db
        )

        with pytest.raises(sqlite3.IntegrityError):
            record_usage(asset_id, 999, test_db)


class TestIntegration:
    """Integration tests for complex scenarios."""

    def test_asset_lifecycle(self, test_db, test_niche, test_video):
        """Test full asset lifecycle."""
        # Create asset
        asset_id = create_asset(
            niche_id=test_niche,
            file_path="/path/to/gandalf.png",
            file_type="image",
            source="stable_diffusion",
            db_path=test_db
        )

        # Update metadata
        update_asset(
            asset_id,
            test_db,
            description="Gandalf with staff",
            subject_tags='["gandalf", "wizard"]'
        )

        # Record usage
        record_usage(asset_id, test_video, test_db)
        record_usage(asset_id, test_video, test_db)

        # Verify final state
        asset = get_asset(asset_id, test_db)
        assert asset["description"] == "Gandalf with staff"
        assert asset["subject_tags"] == '["gandalf", "wizard"]'
        assert asset["times_used"] == 2
        assert asset["last_used_in"] == test_video

    def test_multiple_niches_different_types(self, test_db):
        """Test assets across multiple niches and types."""
        # Create two niches
        niche1 = create_niche(name="LOTR", slug="lotr", db_path=test_db)
        niche2 = create_niche(name="History", slug="history", db_path=test_db)

        # Create assets for each niche
        create_asset(niche_id=niche1, file_path="/lotr/img1.png", file_type="image", db_path=test_db)
        create_asset(niche_id=niche1, file_path="/lotr/vid1.mp4", file_type="video", db_path=test_db)
        create_asset(niche_id=niche2, file_path="/history/img1.png", file_type="image", db_path=test_db)

        # Verify filtering
        lotr_assets = get_assets_by_niche(niche1, test_db)
        assert len(lotr_assets) == 2

        history_assets = get_assets_by_niche(niche2, test_db)
        assert len(history_assets) == 1

        all_images = get_assets_by_type("image", test_db)
        assert len(all_images) == 2

        all_videos = get_assets_by_type("video", test_db)
        assert len(all_videos) == 1

    def test_search_by_source(self, test_db, test_niche):
        """Test filtering assets by generation source."""
        create_asset(
            niche_id=test_niche,
            file_path="/sd1.png",
            source="stable_diffusion",
            db_path=test_db
        )
        create_asset(
            niche_id=test_niche,
            file_path="/mj1.png",
            source="midjourney",
            db_path=test_db
        )
        create_asset(
            niche_id=test_niche,
            file_path="/stock1.png",
            source="stock",
            db_path=test_db
        )
        create_asset(
            niche_id=test_niche,
            file_path="/sd2.png",
            source="stable_diffusion",
            db_path=test_db
        )

        sd_assets = get_assets_by_source("stable_diffusion", test_db)
        assert len(sd_assets) == 2

        mj_assets = get_assets_by_source("midjourney", test_db)
        assert len(mj_assets) == 1

        stock_assets = get_assets_by_source("stock", test_db)
        assert len(stock_assets) == 1
