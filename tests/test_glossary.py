"""
Tests for glossary CRUD operations.
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path

from src.database.schema import init_db
from src.database.niches import create_niche
from src.database.canon_sources import create_canon_source
from src.database.glossary import (
    create_glossary_entry,
    get_glossary_entry,
    get_glossary_by_niche,
    search_glossary_by_term,
    update_glossary_entry,
    delete_glossary_entry
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
    """Create a test niche for glossary tests."""
    niche_id = create_niche(
        name="Middle-earth",
        slug="middle-earth",
        niche_type="fiction",
        db_path=test_db
    )
    return niche_id


@pytest.fixture
def test_source(test_db, test_niche):
    """Create a test canon source for glossary tests."""
    source_id = create_canon_source(
        niche_id=test_niche,
        title="The Silmarillion",
        author="J.R.R. Tolkien",
        db_path=test_db
    )
    return source_id


class TestCreateGlossaryEntry:
    """Tests for create_glossary_entry function."""

    def test_create_glossary_entry_full(self, test_db, test_niche, test_source):
        """Test creating a glossary entry with all fields."""
        entry_id = create_glossary_entry(
            niche_id=test_niche,
            term="Boromir",
            term_type="character",
            phonetic_hints="borrow-meer,bore-oh-mir",
            aliases='["Son of Denethor", "Captain of Gondor"]',
            description="The eldest son of Denethor II",
            source_id=test_source,
            db_path=test_db
        )

        assert isinstance(entry_id, int)
        assert entry_id > 0

    def test_create_glossary_entry_minimal(self, test_db, test_niche):
        """Test creating a glossary entry with only required fields."""
        entry_id = create_glossary_entry(
            niche_id=test_niche,
            term="Gondor",
            db_path=test_db
        )

        assert isinstance(entry_id, int)
        assert entry_id > 0

    def test_create_glossary_entry_invalid_niche(self, test_db):
        """Test that creating an entry with invalid niche_id raises IntegrityError."""
        with pytest.raises(sqlite3.IntegrityError):
            create_glossary_entry(
                niche_id=9999,
                term="Test Term",
                db_path=test_db
            )

    def test_create_glossary_entry_invalid_source(self, test_db, test_niche):
        """Test that creating an entry with invalid source_id raises IntegrityError."""
        with pytest.raises(sqlite3.IntegrityError):
            create_glossary_entry(
                niche_id=test_niche,
                term="Test Term",
                source_id=9999,
                db_path=test_db
            )


class TestGetGlossaryEntry:
    """Tests for get_glossary_entry function."""

    def test_get_glossary_entry_success(self, test_db, test_niche, test_source):
        """Test retrieving an existing glossary entry."""
        entry_id = create_glossary_entry(
            niche_id=test_niche,
            term="Aragorn",
            term_type="character",
            phonetic_hints="air-ah-gorn",
            aliases='["Strider", "Elessar"]',
            description="King of Gondor",
            source_id=test_source,
            db_path=test_db
        )

        entry = get_glossary_entry(entry_id, db_path=test_db)

        assert entry is not None
        assert entry["id"] == entry_id
        assert entry["niche_id"] == test_niche
        assert entry["term"] == "Aragorn"
        assert entry["term_type"] == "character"
        assert entry["phonetic_hints"] == "air-ah-gorn"
        assert entry["aliases"] == '["Strider", "Elessar"]'
        assert entry["description"] == "King of Gondor"
        assert entry["source_id"] == test_source
        assert entry["created_at"] is not None

    def test_get_glossary_entry_not_found(self, test_db):
        """Test retrieving a non-existent glossary entry."""
        entry = get_glossary_entry(9999, db_path=test_db)
        assert entry is None

    def test_get_glossary_entry_with_null_fields(self, test_db, test_niche):
        """Test retrieving a glossary entry with null optional fields."""
        entry_id = create_glossary_entry(
            niche_id=test_niche,
            term="Minimal Term",
            db_path=test_db
        )

        entry = get_glossary_entry(entry_id, db_path=test_db)

        assert entry is not None
        assert entry["term_type"] is None
        assert entry["phonetic_hints"] is None
        assert entry["aliases"] is None
        assert entry["description"] is None
        assert entry["source_id"] is None


class TestGetGlossaryByNiche:
    """Tests for get_glossary_by_niche function."""

    def test_get_glossary_by_niche_empty(self, test_db, test_niche):
        """Test getting glossary entries when niche has no entries."""
        entries = get_glossary_by_niche(test_niche, db_path=test_db)
        assert entries == []

    def test_get_glossary_by_niche_multiple(self, test_db, test_niche):
        """Test getting multiple glossary entries for a niche."""
        id1 = create_glossary_entry(
            niche_id=test_niche,
            term="Frodo",
            db_path=test_db
        )
        id2 = create_glossary_entry(
            niche_id=test_niche,
            term="Gandalf",
            db_path=test_db
        )
        id3 = create_glossary_entry(
            niche_id=test_niche,
            term="Aragorn",
            db_path=test_db
        )

        entries = get_glossary_by_niche(test_niche, db_path=test_db)

        assert len(entries) == 3
        # Should be ordered alphabetically by term
        assert entries[0]["term"] == "Aragorn"
        assert entries[1]["term"] == "Frodo"
        assert entries[2]["term"] == "Gandalf"

    def test_get_glossary_by_niche_filters_correctly(self, test_db):
        """Test that get_glossary_by_niche only returns entries for specified niche."""
        niche1 = create_niche("Niche 1", "niche-1", db_path=test_db)
        niche2 = create_niche("Niche 2", "niche-2", db_path=test_db)

        create_glossary_entry(niche_id=niche1, term="Term N1", db_path=test_db)
        create_glossary_entry(niche_id=niche2, term="Term N2", db_path=test_db)

        entries_n1 = get_glossary_by_niche(niche1, db_path=test_db)
        entries_n2 = get_glossary_by_niche(niche2, db_path=test_db)

        assert len(entries_n1) == 1
        assert entries_n1[0]["term"] == "Term N1"
        assert len(entries_n2) == 1
        assert entries_n2[0]["term"] == "Term N2"

    def test_get_glossary_by_niche_filter_by_term_type(self, test_db, test_niche):
        """Test filtering glossary entries by term_type."""
        create_glossary_entry(
            niche_id=test_niche,
            term="Aragorn",
            term_type="character",
            db_path=test_db
        )
        create_glossary_entry(
            niche_id=test_niche,
            term="Gondor",
            term_type="location",
            db_path=test_db
        )
        create_glossary_entry(
            niche_id=test_niche,
            term="Gandalf",
            term_type="character",
            db_path=test_db
        )

        # Get all entries
        all_entries = get_glossary_by_niche(test_niche, db_path=test_db)
        assert len(all_entries) == 3

        # Filter by character
        characters = get_glossary_by_niche(test_niche, term_type="character", db_path=test_db)
        assert len(characters) == 2
        assert all(e["term_type"] == "character" for e in characters)

        # Filter by location
        locations = get_glossary_by_niche(test_niche, term_type="location", db_path=test_db)
        assert len(locations) == 1
        assert locations[0]["term"] == "Gondor"


class TestSearchGlossaryByTerm:
    """Tests for search_glossary_by_term function."""

    def test_search_glossary_by_term_exact_match(self, test_db, test_niche):
        """Test searching for an exact term match."""
        create_glossary_entry(niche_id=test_niche, term="Gandalf", db_path=test_db)
        create_glossary_entry(niche_id=test_niche, term="Aragorn", db_path=test_db)

        results = search_glossary_by_term(test_niche, "Gandalf", db_path=test_db)

        assert len(results) == 1
        assert results[0]["term"] == "Gandalf"

    def test_search_glossary_by_term_partial_match(self, test_db, test_niche):
        """Test searching for a partial term match."""
        create_glossary_entry(niche_id=test_niche, term="Gandalf", db_path=test_db)
        create_glossary_entry(niche_id=test_niche, term="Galadriel", db_path=test_db)
        create_glossary_entry(niche_id=test_niche, term="Aragorn", db_path=test_db)

        results = search_glossary_by_term(test_niche, "Ga", db_path=test_db)

        assert len(results) == 2
        assert results[0]["term"] == "Galadriel"
        assert results[1]["term"] == "Gandalf"

    def test_search_glossary_by_term_no_match(self, test_db, test_niche):
        """Test searching when no terms match."""
        create_glossary_entry(niche_id=test_niche, term="Gandalf", db_path=test_db)

        results = search_glossary_by_term(test_niche, "Sauron", db_path=test_db)

        assert len(results) == 0

    def test_search_glossary_by_term_case_insensitive(self, test_db, test_niche):
        """Test that search is case-insensitive."""
        create_glossary_entry(niche_id=test_niche, term="Gandalf", db_path=test_db)

        results = search_glossary_by_term(test_niche, "gandalf", db_path=test_db)

        assert len(results) == 1
        assert results[0]["term"] == "Gandalf"


class TestUpdateGlossaryEntry:
    """Tests for update_glossary_entry function."""

    def test_update_glossary_entry_single_field(self, test_db, test_niche):
        """Test updating a single field."""
        entry_id = create_glossary_entry(
            niche_id=test_niche,
            term="Original Term",
            db_path=test_db
        )

        result = update_glossary_entry(entry_id, term="Updated Term", db_path=test_db)

        assert result is True
        entry = get_glossary_entry(entry_id, db_path=test_db)
        assert entry["term"] == "Updated Term"

    def test_update_glossary_entry_multiple_fields(self, test_db, test_niche):
        """Test updating multiple fields."""
        entry_id = create_glossary_entry(
            niche_id=test_niche,
            term="Original",
            db_path=test_db
        )

        result = update_glossary_entry(
            entry_id,
            term="Updated Term",
            term_type="location",
            phonetic_hints="new-hints",
            description="Updated description",
            db_path=test_db
        )

        assert result is True
        entry = get_glossary_entry(entry_id, db_path=test_db)
        assert entry["term"] == "Updated Term"
        assert entry["term_type"] == "location"
        assert entry["phonetic_hints"] == "new-hints"
        assert entry["description"] == "Updated description"

    def test_update_glossary_entry_not_found(self, test_db):
        """Test updating a non-existent glossary entry."""
        result = update_glossary_entry(9999, term="New Term", db_path=test_db)
        assert result is False

    def test_update_glossary_entry_no_fields(self, test_db, test_niche):
        """Test updating with no fields provided."""
        entry_id = create_glossary_entry(
            niche_id=test_niche,
            term="Test",
            db_path=test_db
        )
        result = update_glossary_entry(entry_id, db_path=test_db)
        assert result is False

    def test_update_glossary_entry_invalid_field(self, test_db, test_niche):
        """Test updating with invalid field name."""
        entry_id = create_glossary_entry(
            niche_id=test_niche,
            term="Test",
            db_path=test_db
        )

        with pytest.raises(ValueError) as exc_info:
            update_glossary_entry(entry_id, invalid_field="value", db_path=test_db)

        assert "Invalid fields" in str(exc_info.value)

    def test_update_glossary_entry_invalid_niche(self, test_db, test_niche):
        """Test updating niche_id to non-existent niche."""
        entry_id = create_glossary_entry(
            niche_id=test_niche,
            term="Test",
            db_path=test_db
        )

        with pytest.raises(sqlite3.IntegrityError):
            update_glossary_entry(entry_id, niche_id=9999, db_path=test_db)

    def test_update_glossary_entry_invalid_source(self, test_db, test_niche):
        """Test updating source_id to non-existent source."""
        entry_id = create_glossary_entry(
            niche_id=test_niche,
            term="Test",
            db_path=test_db
        )

        with pytest.raises(sqlite3.IntegrityError):
            update_glossary_entry(entry_id, source_id=9999, db_path=test_db)


class TestDeleteGlossaryEntry:
    """Tests for delete_glossary_entry function."""

    def test_delete_glossary_entry_success(self, test_db, test_niche):
        """Test successfully deleting a glossary entry."""
        entry_id = create_glossary_entry(
            niche_id=test_niche,
            term="To Delete",
            db_path=test_db
        )

        result = delete_glossary_entry(entry_id, db_path=test_db)

        assert result is True
        # Verify it's gone
        entry = get_glossary_entry(entry_id, db_path=test_db)
        assert entry is None

    def test_delete_glossary_entry_not_found(self, test_db):
        """Test deleting a non-existent glossary entry."""
        result = delete_glossary_entry(9999, db_path=test_db)
        assert result is False


class TestIntegration:
    """Integration tests for combined operations."""

    def test_full_crud_lifecycle(self, test_db, test_niche, test_source):
        """Test complete CRUD lifecycle."""
        # Create
        entry_id = create_glossary_entry(
            niche_id=test_niche,
            term="Legolas",
            term_type="character",
            phonetic_hints="leg-oh-las",
            aliases='["Son of Thranduil"]',
            description="Prince of Mirkwood",
            source_id=test_source,
            db_path=test_db
        )
        assert entry_id > 0

        # Read
        entry = get_glossary_entry(entry_id, db_path=test_db)
        assert entry["term"] == "Legolas"
        assert entry["term_type"] == "character"

        # Update
        success = update_glossary_entry(
            entry_id,
            term="Legolas Greenleaf",
            description="Elven archer of the Fellowship",
            db_path=test_db
        )
        assert success is True

        # Verify update
        entry = get_glossary_entry(entry_id, db_path=test_db)
        assert entry["term"] == "Legolas Greenleaf"
        assert entry["description"] == "Elven archer of the Fellowship"

        # Delete
        success = delete_glossary_entry(entry_id, db_path=test_db)
        assert success is True

        # Verify deletion
        entry = get_glossary_entry(entry_id, db_path=test_db)
        assert entry is None

    def test_glossary_with_multiple_term_types(self, test_db, test_niche):
        """Test managing glossary entries with different term types."""
        # Create entries of different types
        create_glossary_entry(
            niche_id=test_niche,
            term="Aragorn",
            term_type="character",
            db_path=test_db
        )
        create_glossary_entry(
            niche_id=test_niche,
            term="Minas Tirith",
            term_type="location",
            db_path=test_db
        )
        create_glossary_entry(
            niche_id=test_niche,
            term="Anduril",
            term_type="item",
            db_path=test_db
        )
        create_glossary_entry(
            niche_id=test_niche,
            term="One Ring",
            term_type="item",
            db_path=test_db
        )

        # Get all entries
        all_entries = get_glossary_by_niche(test_niche, db_path=test_db)
        assert len(all_entries) == 4

        # Filter by type
        characters = get_glossary_by_niche(test_niche, term_type="character", db_path=test_db)
        locations = get_glossary_by_niche(test_niche, term_type="location", db_path=test_db)
        items = get_glossary_by_niche(test_niche, term_type="item", db_path=test_db)

        assert len(characters) == 1
        assert len(locations) == 1
        assert len(items) == 2

    def test_search_across_glossary(self, test_db, test_niche):
        """Test searching across multiple glossary entries."""
        # Create entries
        create_glossary_entry(niche_id=test_niche, term="Gandalf the Grey", db_path=test_db)
        create_glossary_entry(niche_id=test_niche, term="Gandalf the White", db_path=test_db)
        create_glossary_entry(niche_id=test_niche, term="Saruman the White", db_path=test_db)
        create_glossary_entry(niche_id=test_niche, term="Radagast the Brown", db_path=test_db)

        # Search for "Gandalf"
        gandalf_results = search_glossary_by_term(test_niche, "Gandalf", db_path=test_db)
        assert len(gandalf_results) == 2

        # Search for "White"
        white_results = search_glossary_by_term(test_niche, "White", db_path=test_db)
        assert len(white_results) == 2

        # Search for "the"
        the_results = search_glossary_by_term(test_niche, "the", db_path=test_db)
        assert len(the_results) == 4
