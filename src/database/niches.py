"""
CRUD operations for the niches table.

Manages top-level content areas (e.g., "Middle-earth", "ICP Ecosystem").
"""

import sqlite3
from datetime import datetime
from typing import Optional
from pathlib import Path

from .schema import get_connection


def create_niche(
    name: str,
    slug: str,
    niche_type: Optional[str] = None,
    description: Optional[str] = None,
    db_path: Optional[Path] = None
) -> int:
    """
    Create a new niche.

    Args:
        name: Display name (e.g., "Middle-earth")
        slug: URL-safe identifier (e.g., "middle-earth")
        niche_type: Category (e.g., "fiction", "crypto", "food")
        description: Optional description of the niche

    Returns:
        The ID of the newly created niche

    Raises:
        sqlite3.IntegrityError: If slug already exists
        sqlite3.Error: For other database errors
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO niches (name, slug, type, description, created_at, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (name, slug, niche_type, description)
        )
        conn.commit()
        niche_id = cursor.lastrowid
        return niche_id
    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise sqlite3.IntegrityError(f"Niche with slug '{slug}' already exists") from e
    except sqlite3.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_niche(niche_id: int, db_path: Optional[Path] = None) -> Optional[dict]:
    """
    Retrieve a niche by ID.

    Args:
        niche_id: The niche ID to look up

    Returns:
        Dictionary with niche data, or None if not found
        Keys: id, name, slug, type, description, created_at, updated_at
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, name, slug, type, description, created_at, updated_at
            FROM niches
            WHERE id = ?
            """,
            (niche_id,)
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return {
            "id": row[0],
            "name": row[1],
            "slug": row[2],
            "type": row[3],
            "description": row[4],
            "created_at": row[5],
            "updated_at": row[6]
        }
    finally:
        conn.close()


def get_all_niches(db_path: Optional[Path] = None) -> list[dict]:
    """
    Retrieve all niches.

    Returns:
        List of dictionaries, each containing niche data
        Ordered by created_at descending (newest first)
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, name, slug, type, description, created_at, updated_at
            FROM niches
            ORDER BY created_at DESC
            """
        )
        rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "name": row[1],
                "slug": row[2],
                "type": row[3],
                "description": row[4],
                "created_at": row[5],
                "updated_at": row[6]
            }
            for row in rows
        ]
    finally:
        conn.close()


def update_niche(
    niche_id: int,
    db_path: Optional[Path] = None,
    **fields
) -> bool:
    """
    Update a niche's fields.

    Args:
        niche_id: The niche ID to update
        **fields: Field names and new values
                 Valid fields: name, slug, type, description

    Returns:
        True if the niche was updated, False if not found

    Raises:
        ValueError: If invalid field names are provided
        sqlite3.IntegrityError: If slug update violates uniqueness
        sqlite3.Error: For other database errors

    Example:
        update_niche(1, name="New Name", description="New description")
    """
    valid_fields = {"name", "slug", "type", "description"}
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
        set_clause += ", updated_at = CURRENT_TIMESTAMP"
        values = list(fields.values()) + [niche_id]

        cursor.execute(
            f"UPDATE niches SET {set_clause} WHERE id = ?",
            values
        )
        conn.commit()

        # Check if any row was updated
        return cursor.rowcount > 0

    except sqlite3.IntegrityError as e:
        conn.rollback()
        if "slug" in fields:
            raise sqlite3.IntegrityError(f"Niche with slug '{fields['slug']}' already exists") from e
        raise
    except sqlite3.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_niche(niche_id: int, db_path: Optional[Path] = None) -> bool:
    """
    Delete a niche by ID.

    Args:
        niche_id: The niche ID to delete

    Returns:
        True if the niche was deleted, False if not found

    Raises:
        sqlite3.IntegrityError: If niche has related records (foreign key constraint)
        sqlite3.Error: For other database errors

    Note:
        This will fail if the niche has related records (channels, sources, etc.)
        due to foreign key constraints.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM niches WHERE id = ?", (niche_id,))
        conn.commit()

        # Check if any row was deleted
        return cursor.rowcount > 0

    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise sqlite3.IntegrityError(
            f"Cannot delete niche {niche_id}: has related records"
        ) from e
    except sqlite3.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()
