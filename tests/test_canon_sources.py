"""
Tests for canon_sources CRUD operations.
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path

from src.database.schema import init_db
from src.database.niches import create_niche
from src.database.canon_sources import (
    create_canon_source,
    get_canon_source,
    get_sources_by_niche,
    update_canon_source,
    delete_canon_source,
    mark_as_ingested
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
    """Create a test niche for canon source tests."""
    niche_id = create_niche(
        name="Middle-earth",
        slug="middle-earth",
        niche_type="fiction",
        db_path=test_db
    )
    return niche_id


class TestCreateCanonSource:
    """Tests for create_canon_source function."""

    def test_create_canon_source_full(self, test_db, test_niche):
        """Test creating a canon source with all fields."""
        source_id = create_canon_source(
            niche_id=test_niche,
            title="The Silmarillion",
            author="J.R.R. Tolkien",
            source_type="book",
            file_path="/path/to/silmarillion.pdf",
            url="https://example.com/silmarillion",
            priority=5,
            db_path=test_db
        )

        assert isinstance(source_id, int)
        assert source_id > 0

    def test_create_canon_source_minimal(self, test_db, test_niche):
        """Test creating a canon source with only required fields."""
        source_id = create_canon_source(
            niche_id=test_niche,
            title="Test Source",
            db_path=test_db
        )

        assert isinstance(source_id, int)
        assert source_id > 0

    def test_create_canon_source_invalid_niche(self, test_db):
        """Test that creating a source with invalid niche_id raises IntegrityError."""
        with pytest.raises(sqlite3.IntegrityError) as exc_info:
            create_canon_source(
                niche_id=9999,
                title="Test Source",
                db_path=test_db
            )

        assert "does not exist" in str(exc_info.value)

    def test_create_canon_source_default_priority(self, test_db, test_niche):
        """Test that default priority is 1."""
        source_id = create_canon_source(
            niche_id=test_niche,
            title="Test Source",
            db_path=test_db
        )

        source = get_canon_source(source_id, db_path=test_db)
        assert source["priority"] == 1


class TestGetCanonSource:
    """Tests for get_canon_source function."""

    def test_get_canon_source_success(self, test_db, test_niche):
        """Test retrieving an existing canon source."""
        source_id = create_canon_source(
            niche_id=test_niche,
            title="The Silmarillion",
            author="J.R.R. Tolkien",
            source_type="book",
            file_path="/path/to/file.pdf",
            url="https://example.com",
            priority=3,
            db_path=test_db
        )

        source = get_canon_source(source_id, db_path=test_db)

        assert source is not None
        assert source["id"] == source_id
        assert source["niche_id"] == test_niche
        assert source["title"] == "The Silmarillion"
        assert source["author"] == "J.R.R. Tolkien"
        assert source["source_type"] == "book"
        assert source["file_path"] == "/path/to/file.pdf"
        assert source["url"] == "https://example.com"
        assert source["priority"] == 3
        assert source["ingested"] is False
        assert source["ingested_at"] is None
        assert source["created_at"] is not None

    def test_get_canon_source_not_found(self, test_db):
        """Test retrieving a non-existent canon source."""
        source = get_canon_source(9999, db_path=test_db)
        assert source is None

    def test_get_canon_source_with_null_fields(self, test_db, test_niche):
        """Test retrieving a canon source with null optional fields."""
        source_id = create_canon_source(
            niche_id=test_niche,
            title="Minimal Source",
            db_path=test_db
        )

        source = get_canon_source(source_id, db_path=test_db)

        assert source is not None
        assert source["author"] is None
        assert source["source_type"] is None
        assert source["file_path"] is None
        assert source["url"] is None


class TestGetSourcesByNiche:
    """Tests for get_sources_by_niche function."""

    def test_get_sources_by_niche_empty(self, test_db, test_niche):
        """Test getting sources when niche has no sources."""
        sources = get_sources_by_niche(test_niche, db_path=test_db)
        assert sources == []

    def test_get_sources_by_niche_multiple(self, test_db, test_niche):
        """Test getting multiple sources for a niche."""
        source1 = create_canon_source(
            niche_id=test_niche,
            title="Source 1",
            priority=1,
            db_path=test_db
        )
        source2 = create_canon_source(
            niche_id=test_niche,
            title="Source 2",
            priority=5,
            db_path=test_db
        )
        source3 = create_canon_source(
            niche_id=test_niche,
            title="Source 3",
            priority=3,
            db_path=test_db
        )

        sources = get_sources_by_niche(test_niche, db_path=test_db)

        assert len(sources) == 3
        # Should be ordered by priority DESC
        assert sources[0]["id"] == source2  # priority 5
        assert sources[1]["id"] == source3  # priority 3
        assert sources[2]["id"] == source1  # priority 1

    def test_get_sources_by_niche_ordering_by_title(self, test_db, test_niche):
        """Test that sources with same priority are ordered by title."""
        create_canon_source(
            niche_id=test_niche,
            title="Zebra Book",
            priority=1,
            db_path=test_db
        )
        create_canon_source(
            niche_id=test_niche,
            title="Alpha Book",
            priority=1,
            db_path=test_db
        )

        sources = get_sources_by_niche(test_niche, db_path=test_db)

        assert len(sources) == 2
        # Same priority, should be ordered by title ASC
        assert sources[0]["title"] == "Alpha Book"
        assert sources[1]["title"] == "Zebra Book"

    def test_get_sources_by_niche_filters_correctly(self, test_db):
        """Test that get_sources_by_niche only returns sources for specified niche."""
        niche1 = create_niche("Niche 1", "niche-1", db_path=test_db)
        niche2 = create_niche("Niche 2", "niche-2", db_path=test_db)

        create_canon_source(niche_id=niche1, title="Source N1", db_path=test_db)
        create_canon_source(niche_id=niche2, title="Source N2", db_path=test_db)

        sources_n1 = get_sources_by_niche(niche1, db_path=test_db)
        sources_n2 = get_sources_by_niche(niche2, db_path=test_db)

        assert len(sources_n1) == 1
        assert sources_n1[0]["title"] == "Source N1"
        assert len(sources_n2) == 1
        assert sources_n2[0]["title"] == "Source N2"


class TestUpdateCanonSource:
    """Tests for update_canon_source function."""

    def test_update_canon_source_single_field(self, test_db, test_niche):
        """Test updating a single field."""
        source_id = create_canon_source(
            niche_id=test_niche,
            title="Original Title",
            db_path=test_db
        )

        result = update_canon_source(source_id, title="Updated Title", db_path=test_db)

        assert result is True
        source = get_canon_source(source_id, db_path=test_db)
        assert source["title"] == "Updated Title"

    def test_update_canon_source_multiple_fields(self, test_db, test_niche):
        """Test updating multiple fields."""
        source_id = create_canon_source(
            niche_id=test_niche,
            title="Original",
            db_path=test_db
        )

        result = update_canon_source(
            source_id,
            title="Updated Title",
            author="New Author",
            source_type="wiki",
            priority=10,
            db_path=test_db
        )

        assert result is True
        source = get_canon_source(source_id, db_path=test_db)
        assert source["title"] == "Updated Title"
        assert source["author"] == "New Author"
        assert source["source_type"] == "wiki"
        assert source["priority"] == 10

    def test_update_canon_source_not_found(self, test_db):
        """Test updating a non-existent canon source."""
        result = update_canon_source(9999, title="New Title", db_path=test_db)
        assert result is False

    def test_update_canon_source_no_fields(self, test_db, test_niche):
        """Test updating with no fields provided."""
        source_id = create_canon_source(
            niche_id=test_niche,
            title="Test",
            db_path=test_db
        )
        result = update_canon_source(source_id, db_path=test_db)
        assert result is False

    def test_update_canon_source_invalid_field(self, test_db, test_niche):
        """Test updating with invalid field name."""
        source_id = create_canon_source(
            niche_id=test_niche,
            title="Test",
            db_path=test_db
        )

        with pytest.raises(ValueError) as exc_info:
            update_canon_source(source_id, invalid_field="value", db_path=test_db)

        assert "Invalid fields" in str(exc_info.value)

    def test_update_canon_source_invalid_niche(self, test_db, test_niche):
        """Test updating niche_id to non-existent niche."""
        source_id = create_canon_source(
            niche_id=test_niche,
            title="Test",
            db_path=test_db
        )

        with pytest.raises(sqlite3.IntegrityError) as exc_info:
            update_canon_source(source_id, niche_id=9999, db_path=test_db)

        assert "does not exist" in str(exc_info.value)


class TestDeleteCanonSource:
    """Tests for delete_canon_source function."""

    def test_delete_canon_source_success(self, test_db, test_niche):
        """Test successfully deleting a canon source."""
        source_id = create_canon_source(
            niche_id=test_niche,
            title="To Delete",
            db_path=test_db
        )

        result = delete_canon_source(source_id, db_path=test_db)

        assert result is True
        # Verify it's gone
        source = get_canon_source(source_id, db_path=test_db)
        assert source is None

    def test_delete_canon_source_not_found(self, test_db):
        """Test deleting a non-existent canon source."""
        result = delete_canon_source(9999, db_path=test_db)
        assert result is False

    def test_delete_canon_source_with_foreign_key_constraint(self, test_db, test_niche):
        """Test that deleting a source with related records fails."""
        source_id = create_canon_source(
            niche_id=test_niche,
            title="Test",
            db_path=test_db
        )

        # Create a related record (glossary entry)
        from src.database.schema import get_connection
        conn = get_connection(test_db)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO glossary (niche_id, term, source_id)
            VALUES (?, ?, ?)
            """,
            (test_niche, "Test Term", source_id)
        )
        conn.commit()
        conn.close()

        # Try to delete the source - should fail
        with pytest.raises(sqlite3.IntegrityError) as exc_info:
            delete_canon_source(source_id, db_path=test_db)

        assert "related records" in str(exc_info.value)


class TestMarkAsIngested:
    """Tests for mark_as_ingested function."""

    def test_mark_as_ingested_success(self, test_db, test_niche):
        """Test marking a source as ingested."""
        source_id = create_canon_source(
            niche_id=test_niche,
            title="Test Source",
            db_path=test_db
        )

        # Initially not ingested
        source = get_canon_source(source_id, db_path=test_db)
        assert source["ingested"] is False
        assert source["ingested_at"] is None

        # Mark as ingested
        result = mark_as_ingested(source_id, db_path=test_db)
        assert result is True

        # Verify it's marked
        source = get_canon_source(source_id, db_path=test_db)
        assert source["ingested"] is True
        assert source["ingested_at"] is not None

    def test_mark_as_ingested_not_found(self, test_db):
        """Test marking a non-existent source as ingested."""
        result = mark_as_ingested(9999, db_path=test_db)
        assert result is False

    def test_mark_as_ingested_idempotent(self, test_db, test_niche):
        """Test that marking as ingested multiple times is safe."""
        source_id = create_canon_source(
            niche_id=test_niche,
            title="Test Source",
            db_path=test_db
        )

        # Mark as ingested twice
        result1 = mark_as_ingested(source_id, db_path=test_db)
        result2 = mark_as_ingested(source_id, db_path=test_db)

        assert result1 is True
        assert result2 is True

        # Should still be marked as ingested
        source = get_canon_source(source_id, db_path=test_db)
        assert source["ingested"] is True


class TestIntegration:
    """Integration tests for combined operations."""

    def test_full_crud_lifecycle(self, test_db, test_niche):
        """Test complete CRUD lifecycle."""
        # Create
        source_id = create_canon_source(
            niche_id=test_niche,
            title="Test Source",
            author="Test Author",
            source_type="book",
            priority=3,
            db_path=test_db
        )
        assert source_id > 0

        # Read
        source = get_canon_source(source_id, db_path=test_db)
        assert source["title"] == "Test Source"
        assert source["ingested"] is False

        # Update
        success = update_canon_source(
            source_id,
            title="Updated Source",
            priority=5,
            db_path=test_db
        )
        assert success is True

        # Verify update
        source = get_canon_source(source_id, db_path=test_db)
        assert source["title"] == "Updated Source"
        assert source["priority"] == 5

        # Mark as ingested
        success = mark_as_ingested(source_id, db_path=test_db)
        assert success is True

        # Verify ingestion
        source = get_canon_source(source_id, db_path=test_db)
        assert source["ingested"] is True

        # Delete
        success = delete_canon_source(source_id, db_path=test_db)
        assert success is True

        # Verify deletion
        source = get_canon_source(source_id, db_path=test_db)
        assert source is None

    def test_multiple_niches_with_sources(self, test_db):
        """Test managing sources across multiple niches."""
        # Create two niches
        niche1 = create_niche("Niche 1", "niche-1", db_path=test_db)
        niche2 = create_niche("Niche 2", "niche-2", db_path=test_db)

        # Add sources to each
        create_canon_source(niche_id=niche1, title="N1 Source 1", db_path=test_db)
        create_canon_source(niche_id=niche1, title="N1 Source 2", db_path=test_db)
        create_canon_source(niche_id=niche2, title="N2 Source 1", db_path=test_db)

        # Verify filtering works
        n1_sources = get_sources_by_niche(niche1, db_path=test_db)
        n2_sources = get_sources_by_niche(niche2, db_path=test_db)

        assert len(n1_sources) == 2
        assert len(n2_sources) == 1
        assert all(s["niche_id"] == niche1 for s in n1_sources)
        assert all(s["niche_id"] == niche2 for s in n2_sources)
