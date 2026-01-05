"""
CRUD operations for the tags table.

Manages flexible tagging system across niches.
"""

import sqlite3
from typing import Optional
from pathlib import Path

from .schema import get_connection


def create_tag(
    name: str,
    niche_id: Optional[int] = None,
    tag_type: Optional[str] = None,
    db_path: Optional[Path] = None
) -> int:
    """
    Create a new tag.

    Args:
        name: Tag name (e.g., "morgoth", "first_age", "betrayal")
        niche_id: ID of the niche this tag belongs to (NULL for universal tags)
        tag_type: Type of tag ("character", "era", "location", "theme", "mood")
        db_path: Optional database path

    Returns:
        The ID of the newly created tag

    Raises:
        sqlite3.IntegrityError: If niche_id doesn't exist or tag already exists
        sqlite3.Error: For other database errors

    Note:
        Tags have a UNIQUE constraint on (niche_id, name, tag_type).
        Creating a duplicate will raise IntegrityError.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO tags
            (niche_id, name, tag_type, created_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (niche_id, name, tag_type)
        )
        conn.commit()
        tag_id = cursor.lastrowid
        return tag_id
    except sqlite3.IntegrityError as e:
        conn.rollback()
        error_msg = str(e).lower()
        if "unique" in error_msg:
            raise sqlite3.IntegrityError(
                f"Tag '{name}' (type: {tag_type}, niche: {niche_id}) already exists"
            ) from e
        elif "niche" in error_msg:
            raise sqlite3.IntegrityError(f"Niche with ID {niche_id} does not exist") from e
        raise
    except sqlite3.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_tag(tag_id: int, db_path: Optional[Path] = None) -> Optional[dict]:
    """
    Retrieve a tag by ID.

    Args:
        tag_id: The tag ID to look up
        db_path: Optional database path

    Returns:
        Dictionary with tag data, or None if not found
        Keys: id, niche_id, name, tag_type, created_at
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, niche_id, name, tag_type, created_at
            FROM tags
            WHERE id = ?
            """,
            (tag_id,)
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return {
            "id": row[0],
            "niche_id": row[1],
            "name": row[2],
            "tag_type": row[3],
            "created_at": row[4]
        }
    finally:
        conn.close()


def get_tag_by_name(
    name: str,
    niche_id: Optional[int] = None,
    tag_type: Optional[str] = None,
    db_path: Optional[Path] = None
) -> Optional[dict]:
    """
    Retrieve a tag by name, niche, and type.

    Args:
        name: Tag name to look up
        niche_id: Niche ID (NULL for universal tags)
        tag_type: Tag type to match
        db_path: Optional database path

    Returns:
        Dictionary with tag data, or None if not found
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, niche_id, name, tag_type, created_at
            FROM tags
            WHERE name = ? AND niche_id IS ? AND tag_type IS ?
            """,
            (name, niche_id, tag_type)
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return {
            "id": row[0],
            "niche_id": row[1],
            "name": row[2],
            "tag_type": row[3],
            "created_at": row[4]
        }
    finally:
        conn.close()


def get_tags_by_niche(
    niche_id: int,
    db_path: Optional[Path] = None
) -> list[dict]:
    """
    Retrieve all tags for a specific niche.

    Args:
        niche_id: The niche ID to filter by
        db_path: Optional database path

    Returns:
        List of dictionaries, each containing tag data
        Ordered by name ascending
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, niche_id, name, tag_type, created_at
            FROM tags
            WHERE niche_id = ?
            ORDER BY name ASC
            """,
            (niche_id,)
        )
        rows = cursor.fetchall()

        return _rows_to_dicts(rows)
    finally:
        conn.close()


def get_tags_by_type(
    tag_type: str,
    niche_id: Optional[int] = None,
    db_path: Optional[Path] = None
) -> list[dict]:
    """
    Retrieve all tags of a specific type.

    Args:
        tag_type: The tag type to filter by ("character", "era", "location", "theme", "mood")
        niche_id: Optional niche ID to further filter by
        db_path: Optional database path

    Returns:
        List of dictionaries, each containing tag data
        Ordered by name ascending
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        if niche_id is not None:
            cursor.execute(
                """
                SELECT id, niche_id, name, tag_type, created_at
                FROM tags
                WHERE tag_type = ? AND niche_id = ?
                ORDER BY name ASC
                """,
                (tag_type, niche_id)
            )
        else:
            cursor.execute(
                """
                SELECT id, niche_id, name, tag_type, created_at
                FROM tags
                WHERE tag_type = ?
                ORDER BY name ASC
                """,
                (tag_type,)
            )
        rows = cursor.fetchall()

        return _rows_to_dicts(rows)
    finally:
        conn.close()


def get_universal_tags(db_path: Optional[Path] = None) -> list[dict]:
    """
    Retrieve all universal tags (tags with NULL niche_id).

    Args:
        db_path: Optional database path

    Returns:
        List of dictionaries, each containing tag data
        Ordered by name ascending
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, niche_id, name, tag_type, created_at
            FROM tags
            WHERE niche_id IS NULL
            ORDER BY name ASC
            """
        )
        rows = cursor.fetchall()

        return _rows_to_dicts(rows)
    finally:
        conn.close()


def update_tag(
    tag_id: int,
    db_path: Optional[Path] = None,
    **fields
) -> bool:
    """
    Update a tag's fields.

    Args:
        tag_id: The tag ID to update
        db_path: Optional database path
        **fields: Field names and new values
                 Valid fields: niche_id, name, tag_type

    Returns:
        True if the tag was updated, False if not found

    Raises:
        ValueError: If invalid field names are provided
        sqlite3.IntegrityError: If update violates UNIQUE constraint or niche_id constraint
        sqlite3.Error: For other database errors

    Example:
        update_tag(1, name="Updated Name", tag_type="character")
    """
    valid_fields = {"niche_id", "name", "tag_type"}
    provided_fields = set(fields.keys())

    # Validate field names
    invalid_fields = provided_fields - valid_fields
    if invalid_fields:
        raise ValueError(f"Invalid fields: {invalid_fields}. Valid fields: {valid_fields}")

    if not fields:
        return False

    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        # Build UPDATE query dynamically
        set_clause = ", ".join([f"{field} = ?" for field in fields.keys()])
        values = list(fields.values()) + [tag_id]

        cursor.execute(
            f"UPDATE tags SET {set_clause} WHERE id = ?",
            values
        )
        conn.commit()

        # Check if any row was updated
        return cursor.rowcount > 0

    except sqlite3.IntegrityError as e:
        conn.rollback()
        error_msg = str(e).lower()
        if "unique" in error_msg:
            raise sqlite3.IntegrityError(
                f"Tag with name '{fields.get('name')}' (type: {fields.get('tag_type')}) already exists"
            ) from e
        elif "niche" in error_msg:
            raise sqlite3.IntegrityError(f"Niche with ID {fields.get('niche_id')} does not exist") from e
        raise
    except sqlite3.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_tag(tag_id: int, db_path: Optional[Path] = None) -> bool:
    """
    Delete a tag by ID.

    Args:
        tag_id: The tag ID to delete
        db_path: Optional database path

    Returns:
        True if the tag was deleted, False if not found

    Raises:
        sqlite3.IntegrityError: If tag has related records (foreign key constraint)
        sqlite3.Error: For other database errors

    Note:
        This will fail if the tag has related records (video_tags, etc.)
        due to foreign key constraints.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
        conn.commit()

        # Check if any row was deleted
        return cursor.rowcount > 0

    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise sqlite3.IntegrityError(
            f"Cannot delete tag {tag_id}: has related records"
        ) from e
    except sqlite3.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def _rows_to_dicts(rows: list) -> list[dict]:
    """Convert database rows to dictionaries."""
    return [
        {
            "id": row[0],
            "niche_id": row[1],
            "name": row[2],
            "tag_type": row[3],
            "created_at": row[4]
        }
        for row in rows
    ]
