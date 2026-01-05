"""
CRUD operations for the my_channels table.

Manages user's own YouTube channels.
"""

import sqlite3
from typing import Optional
from pathlib import Path

from .schema import get_connection


def create_my_channel(
    niche_id: int,
    name: str,
    youtube_id: Optional[str] = None,
    url: Optional[str] = None,
    subscriber_count: int = 0,
    db_path: Optional[Path] = None
) -> int:
    """
    Create a new channel for the user.

    Args:
        niche_id: ID of the niche this channel belongs to
        name: Channel name
        youtube_id: YouTube channel ID (optional, NULL until channel is created)
        url: Channel URL
        subscriber_count: Number of subscribers (default 0)
        db_path: Optional database path

    Returns:
        The ID of the newly created channel

    Raises:
        sqlite3.IntegrityError: If niche_id doesn't exist or youtube_id is duplicate
        sqlite3.Error: For other database errors
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO my_channels
            (niche_id, youtube_id, name, url, subscriber_count, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (niche_id, youtube_id, name, url, subscriber_count)
        )
        conn.commit()
        channel_id = cursor.lastrowid
        return channel_id
    except sqlite3.IntegrityError as e:
        conn.rollback()
        error_msg = str(e).lower()
        if youtube_id and ("youtube_id" in error_msg or "unique" in error_msg):
            raise sqlite3.IntegrityError(f"Channel with YouTube ID '{youtube_id}' already exists") from e
        elif "niche" in error_msg:
            raise sqlite3.IntegrityError(f"Niche with ID {niche_id} does not exist") from e
        raise
    except sqlite3.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_my_channel(channel_id: int, db_path: Optional[Path] = None) -> Optional[dict]:
    """
    Retrieve a channel by ID.

    Args:
        channel_id: The channel ID to look up
        db_path: Optional database path

    Returns:
        Dictionary with channel data, or None if not found
        Keys: id, niche_id, youtube_id, name, url, subscriber_count, created_at, updated_at
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, niche_id, youtube_id, name, url, subscriber_count, created_at, updated_at
            FROM my_channels
            WHERE id = ?
            """,
            (channel_id,)
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return {
            "id": row[0],
            "niche_id": row[1],
            "youtube_id": row[2],
            "name": row[3],
            "url": row[4],
            "subscriber_count": row[5],
            "created_at": row[6],
            "updated_at": row[7]
        }
    finally:
        conn.close()


def get_my_channel_by_youtube_id(
    youtube_id: str,
    db_path: Optional[Path] = None
) -> Optional[dict]:
    """
    Retrieve a channel by YouTube ID.

    Args:
        youtube_id: The YouTube channel ID to look up
        db_path: Optional database path

    Returns:
        Dictionary with channel data, or None if not found
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, niche_id, youtube_id, name, url, subscriber_count, created_at, updated_at
            FROM my_channels
            WHERE youtube_id = ?
            """,
            (youtube_id,)
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return {
            "id": row[0],
            "niche_id": row[1],
            "youtube_id": row[2],
            "name": row[3],
            "url": row[4],
            "subscriber_count": row[5],
            "created_at": row[6],
            "updated_at": row[7]
        }
    finally:
        conn.close()


def get_channels_by_niche(
    niche_id: int,
    db_path: Optional[Path] = None
) -> list[dict]:
    """
    Retrieve all channels for a specific niche.

    Args:
        niche_id: The niche ID to filter by
        db_path: Optional database path

    Returns:
        List of dictionaries, each containing channel data
        Ordered by created_at descending (newest first)
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, niche_id, youtube_id, name, url, subscriber_count, created_at, updated_at
            FROM my_channels
            WHERE niche_id = ?
            ORDER BY created_at DESC
            """,
            (niche_id,)
        )
        rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "niche_id": row[1],
                "youtube_id": row[2],
                "name": row[3],
                "url": row[4],
                "subscriber_count": row[5],
                "created_at": row[6],
                "updated_at": row[7]
            }
            for row in rows
        ]
    finally:
        conn.close()


def get_all_my_channels(db_path: Optional[Path] = None) -> list[dict]:
    """
    Retrieve all user channels.

    Args:
        db_path: Optional database path

    Returns:
        List of dictionaries, each containing channel data
        Ordered by created_at descending (newest first)
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, niche_id, youtube_id, name, url, subscriber_count, created_at, updated_at
            FROM my_channels
            ORDER BY created_at DESC
            """
        )
        rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "niche_id": row[1],
                "youtube_id": row[2],
                "name": row[3],
                "url": row[4],
                "subscriber_count": row[5],
                "created_at": row[6],
                "updated_at": row[7]
            }
            for row in rows
        ]
    finally:
        conn.close()


def update_my_channel(
    channel_id: int,
    db_path: Optional[Path] = None,
    **fields
) -> bool:
    """
    Update a channel's fields.

    Args:
        channel_id: The channel ID to update
        db_path: Optional database path
        **fields: Field names and new values
                 Valid fields: niche_id, youtube_id, name, url, subscriber_count

    Returns:
        True if the channel was updated, False if not found

    Raises:
        ValueError: If invalid field names are provided
        sqlite3.IntegrityError: If niche_id or youtube_id update violates constraints
        sqlite3.Error: For other database errors

    Example:
        update_my_channel(1, name="Updated Name", subscriber_count=1000)
    """
    valid_fields = {"niche_id", "youtube_id", "name", "url", "subscriber_count"}
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
        values = list(fields.values()) + [channel_id]

        cursor.execute(
            f"UPDATE my_channels SET {set_clause} WHERE id = ?",
            values
        )
        conn.commit()

        # Check if any row was updated
        return cursor.rowcount > 0

    except sqlite3.IntegrityError as e:
        conn.rollback()
        error_msg = str(e).lower()
        if "youtube_id" in fields and ("youtube_id" in error_msg or "unique" in error_msg):
            raise sqlite3.IntegrityError(
                f"Channel with YouTube ID '{fields['youtube_id']}' already exists"
            ) from e
        elif "niche_id" in fields and "niche" in error_msg:
            raise sqlite3.IntegrityError(f"Niche with ID {fields['niche_id']} does not exist") from e
        raise
    except sqlite3.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_my_channel(channel_id: int, db_path: Optional[Path] = None) -> bool:
    """
    Delete a channel by ID.

    Args:
        channel_id: The channel ID to delete
        db_path: Optional database path

    Returns:
        True if the channel was deleted, False if not found

    Raises:
        sqlite3.IntegrityError: If channel has related records (foreign key constraint)
        sqlite3.Error: For other database errors

    Note:
        This will fail if the channel has related records (my_videos, etc.)
        due to foreign key constraints.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM my_channels WHERE id = ?", (channel_id,))
        conn.commit()

        # Check if any row was deleted
        return cursor.rowcount > 0

    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise sqlite3.IntegrityError(
            f"Cannot delete channel {channel_id}: has related records"
        ) from e
    except sqlite3.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_subscriber_count(
    channel_id: int,
    subscriber_count: int,
    db_path: Optional[Path] = None
) -> bool:
    """
    Update a channel's subscriber count.

    Convenience function for updating just the subscriber count.

    Args:
        channel_id: The channel ID to update
        subscriber_count: New subscriber count
        db_path: Optional database path

    Returns:
        True if the channel was updated, False if not found

    Raises:
        sqlite3.Error: For database errors
    """
    return update_my_channel(channel_id, subscriber_count=subscriber_count, db_path=db_path)
