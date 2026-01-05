"""
CRUD operations for the canon_sources table.

Manages authoritative source material (books, documents, wikis) for each niche.
"""

import sqlite3
from typing import Optional
from pathlib import Path

from .schema import get_connection


def create_canon_source(
    niche_id: int,
    title: str,
    author: Optional[str] = None,
    source_type: Optional[str] = None,
    file_path: Optional[str] = None,
    url: Optional[str] = None,
    priority: int = 1,
    db_path: Optional[Path] = None
) -> int:
    """
    Create a new canon source.

    Args:
        niche_id: ID of the niche this source belongs to
        title: Title of the source (e.g., "The Silmarillion")
        author: Author name (e.g., "J.R.R. Tolkien")
        source_type: Type of source (e.g., "book", "wiki", "whitepaper", "documentation")
        file_path: Local path to PDF/text file
        url: Web source URL if applicable
        priority: Priority level (higher = more authoritative), default 1
        db_path: Optional database path

    Returns:
        The ID of the newly created canon source

    Raises:
        sqlite3.IntegrityError: If niche_id doesn't exist (foreign key constraint)
        sqlite3.Error: For other database errors
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO canon_sources
            (niche_id, title, author, source_type, file_path, url, priority, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (niche_id, title, author, source_type, file_path, url, priority)
        )
        conn.commit()
        source_id = cursor.lastrowid
        return source_id
    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise sqlite3.IntegrityError(f"Niche with ID {niche_id} does not exist") from e
    except sqlite3.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_canon_source(source_id: int, db_path: Optional[Path] = None) -> Optional[dict]:
    """
    Retrieve a canon source by ID.

    Args:
        source_id: The canon source ID to look up
        db_path: Optional database path

    Returns:
        Dictionary with canon source data, or None if not found
        Keys: id, niche_id, title, author, source_type, file_path, url,
              priority, ingested, ingested_at, created_at
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, niche_id, title, author, source_type, file_path, url,
                   priority, ingested, ingested_at, created_at
            FROM canon_sources
            WHERE id = ?
            """,
            (source_id,)
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return {
            "id": row[0],
            "niche_id": row[1],
            "title": row[2],
            "author": row[3],
            "source_type": row[4],
            "file_path": row[5],
            "url": row[6],
            "priority": row[7],
            "ingested": bool(row[8]),
            "ingested_at": row[9],
            "created_at": row[10]
        }
    finally:
        conn.close()


def get_sources_by_niche(niche_id: int, db_path: Optional[Path] = None) -> list[dict]:
    """
    Retrieve all canon sources for a specific niche.

    Args:
        niche_id: The niche ID to filter by
        db_path: Optional database path

    Returns:
        List of dictionaries, each containing canon source data
        Ordered by priority descending (highest priority first), then by title
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, niche_id, title, author, source_type, file_path, url,
                   priority, ingested, ingested_at, created_at
            FROM canon_sources
            WHERE niche_id = ?
            ORDER BY priority DESC, title ASC
            """,
            (niche_id,)
        )
        rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "niche_id": row[1],
                "title": row[2],
                "author": row[3],
                "source_type": row[4],
                "file_path": row[5],
                "url": row[6],
                "priority": row[7],
                "ingested": bool(row[8]),
                "ingested_at": row[9],
                "created_at": row[10]
            }
            for row in rows
        ]
    finally:
        conn.close()


def update_canon_source(
    source_id: int,
    db_path: Optional[Path] = None,
    **fields
) -> bool:
    """
    Update a canon source's fields.

    Args:
        source_id: The canon source ID to update
        db_path: Optional database path
        **fields: Field names and new values
                 Valid fields: niche_id, title, author, source_type, file_path,
                              url, priority, ingested, ingested_at

    Returns:
        True if the source was updated, False if not found

    Raises:
        ValueError: If invalid field names are provided
        sqlite3.IntegrityError: If niche_id update violates foreign key constraint
        sqlite3.Error: For other database errors

    Example:
        update_canon_source(1, title="New Title", priority=5)
    """
    valid_fields = {
        "niche_id", "title", "author", "source_type", "file_path",
        "url", "priority", "ingested", "ingested_at"
    }
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
        values = list(fields.values()) + [source_id]

        cursor.execute(
            f"UPDATE canon_sources SET {set_clause} WHERE id = ?",
            values
        )
        conn.commit()

        # Check if any row was updated
        return cursor.rowcount > 0

    except sqlite3.IntegrityError as e:
        conn.rollback()
        if "niche_id" in fields:
            raise sqlite3.IntegrityError(
                f"Niche with ID {fields['niche_id']} does not exist"
            ) from e
        raise
    except sqlite3.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_canon_source(source_id: int, db_path: Optional[Path] = None) -> bool:
    """
    Delete a canon source by ID.

    Args:
        source_id: The canon source ID to delete
        db_path: Optional database path

    Returns:
        True if the source was deleted, False if not found

    Raises:
        sqlite3.IntegrityError: If source has related records (foreign key constraint)
        sqlite3.Error: For other database errors

    Note:
        This will fail if the source has related records (glossary entries, etc.)
        due to foreign key constraints.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM canon_sources WHERE id = ?", (source_id,))
        conn.commit()

        # Check if any row was deleted
        return cursor.rowcount > 0

    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise sqlite3.IntegrityError(
            f"Cannot delete canon source {source_id}: has related records"
        ) from e
    except sqlite3.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def mark_as_ingested(source_id: int, db_path: Optional[Path] = None) -> bool:
    """
    Mark a canon source as ingested (processed into the vector database).

    Args:
        source_id: The canon source ID to mark as ingested
        db_path: Optional database path

    Returns:
        True if the source was updated, False if not found

    Raises:
        sqlite3.Error: For database errors
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            UPDATE canon_sources
            SET ingested = TRUE, ingested_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (source_id,)
        )
        conn.commit()

        # Check if any row was updated
        return cursor.rowcount > 0

    except sqlite3.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()
