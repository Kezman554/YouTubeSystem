"""
CRUD operations for the glossary table.

Manages canonical terms per niche (used for transcript cleaning and auto-tagging).
"""

import sqlite3
from typing import Optional
from pathlib import Path

from .schema import get_connection


def create_glossary_entry(
    niche_id: int,
    term: str,
    term_type: Optional[str] = None,
    phonetic_hints: Optional[str] = None,
    aliases: Optional[str] = None,
    description: Optional[str] = None,
    source_id: Optional[int] = None,
    db_path: Optional[Path] = None
) -> int:
    """
    Create a new glossary entry.

    Args:
        niche_id: ID of the niche this term belongs to
        term: The canonical term (e.g., "Boromir")
        term_type: Type of term (e.g., "character", "location", "item", "concept", "brand")
        phonetic_hints: Phonetic variations (e.g., "borrow-meer,bore-oh-mir")
        aliases: JSON string of aliases (e.g., '["Son of Denethor", "Captain of Gondor"]')
        description: Description of the term
        source_id: ID of the canon source this term came from
        db_path: Optional database path

    Returns:
        The ID of the newly created glossary entry

    Raises:
        sqlite3.IntegrityError: If niche_id or source_id don't exist (foreign key constraint)
        sqlite3.Error: For other database errors
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO glossary
            (niche_id, term, term_type, phonetic_hints, aliases, description, source_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (niche_id, term, term_type, phonetic_hints, aliases, description, source_id)
        )
        conn.commit()
        entry_id = cursor.lastrowid
        return entry_id
    except sqlite3.IntegrityError as e:
        conn.rollback()
        error_msg = str(e).lower()
        if "niche" in error_msg:
            raise sqlite3.IntegrityError(f"Niche with ID {niche_id} does not exist") from e
        elif "source" in error_msg:
            raise sqlite3.IntegrityError(f"Canon source with ID {source_id} does not exist") from e
        raise
    except sqlite3.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_glossary_entry(entry_id: int, db_path: Optional[Path] = None) -> Optional[dict]:
    """
    Retrieve a glossary entry by ID.

    Args:
        entry_id: The glossary entry ID to look up
        db_path: Optional database path

    Returns:
        Dictionary with glossary entry data, or None if not found
        Keys: id, niche_id, term, term_type, phonetic_hints, aliases,
              description, source_id, created_at
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, niche_id, term, term_type, phonetic_hints, aliases,
                   description, source_id, created_at
            FROM glossary
            WHERE id = ?
            """,
            (entry_id,)
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return {
            "id": row[0],
            "niche_id": row[1],
            "term": row[2],
            "term_type": row[3],
            "phonetic_hints": row[4],
            "aliases": row[5],
            "description": row[6],
            "source_id": row[7],
            "created_at": row[8]
        }
    finally:
        conn.close()


def get_glossary_by_niche(
    niche_id: int,
    term_type: Optional[str] = None,
    db_path: Optional[Path] = None
) -> list[dict]:
    """
    Retrieve all glossary entries for a specific niche.

    Args:
        niche_id: The niche ID to filter by
        term_type: Optional term type to filter by (e.g., "character", "location")
        db_path: Optional database path

    Returns:
        List of dictionaries, each containing glossary entry data
        Ordered by term alphabetically
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        if term_type:
            cursor.execute(
                """
                SELECT id, niche_id, term, term_type, phonetic_hints, aliases,
                       description, source_id, created_at
                FROM glossary
                WHERE niche_id = ? AND term_type = ?
                ORDER BY term ASC
                """,
                (niche_id, term_type)
            )
        else:
            cursor.execute(
                """
                SELECT id, niche_id, term, term_type, phonetic_hints, aliases,
                       description, source_id, created_at
                FROM glossary
                WHERE niche_id = ?
                ORDER BY term ASC
                """,
                (niche_id,)
            )

        rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "niche_id": row[1],
                "term": row[2],
                "term_type": row[3],
                "phonetic_hints": row[4],
                "aliases": row[5],
                "description": row[6],
                "source_id": row[7],
                "created_at": row[8]
            }
            for row in rows
        ]
    finally:
        conn.close()


def search_glossary_by_term(
    niche_id: int,
    search_term: str,
    db_path: Optional[Path] = None
) -> list[dict]:
    """
    Search for glossary entries by term (case-insensitive partial match).

    Args:
        niche_id: The niche ID to search within
        search_term: The term to search for (partial match)
        db_path: Optional database path

    Returns:
        List of dictionaries containing matching glossary entries
        Ordered by term alphabetically
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, niche_id, term, term_type, phonetic_hints, aliases,
                   description, source_id, created_at
            FROM glossary
            WHERE niche_id = ? AND LOWER(term) LIKE LOWER(?)
            ORDER BY term ASC
            """,
            (niche_id, f"%{search_term}%")
        )
        rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "niche_id": row[1],
                "term": row[2],
                "term_type": row[3],
                "phonetic_hints": row[4],
                "aliases": row[5],
                "description": row[6],
                "source_id": row[7],
                "created_at": row[8]
            }
            for row in rows
        ]
    finally:
        conn.close()


def update_glossary_entry(
    entry_id: int,
    db_path: Optional[Path] = None,
    **fields
) -> bool:
    """
    Update a glossary entry's fields.

    Args:
        entry_id: The glossary entry ID to update
        db_path: Optional database path
        **fields: Field names and new values
                 Valid fields: niche_id, term, term_type, phonetic_hints,
                              aliases, description, source_id

    Returns:
        True if the entry was updated, False if not found

    Raises:
        ValueError: If invalid field names are provided
        sqlite3.IntegrityError: If niche_id or source_id update violates foreign key constraint
        sqlite3.Error: For other database errors

    Example:
        update_glossary_entry(1, term="Updated Term", description="New description")
    """
    valid_fields = {
        "niche_id", "term", "term_type", "phonetic_hints",
        "aliases", "description", "source_id"
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
        values = list(fields.values()) + [entry_id]

        cursor.execute(
            f"UPDATE glossary SET {set_clause} WHERE id = ?",
            values
        )
        conn.commit()

        # Check if any row was updated
        return cursor.rowcount > 0

    except sqlite3.IntegrityError as e:
        conn.rollback()
        error_msg = str(e).lower()
        if "niche" in error_msg and "niche_id" in fields:
            raise sqlite3.IntegrityError(
                f"Niche with ID {fields['niche_id']} does not exist"
            ) from e
        elif "source" in error_msg and "source_id" in fields:
            raise sqlite3.IntegrityError(
                f"Canon source with ID {fields['source_id']} does not exist"
            ) from e
        raise
    except sqlite3.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_glossary_entry(entry_id: int, db_path: Optional[Path] = None) -> bool:
    """
    Delete a glossary entry by ID.

    Args:
        entry_id: The glossary entry ID to delete
        db_path: Optional database path

    Returns:
        True if the entry was deleted, False if not found

    Raises:
        sqlite3.Error: For database errors
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM glossary WHERE id = ?", (entry_id,))
        conn.commit()

        # Check if any row was deleted
        return cursor.rowcount > 0

    except sqlite3.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()
