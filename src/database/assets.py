"""
CRUD operations for the assets table.

Manages generated or collected images, videos, and audio.
"""

import sqlite3
from typing import Optional
from pathlib import Path

from .schema import get_connection


def create_asset(
    niche_id: int,
    file_path: str,
    file_type: Optional[str] = None,
    source: Optional[str] = None,
    prompt: Optional[str] = None,
    description: Optional[str] = None,
    subject_tags: Optional[str] = None,
    mood_tags: Optional[str] = None,
    style_tags: Optional[str] = None,
    db_path: Optional[Path] = None
) -> int:
    """
    Create a new asset.

    Args:
        niche_id: ID of the niche this asset belongs to
        file_path: Local path to the asset file
        file_type: Type of file ("image", "video", "audio")
        source: Source of the asset ("stable_diffusion", "midjourney", "leonardo", "stock")
        prompt: Generation prompt if AI-created
        description: Description of what this depicts
        subject_tags: JSON array of subject tags (e.g., '["gandalf", "staff"]')
        mood_tags: JSON array of mood tags (e.g., '["dramatic", "dark"]')
        style_tags: JSON array of style tags (e.g., '["painted", "cinematic"]')
        db_path: Optional database path

    Returns:
        The ID of the newly created asset

    Raises:
        sqlite3.IntegrityError: If niche_id doesn't exist
        sqlite3.Error: For other database errors
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO assets
            (niche_id, file_path, file_type, source, prompt, description,
             subject_tags, mood_tags, style_tags, times_used, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, CURRENT_TIMESTAMP)
            """,
            (niche_id, file_path, file_type, source, prompt, description,
             subject_tags, mood_tags, style_tags)
        )
        conn.commit()
        asset_id = cursor.lastrowid
        return asset_id
    except sqlite3.IntegrityError as e:
        conn.rollback()
        error_msg = str(e).lower()
        if "niche" in error_msg:
            raise sqlite3.IntegrityError(f"Niche with ID {niche_id} does not exist") from e
        raise
    except sqlite3.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_asset(asset_id: int, db_path: Optional[Path] = None) -> Optional[dict]:
    """
    Retrieve an asset by ID.

    Args:
        asset_id: The asset ID to look up
        db_path: Optional database path

    Returns:
        Dictionary with asset data, or None if not found
        Keys: id, niche_id, file_path, file_type, source, prompt, description,
              subject_tags, mood_tags, style_tags, times_used, last_used_in,
              last_used_at, created_at
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, niche_id, file_path, file_type, source, prompt, description,
                   subject_tags, mood_tags, style_tags, times_used, last_used_in,
                   last_used_at, created_at
            FROM assets
            WHERE id = ?
            """,
            (asset_id,)
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return {
            "id": row[0],
            "niche_id": row[1],
            "file_path": row[2],
            "file_type": row[3],
            "source": row[4],
            "prompt": row[5],
            "description": row[6],
            "subject_tags": row[7],
            "mood_tags": row[8],
            "style_tags": row[9],
            "times_used": row[10],
            "last_used_in": row[11],
            "last_used_at": row[12],
            "created_at": row[13]
        }
    finally:
        conn.close()


def get_assets_by_niche(
    niche_id: int,
    db_path: Optional[Path] = None
) -> list[dict]:
    """
    Retrieve all assets for a specific niche.

    Args:
        niche_id: The niche ID to filter by
        db_path: Optional database path

    Returns:
        List of dictionaries, each containing asset data
        Ordered by created_at descending (newest first)
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, niche_id, file_path, file_type, source, prompt, description,
                   subject_tags, mood_tags, style_tags, times_used, last_used_in,
                   last_used_at, created_at
            FROM assets
            WHERE niche_id = ?
            ORDER BY created_at DESC
            """,
            (niche_id,)
        )
        rows = cursor.fetchall()

        return _rows_to_dicts(rows)
    finally:
        conn.close()


def get_assets_by_type(
    file_type: str,
    db_path: Optional[Path] = None
) -> list[dict]:
    """
    Retrieve all assets of a specific file type.

    Args:
        file_type: The file type to filter by ("image", "video", "audio")
        db_path: Optional database path

    Returns:
        List of dictionaries, each containing asset data
        Ordered by created_at descending (newest first)
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, niche_id, file_path, file_type, source, prompt, description,
                   subject_tags, mood_tags, style_tags, times_used, last_used_in,
                   last_used_at, created_at
            FROM assets
            WHERE file_type = ?
            ORDER BY created_at DESC
            """,
            (file_type,)
        )
        rows = cursor.fetchall()

        return _rows_to_dicts(rows)
    finally:
        conn.close()


def get_assets_by_source(
    source: str,
    db_path: Optional[Path] = None
) -> list[dict]:
    """
    Retrieve all assets from a specific source.

    Args:
        source: The source to filter by ("stable_diffusion", "midjourney", "leonardo", "stock")
        db_path: Optional database path

    Returns:
        List of dictionaries, each containing asset data
        Ordered by created_at descending (newest first)
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, niche_id, file_path, file_type, source, prompt, description,
                   subject_tags, mood_tags, style_tags, times_used, last_used_in,
                   last_used_at, created_at
            FROM assets
            WHERE source = ?
            ORDER BY created_at DESC
            """,
            (source,)
        )
        rows = cursor.fetchall()

        return _rows_to_dicts(rows)
    finally:
        conn.close()


def update_asset(
    asset_id: int,
    db_path: Optional[Path] = None,
    **fields
) -> bool:
    """
    Update an asset's fields.

    Args:
        asset_id: The asset ID to update
        db_path: Optional database path
        **fields: Field names and new values
                 Valid fields: niche_id, file_path, file_type, source, prompt,
                              description, subject_tags, mood_tags, style_tags

    Returns:
        True if the asset was updated, False if not found

    Raises:
        ValueError: If invalid field names are provided
        sqlite3.IntegrityError: If niche_id update violates constraints
        sqlite3.Error: For other database errors

    Example:
        update_asset(1, description="Updated description", file_type="image")
    """
    valid_fields = {
        "niche_id", "file_path", "file_type", "source", "prompt",
        "description", "subject_tags", "mood_tags", "style_tags"
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
        values = list(fields.values()) + [asset_id]

        cursor.execute(
            f"UPDATE assets SET {set_clause} WHERE id = ?",
            values
        )
        conn.commit()

        # Check if any row was updated
        return cursor.rowcount > 0

    except sqlite3.IntegrityError as e:
        conn.rollback()
        error_msg = str(e).lower()
        if "niche_id" in fields and "niche" in error_msg:
            raise sqlite3.IntegrityError(f"Niche with ID {fields['niche_id']} does not exist") from e
        raise
    except sqlite3.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_asset(asset_id: int, db_path: Optional[Path] = None) -> bool:
    """
    Delete an asset by ID.

    Args:
        asset_id: The asset ID to delete
        db_path: Optional database path

    Returns:
        True if the asset was deleted, False if not found

    Raises:
        sqlite3.IntegrityError: If asset has related records (foreign key constraint)
        sqlite3.Error: For other database errors

    Note:
        This will fail if the asset has related records (asset_usage, etc.)
        due to foreign key constraints.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM assets WHERE id = ?", (asset_id,))
        conn.commit()

        # Check if any row was deleted
        return cursor.rowcount > 0

    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise sqlite3.IntegrityError(
            f"Cannot delete asset {asset_id}: has related records"
        ) from e
    except sqlite3.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def record_usage(
    asset_id: int,
    video_id: int,
    db_path: Optional[Path] = None
) -> bool:
    """
    Record usage of an asset in a video.

    Updates times_used, last_used_in, and last_used_at fields.

    Args:
        asset_id: The asset ID that was used
        video_id: The video ID where the asset was used
        db_path: Optional database path

    Returns:
        True if the asset was updated, False if not found

    Raises:
        sqlite3.IntegrityError: If video_id doesn't exist
        sqlite3.Error: For other database errors
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            UPDATE assets
            SET times_used = times_used + 1,
                last_used_in = ?,
                last_used_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (video_id, asset_id)
        )
        conn.commit()

        # Check if any row was updated
        return cursor.rowcount > 0

    except sqlite3.IntegrityError as e:
        conn.rollback()
        error_msg = str(e).lower()
        if "video" in error_msg or "my_videos" in error_msg:
            raise sqlite3.IntegrityError(f"Video with ID {video_id} does not exist") from e
        raise
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
            "file_path": row[2],
            "file_type": row[3],
            "source": row[4],
            "prompt": row[5],
            "description": row[6],
            "subject_tags": row[7],
            "mood_tags": row[8],
            "style_tags": row[9],
            "times_used": row[10],
            "last_used_in": row[11],
            "last_used_at": row[12],
            "created_at": row[13]
        }
        for row in rows
    ]
