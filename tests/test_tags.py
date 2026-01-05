"""
Tests for tags CRUD operations.
"""

import pytest
import sqlite3
from pathlib import Path

from src.database.schema import init_db
from src.database.niches import create_niche
from src.database.tags import (
    create_tag,
    get_tag,
    get_tag_by_name,
    get_tags_by_niche,
    get_tags_by_type,
    get_universal_tags,
    update_tag,
    delete_tag
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


class TestCreateTag:
    """Test creating tags."""

    def test_create_tag_with_niche(self, test_db, test_niche):
        """Create a tag associated with a niche."""
        tag_id = create_tag(
            name="gandalf",
            niche_id=test_niche,
            tag_type="character",
            db_path=test_db
        )
        assert tag_id > 0

        # Verify it was created
        tag = get_tag(tag_id, test_db)
        assert tag is not None
        assert tag["name"] == "gandalf"
        assert tag["niche_id"] == test_niche
        assert tag["tag_type"] == "character"

    def test_create_universal_tag(self, test_db):
        """Create a universal tag (NULL niche_id)."""
        tag_id = create_tag(
            name="betrayal",
            tag_type="theme",
            db_path=test_db
        )
        assert tag_id > 0

        # Verify it was created
        tag = get_tag(tag_id, test_db)
        assert tag is not None
        assert tag["name"] == "betrayal"
        assert tag["niche_id"] is None
        assert tag["tag_type"] == "theme"

    def test_create_tag_minimal(self, test_db):
        """Create a tag with only name (no niche, no type)."""
        tag_id = create_tag(
            name="minimal_tag",
            db_path=test_db
        )
        assert tag_id > 0

        # Verify it was created
        tag = get_tag(tag_id, test_db)
        assert tag is not None
        assert tag["name"] == "minimal_tag"
        assert tag["niche_id"] is None
        assert tag["tag_type"] is None

    def test_create_tag_invalid_niche(self, test_db):
        """Creating a tag with invalid niche_id should raise IntegrityError."""
        with pytest.raises(sqlite3.IntegrityError):
            create_tag(
                name="test",
                niche_id=999,
                db_path=test_db
            )

    def test_create_duplicate_tag(self, test_db, test_niche):
        """Creating a duplicate tag should raise IntegrityError."""
        create_tag(
            name="gandalf",
            niche_id=test_niche,
            tag_type="character",
            db_path=test_db
        )

        # Try to create the same tag again
        with pytest.raises(sqlite3.IntegrityError):
            create_tag(
                name="gandalf",
                niche_id=test_niche,
                tag_type="character",
                db_path=test_db
            )

    def test_create_same_name_different_niche(self, test_db):
        """Same tag name can exist in different niches."""
        niche1 = create_niche(name="LOTR", slug="lotr", db_path=test_db)
        niche2 = create_niche(name="History", slug="history", db_path=test_db)

        tag1_id = create_tag(name="magic", niche_id=niche1, db_path=test_db)
        tag2_id = create_tag(name="magic", niche_id=niche2, db_path=test_db)

        assert tag1_id != tag2_id

    def test_create_same_name_different_type(self, test_db, test_niche):
        """Same tag name can exist with different types in same niche."""
        tag1_id = create_tag(
            name="dark",
            niche_id=test_niche,
            tag_type="theme",
            db_path=test_db
        )
        tag2_id = create_tag(
            name="dark",
            niche_id=test_niche,
            tag_type="mood",
            db_path=test_db
        )

        assert tag1_id != tag2_id


class TestGetTag:
    """Test retrieving tags."""

    def test_get_tag_success(self, test_db, test_niche):
        """Get an existing tag."""
        tag_id = create_tag(
            name="gandalf",
            niche_id=test_niche,
            tag_type="character",
            db_path=test_db
        )

        tag = get_tag(tag_id, test_db)
        assert tag is not None
        assert tag["id"] == tag_id
        assert tag["name"] == "gandalf"
        assert tag["niche_id"] == test_niche
        assert tag["tag_type"] == "character"

    def test_get_tag_not_found(self, test_db):
        """Get a non-existent tag should return None."""
        tag = get_tag(999, test_db)
        assert tag is None


class TestGetTagByName:
    """Test retrieving tags by name."""

    def test_get_tag_by_name_success(self, test_db, test_niche):
        """Get a tag by name, niche, and type."""
        tag_id = create_tag(
            name="gandalf",
            niche_id=test_niche,
            tag_type="character",
            db_path=test_db
        )

        tag = get_tag_by_name("gandalf", test_niche, "character", test_db)
        assert tag is not None
        assert tag["id"] == tag_id
        assert tag["name"] == "gandalf"

    def test_get_tag_by_name_universal(self, test_db):
        """Get a universal tag by name."""
        tag_id = create_tag(
            name="betrayal",
            tag_type="theme",
            db_path=test_db
        )

        tag = get_tag_by_name("betrayal", None, "theme", test_db)
        assert tag is not None
        assert tag["id"] == tag_id
        assert tag["niche_id"] is None

    def test_get_tag_by_name_not_found(self, test_db, test_niche):
        """Get a non-existent tag by name should return None."""
        tag = get_tag_by_name("nonexistent", test_niche, "character", test_db)
        assert tag is None


class TestGetTagsByNiche:
    """Test retrieving tags by niche."""

    def test_get_tags_by_niche_empty(self, test_db, test_niche):
        """Get tags for a niche with no tags."""
        tags = get_tags_by_niche(test_niche, test_db)
        assert tags == []

    def test_get_tags_by_niche_multiple(self, test_db, test_niche):
        """Get multiple tags for a niche."""
        id1 = create_tag(name="gandalf", niche_id=test_niche, db_path=test_db)
        id2 = create_tag(name="frodo", niche_id=test_niche, db_path=test_db)
        id3 = create_tag(name="aragorn", niche_id=test_niche, db_path=test_db)

        tags = get_tags_by_niche(test_niche, test_db)
        assert len(tags) == 3
        # Should be ordered by name ASC
        assert tags[0]["name"] == "aragorn"
        assert tags[1]["name"] == "frodo"
        assert tags[2]["name"] == "gandalf"

    def test_get_tags_by_niche_excludes_universal(self, test_db, test_niche):
        """Get tags by niche should not include universal tags."""
        create_tag(name="gandalf", niche_id=test_niche, db_path=test_db)
        create_tag(name="betrayal", db_path=test_db)  # Universal tag

        tags = get_tags_by_niche(test_niche, test_db)
        assert len(tags) == 1
        assert tags[0]["name"] == "gandalf"


class TestGetTagsByType:
    """Test retrieving tags by type."""

    def test_get_tags_by_type_empty(self, test_db):
        """Get tags for a type with no tags."""
        tags = get_tags_by_type("character", db_path=test_db)
        assert tags == []

    def test_get_tags_by_type_multiple(self, test_db, test_niche):
        """Get multiple tags of the same type."""
        create_tag(name="gandalf", niche_id=test_niche, tag_type="character", db_path=test_db)
        create_tag(name="frodo", niche_id=test_niche, tag_type="character", db_path=test_db)
        create_tag(name="shire", niche_id=test_niche, tag_type="location", db_path=test_db)

        characters = get_tags_by_type("character", db_path=test_db)
        assert len(characters) == 2
        assert {characters[0]["name"], characters[1]["name"]} == {"gandalf", "frodo"}

        locations = get_tags_by_type("location", db_path=test_db)
        assert len(locations) == 1
        assert locations[0]["name"] == "shire"

    def test_get_tags_by_type_with_niche_filter(self, test_db):
        """Get tags by type filtered by niche."""
        niche1 = create_niche(name="LOTR", slug="lotr", db_path=test_db)
        niche2 = create_niche(name="History", slug="history", db_path=test_db)

        create_tag(name="gandalf", niche_id=niche1, tag_type="character", db_path=test_db)
        create_tag(name="napoleon", niche_id=niche2, tag_type="character", db_path=test_db)

        # Get characters from niche1 only
        tags = get_tags_by_type("character", niche1, test_db)
        assert len(tags) == 1
        assert tags[0]["name"] == "gandalf"

        # Get characters from niche2 only
        tags = get_tags_by_type("character", niche2, test_db)
        assert len(tags) == 1
        assert tags[0]["name"] == "napoleon"


class TestGetUniversalTags:
    """Test retrieving universal tags."""

    def test_get_universal_tags_empty(self, test_db):
        """Get universal tags when none exist."""
        tags = get_universal_tags(test_db)
        assert tags == []

    def test_get_universal_tags_multiple(self, test_db, test_niche):
        """Get multiple universal tags."""
        create_tag(name="betrayal", tag_type="theme", db_path=test_db)
        create_tag(name="redemption", tag_type="theme", db_path=test_db)
        create_tag(name="gandalf", niche_id=test_niche, db_path=test_db)  # Not universal

        universal = get_universal_tags(test_db)
        assert len(universal) == 2
        assert {universal[0]["name"], universal[1]["name"]} == {"betrayal", "redemption"}


class TestUpdateTag:
    """Test updating tags."""

    def test_update_tag_single_field(self, test_db, test_niche):
        """Update a single field."""
        tag_id = create_tag(
            name="gandalf",
            niche_id=test_niche,
            db_path=test_db
        )

        result = update_tag(tag_id, test_db, tag_type="character")
        assert result is True

        tag = get_tag(tag_id, test_db)
        assert tag["tag_type"] == "character"

    def test_update_tag_multiple_fields(self, test_db, test_niche):
        """Update multiple fields."""
        tag_id = create_tag(
            name="old_name",
            db_path=test_db
        )

        result = update_tag(
            tag_id,
            test_db,
            name="new_name",
            niche_id=test_niche,
            tag_type="character"
        )
        assert result is True

        tag = get_tag(tag_id, test_db)
        assert tag["name"] == "new_name"
        assert tag["niche_id"] == test_niche
        assert tag["tag_type"] == "character"

    def test_update_tag_not_found(self, test_db):
        """Update a non-existent tag should return False."""
        result = update_tag(999, test_db, name="test")
        assert result is False

    def test_update_tag_no_fields(self, test_db, test_niche):
        """Update with no fields should return False."""
        tag_id = create_tag(name="gandalf", niche_id=test_niche, db_path=test_db)

        result = update_tag(tag_id, test_db)
        assert result is False

    def test_update_tag_invalid_field(self, test_db, test_niche):
        """Update with invalid field should raise ValueError."""
        tag_id = create_tag(name="gandalf", niche_id=test_niche, db_path=test_db)

        with pytest.raises(ValueError):
            update_tag(tag_id, test_db, invalid_field="value")

    def test_update_tag_duplicate(self, test_db, test_niche):
        """Update that creates a duplicate should raise IntegrityError."""
        create_tag(
            name="gandalf",
            niche_id=test_niche,
            tag_type="character",
            db_path=test_db
        )
        tag2_id = create_tag(
            name="frodo",
            niche_id=test_niche,
            tag_type="character",
            db_path=test_db
        )

        # Try to rename frodo to gandalf
        with pytest.raises(sqlite3.IntegrityError):
            update_tag(tag2_id, test_db, name="gandalf")

    def test_update_tag_invalid_niche(self, test_db, test_niche):
        """Update with invalid niche_id should raise IntegrityError."""
        tag_id = create_tag(name="gandalf", niche_id=test_niche, db_path=test_db)

        with pytest.raises(sqlite3.IntegrityError):
            update_tag(tag_id, test_db, niche_id=999)


class TestDeleteTag:
    """Test deleting tags."""

    def test_delete_tag_success(self, test_db, test_niche):
        """Delete an existing tag."""
        tag_id = create_tag(
            name="gandalf",
            niche_id=test_niche,
            db_path=test_db
        )

        result = delete_tag(tag_id, test_db)
        assert result is True

        # Verify it's gone
        tag = get_tag(tag_id, test_db)
        assert tag is None

    def test_delete_tag_not_found(self, test_db):
        """Delete a non-existent tag should return False."""
        result = delete_tag(999, test_db)
        assert result is False


class TestIntegration:
    """Integration tests for complex scenarios."""

    def test_niche_specific_vs_universal_tags(self, test_db):
        """Test mixing niche-specific and universal tags."""
        niche1 = create_niche(name="LOTR", slug="lotr", db_path=test_db)
        niche2 = create_niche(name="History", slug="history", db_path=test_db)

        # Create niche-specific tags
        create_tag(name="gandalf", niche_id=niche1, tag_type="character", db_path=test_db)
        create_tag(name="napoleon", niche_id=niche2, tag_type="character", db_path=test_db)

        # Create universal tags
        create_tag(name="betrayal", tag_type="theme", db_path=test_db)
        create_tag(name="redemption", tag_type="theme", db_path=test_db)

        # Verify separation
        niche1_tags = get_tags_by_niche(niche1, test_db)
        assert len(niche1_tags) == 1
        assert niche1_tags[0]["name"] == "gandalf"

        universal_tags = get_universal_tags(test_db)
        assert len(universal_tags) == 2
        assert {t["name"] for t in universal_tags} == {"betrayal", "redemption"}

        # Verify by type across all niches
        all_characters = get_tags_by_type("character", db_path=test_db)
        assert len(all_characters) == 2
        assert {t["name"] for t in all_characters} == {"gandalf", "napoleon"}

    def test_tag_types_organization(self, test_db, test_niche):
        """Test organizing tags by different types."""
        # Create tags of different types
        create_tag(name="gandalf", niche_id=test_niche, tag_type="character", db_path=test_db)
        create_tag(name="frodo", niche_id=test_niche, tag_type="character", db_path=test_db)
        create_tag(name="first_age", niche_id=test_niche, tag_type="era", db_path=test_db)
        create_tag(name="third_age", niche_id=test_niche, tag_type="era", db_path=test_db)
        create_tag(name="shire", niche_id=test_niche, tag_type="location", db_path=test_db)

        # Get by type
        characters = get_tags_by_type("character", db_path=test_db)
        eras = get_tags_by_type("era", db_path=test_db)
        locations = get_tags_by_type("location", db_path=test_db)

        assert len(characters) == 2
        assert len(eras) == 2
        assert len(locations) == 1

        # All should be in niche
        all_niche_tags = get_tags_by_niche(test_niche, test_db)
        assert len(all_niche_tags) == 5

    def test_update_tag_from_niche_to_universal(self, test_db, test_niche):
        """Test converting a niche-specific tag to universal."""
        tag_id = create_tag(
            name="betrayal",
            niche_id=test_niche,
            tag_type="theme",
            db_path=test_db
        )

        # Initially in niche
        niche_tags = get_tags_by_niche(test_niche, test_db)
        assert len(niche_tags) == 1

        universal_tags = get_universal_tags(test_db)
        assert len(universal_tags) == 0

        # Convert to universal by setting niche_id to None
        update_tag(tag_id, test_db, niche_id=None)

        # Now should be universal
        niche_tags = get_tags_by_niche(test_niche, test_db)
        assert len(niche_tags) == 0

        universal_tags = get_universal_tags(test_db)
        assert len(universal_tags) == 1
        assert universal_tags[0]["name"] == "betrayal"
