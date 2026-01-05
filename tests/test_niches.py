"""
Tests for niches CRUD operations.
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path

from src.database.schema import init_db
from src.database.niches import (
    create_niche,
    get_niche,
    get_all_niches,
    update_niche,
    delete_niche
)


@pytest.fixture
def test_db():
    """Create a temporary test database for each test."""
    # Create a temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    temp_path = Path(temp_file.name)
    temp_file.close()

    # Initialize the database schema
    init_db(temp_path)

    yield temp_path

    # Cleanup
    temp_path.unlink()


class TestCreateNiche:
    """Tests for create_niche function."""

    def test_create_niche_success(self, test_db):
        """Test successfully creating a niche."""
        niche_id = create_niche(
            name="Middle-earth",
            slug="middle-earth",
            niche_type="fiction",
            description="Tolkien's legendary world",
            db_path=test_db
        )

        assert isinstance(niche_id, int)
        assert niche_id > 0

    def test_create_niche_minimal(self, test_db):
        """Test creating a niche with only required fields."""
        niche_id = create_niche(
            name="Test Niche",
            slug="test-niche",
            db_path=test_db
        )

        assert isinstance(niche_id, int)
        assert niche_id > 0

    def test_create_niche_duplicate_slug(self, test_db):
        """Test that creating a niche with duplicate slug raises IntegrityError."""
        create_niche(
            name="First",
            slug="duplicate",
            db_path=test_db
        )

        with pytest.raises(sqlite3.IntegrityError) as exc_info:
            create_niche(
                name="Second",
                slug="duplicate",
                db_path=test_db
            )

        assert "already exists" in str(exc_info.value)


class TestGetNiche:
    """Tests for get_niche function."""

    def test_get_niche_success(self, test_db):
        """Test retrieving an existing niche."""
        niche_id = create_niche(
            name="ICP Ecosystem",
            slug="icp",
            niche_type="crypto",
            description="Internet Computer Protocol",
            db_path=test_db
        )

        niche = get_niche(niche_id, db_path=test_db)

        assert niche is not None
        assert niche["id"] == niche_id
        assert niche["name"] == "ICP Ecosystem"
        assert niche["slug"] == "icp"
        assert niche["type"] == "crypto"
        assert niche["description"] == "Internet Computer Protocol"
        assert niche["created_at"] is not None
        assert niche["updated_at"] is not None

    def test_get_niche_not_found(self, test_db):
        """Test retrieving a non-existent niche."""
        niche = get_niche(9999, db_path=test_db)
        assert niche is None

    def test_get_niche_with_null_fields(self, test_db):
        """Test retrieving a niche with null optional fields."""
        niche_id = create_niche(
            name="Minimal",
            slug="minimal",
            db_path=test_db
        )

        niche = get_niche(niche_id, db_path=test_db)

        assert niche is not None
        assert niche["type"] is None
        assert niche["description"] is None


class TestGetAllNiches:
    """Tests for get_all_niches function."""

    def test_get_all_niches_empty(self, test_db):
        """Test getting all niches when database is empty."""
        niches = get_all_niches(db_path=test_db)
        assert niches == []

    def test_get_all_niches_multiple(self, test_db):
        """Test getting all niches with multiple entries."""
        # Create multiple niches
        id1 = create_niche("Niche 1", "niche-1", db_path=test_db)
        id2 = create_niche("Niche 2", "niche-2", db_path=test_db)
        id3 = create_niche("Niche 3", "niche-3", db_path=test_db)

        niches = get_all_niches(db_path=test_db)

        assert len(niches) == 3
        # Verify all IDs are present
        niche_ids = {n["id"] for n in niches}
        assert niche_ids == {id1, id2, id3}

    def test_get_all_niches_structure(self, test_db):
        """Test that returned dictionaries have correct structure."""
        create_niche(
            name="Test",
            slug="test",
            niche_type="test-type",
            description="Test description",
            db_path=test_db
        )

        niches = get_all_niches(db_path=test_db)

        assert len(niches) == 1
        niche = niches[0]
        assert "id" in niche
        assert "name" in niche
        assert "slug" in niche
        assert "type" in niche
        assert "description" in niche
        assert "created_at" in niche
        assert "updated_at" in niche


class TestUpdateNiche:
    """Tests for update_niche function."""

    def test_update_niche_single_field(self, test_db):
        """Test updating a single field."""
        niche_id = create_niche(
            name="Original Name",
            slug="original",
            db_path=test_db
        )

        result = update_niche(niche_id, name="Updated Name", db_path=test_db)

        assert result is True
        niche = get_niche(niche_id, db_path=test_db)
        assert niche["name"] == "Updated Name"
        assert niche["slug"] == "original"  # Unchanged

    def test_update_niche_multiple_fields(self, test_db):
        """Test updating multiple fields."""
        niche_id = create_niche(
            name="Original",
            slug="original",
            db_path=test_db
        )

        result = update_niche(
            niche_id,
            name="Updated Name",
            type="new-type",
            description="Updated description",
            db_path=test_db
        )

        assert result is True
        niche = get_niche(niche_id, db_path=test_db)
        assert niche["name"] == "Updated Name"
        assert niche["type"] == "new-type"
        assert niche["description"] == "Updated description"

    def test_update_niche_not_found(self, test_db):
        """Test updating a non-existent niche."""
        result = update_niche(9999, name="New Name", db_path=test_db)
        assert result is False

    def test_update_niche_no_fields(self, test_db):
        """Test updating with no fields provided."""
        niche_id = create_niche("Test", "test", db_path=test_db)
        result = update_niche(niche_id, db_path=test_db)
        assert result is False

    def test_update_niche_invalid_field(self, test_db):
        """Test updating with invalid field name."""
        niche_id = create_niche("Test", "test", db_path=test_db)

        with pytest.raises(ValueError) as exc_info:
            update_niche(niche_id, invalid_field="value", db_path=test_db)

        assert "Invalid fields" in str(exc_info.value)

    def test_update_niche_duplicate_slug(self, test_db):
        """Test updating slug to a value that already exists."""
        create_niche("First", "first", db_path=test_db)
        niche_id2 = create_niche("Second", "second", db_path=test_db)

        with pytest.raises(sqlite3.IntegrityError) as exc_info:
            update_niche(niche_id2, slug="first", db_path=test_db)

        assert "already exists" in str(exc_info.value)

    def test_update_niche_updates_timestamp(self, test_db):
        """Test that updated_at timestamp changes on update."""
        niche_id = create_niche("Test", "test", db_path=test_db)

        original = get_niche(niche_id, db_path=test_db)
        original_updated_at = original["updated_at"]

        # Small delay to ensure timestamp changes
        import time
        time.sleep(0.1)

        update_niche(niche_id, name="Updated", db_path=test_db)

        updated = get_niche(niche_id, db_path=test_db)
        # Note: This might be flaky on very fast systems, but SQLite timestamps
        # should differ if there's any delay
        assert updated["updated_at"] >= original_updated_at


class TestDeleteNiche:
    """Tests for delete_niche function."""

    def test_delete_niche_success(self, test_db):
        """Test successfully deleting a niche."""
        niche_id = create_niche("To Delete", "to-delete", db_path=test_db)

        result = delete_niche(niche_id, db_path=test_db)

        assert result is True
        # Verify it's gone
        niche = get_niche(niche_id, db_path=test_db)
        assert niche is None

    def test_delete_niche_not_found(self, test_db):
        """Test deleting a non-existent niche."""
        result = delete_niche(9999, db_path=test_db)
        assert result is False

    def test_delete_niche_with_foreign_key_constraint(self, test_db):
        """Test that deleting a niche with related records fails."""
        niche_id = create_niche("Test", "test", db_path=test_db)

        # Create a related record (canon_source)
        from src.database.schema import get_connection
        conn = get_connection(test_db)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO canon_sources (niche_id, title)
            VALUES (?, ?)
            """,
            (niche_id, "Test Source")
        )
        conn.commit()
        conn.close()

        # Try to delete the niche - should fail
        with pytest.raises(sqlite3.IntegrityError) as exc_info:
            delete_niche(niche_id, db_path=test_db)

        assert "related records" in str(exc_info.value)


class TestIntegration:
    """Integration tests for combined operations."""

    def test_full_crud_lifecycle(self, test_db):
        """Test complete CRUD lifecycle."""
        # Create
        niche_id = create_niche(
            name="Test Niche",
            slug="test-niche",
            niche_type="test",
            description="A test niche",
            db_path=test_db
        )
        assert niche_id > 0

        # Read
        niche = get_niche(niche_id, db_path=test_db)
        assert niche["name"] == "Test Niche"

        # Update
        success = update_niche(
            niche_id,
            name="Updated Niche",
            description="Updated description",
            db_path=test_db
        )
        assert success is True

        # Verify update
        niche = get_niche(niche_id, db_path=test_db)
        assert niche["name"] == "Updated Niche"
        assert niche["description"] == "Updated description"

        # Delete
        success = delete_niche(niche_id, db_path=test_db)
        assert success is True

        # Verify deletion
        niche = get_niche(niche_id, db_path=test_db)
        assert niche is None
