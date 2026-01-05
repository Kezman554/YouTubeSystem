"""
CRUD operations for the competitor_channels table.

Manages channels being tracked in each niche.
"""

import sqlite3
from typing import Optional
from pathlib import Path

from .schema import get_connection


def create_competitor_channel(
    niche_id: int,
    youtube_id: str,
    name: str,
    url: Optional[str] = None,
    subscriber_count: Optional[int] = None,
    video_count: Optional[int] = None,
    style: Optional[str] = None,
    quality_tier: Optional[str] = None,
    notes: Optional[str] = None,
    is_active: bool = True,
    db_path: Optional[Path] = None
) -> int:
    """
    Create a new competitor channel.

    Args:
        niche_id: ID of the niche this channel belongs to
        youtube_id: YouTube channel ID (must be unique)
        name: Channel name (e.g., "Nerd of the Rings")
        url: Channel URL
        subscriber_count: Number of subscribers
        video_count: Number of videos
        style: Channel style (e.g., "AI voiceover", "real person", "documentary")
        quality_tier: Quality classification (e.g., "top", "mid", "small")
        notes: Additional notes
        is_active: Whether the channel is actively tracked (default True)
        db_path: Optional database path

    Returns:
        The ID of the newly created competitor channel

    Raises:
        sqlite3.IntegrityError: If niche_id doesn't exist or youtube_id is duplicate
        sqlite3.Error: For other database errors
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO competitor_channels
            (niche_id, youtube_id, name, url, subscriber_count, video_count,
             style, quality_tier, notes, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (niche_id, youtube_id, name, url, subscriber_count, video_count,
             style, quality_tier, notes, is_active)
        )
        conn.commit()
        channel_id = cursor.lastrowid
        return channel_id
    except sqlite3.IntegrityError as e:
        conn.rollback()
        error_msg = str(e).lower()
        if "youtube_id" in error_msg or "unique" in error_msg:
            raise sqlite3.IntegrityError(f"Channel with YouTube ID '{youtube_id}' already exists") from e
        elif "niche" in error_msg:
            raise sqlite3.IntegrityError(f"Niche with ID {niche_id} does not exist") from e
        raise
    except sqlite3.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_competitor_channel(channel_id: int, db_path: Optional[Path] = None) -> Optional[dict]:
    """
    Retrieve a competitor channel by ID.

    Args:
        channel_id: The competitor channel ID to look up
        db_path: Optional database path

    Returns:
        Dictionary with competitor channel data, or None if not found
        Keys: id, niche_id, youtube_id, name, url, subscriber_count, video_count,
              style, quality_tier, notes, is_active, last_scraped, created_at, updated_at
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, niche_id, youtube_id, name, url, subscriber_count, video_count,
                   style, quality_tier, notes, is_active, last_scraped, created_at, updated_at
            FROM competitor_channels
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
            "video_count": row[6],
            "style": row[7],
            "quality_tier": row[8],
            "notes": row[9],
            "is_active": bool(row[10]),
            "last_scraped": row[11],
            "created_at": row[12],
            "updated_at": row[13]
        }
    finally:
        conn.close()


def get_competitor_channel_by_youtube_id(
    youtube_id: str,
    db_path: Optional[Path] = None
) -> Optional[dict]:
    """
    Retrieve a competitor channel by YouTube ID.

    Args:
        youtube_id: The YouTube channel ID to look up
        db_path: Optional database path

    Returns:
        Dictionary with competitor channel data, or None if not found
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, niche_id, youtube_id, name, url, subscriber_count, video_count,
                   style, quality_tier, notes, is_active, last_scraped, created_at, updated_at
            FROM competitor_channels
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
            "video_count": row[6],
            "style": row[7],
            "quality_tier": row[8],
            "notes": row[9],
            "is_active": bool(row[10]),
            "last_scraped": row[11],
            "created_at": row[12],
            "updated_at": row[13]
        }
    finally:
        conn.close()


def get_channels_by_niche(
    niche_id: int,
    active_only: bool = False,
    db_path: Optional[Path] = None
) -> list[dict]:
    """
    Retrieve all competitor channels for a specific niche.

    Args:
        niche_id: The niche ID to filter by
        active_only: If True, only return active channels (default False)
        db_path: Optional database path

    Returns:
        List of dictionaries, each containing competitor channel data
        Ordered by subscriber_count descending (highest first), then by name
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        if active_only:
            cursor.execute(
                """
                SELECT id, niche_id, youtube_id, name, url, subscriber_count, video_count,
                       style, quality_tier, notes, is_active, last_scraped, created_at, updated_at
                FROM competitor_channels
                WHERE niche_id = ? AND is_active = 1
                ORDER BY subscriber_count DESC, name ASC
                """,
                (niche_id,)
            )
        else:
            cursor.execute(
                """
                SELECT id, niche_id, youtube_id, name, url, subscriber_count, video_count,
                       style, quality_tier, notes, is_active, last_scraped, created_at, updated_at
                FROM competitor_channels
                WHERE niche_id = ?
                ORDER BY subscriber_count DESC, name ASC
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
                "video_count": row[6],
                "style": row[7],
                "quality_tier": row[8],
                "notes": row[9],
                "is_active": bool(row[10]),
                "last_scraped": row[11],
                "created_at": row[12],
                "updated_at": row[13]
            }
            for row in rows
        ]
    finally:
        conn.close()


def update_competitor_channel(
    channel_id: int,
    db_path: Optional[Path] = None,
    **fields
) -> bool:
    """
    Update a competitor channel's fields.

    Args:
        channel_id: The competitor channel ID to update
        db_path: Optional database path
        **fields: Field names and new values
                 Valid fields: niche_id, youtube_id, name, url, subscriber_count,
                              video_count, style, quality_tier, notes, is_active, last_scraped

    Returns:
        True if the channel was updated, False if not found

    Raises:
        ValueError: If invalid field names are provided
        sqlite3.IntegrityError: If niche_id or youtube_id update violates constraints
        sqlite3.Error: For other database errors

    Example:
        update_competitor_channel(1, subscriber_count=50000, is_active=True)
    """
    valid_fields = {
        "niche_id", "youtube_id", "name", "url", "subscriber_count",
        "video_count", "style", "quality_tier", "notes", "is_active", "last_scraped"
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
        set_clause += ", updated_at = CURRENT_TIMESTAMP"
        values = list(fields.values()) + [channel_id]

        cursor.execute(
            f"UPDATE competitor_channels SET {set_clause} WHERE id = ?",
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


def delete_competitor_channel(channel_id: int, db_path: Optional[Path] = None) -> bool:
    """
    Delete a competitor channel by ID.

    Args:
        channel_id: The competitor channel ID to delete
        db_path: Optional database path

    Returns:
        True if the channel was deleted, False if not found

    Raises:
        sqlite3.IntegrityError: If channel has related records (foreign key constraint)
        sqlite3.Error: For other database errors

    Note:
        This will fail if the channel has related records (competitor_videos, etc.)
        due to foreign key constraints.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM competitor_channels WHERE id = ?", (channel_id,))
        conn.commit()

        # Check if any row was deleted
        return cursor.rowcount > 0

    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise sqlite3.IntegrityError(
            f"Cannot delete competitor channel {channel_id}: has related records"
        ) from e
    except sqlite3.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def mark_as_scraped(channel_id: int, db_path: Optional[Path] = None) -> bool:
    """
    Mark a competitor channel as scraped (update last_scraped timestamp).

    Args:
        channel_id: The competitor channel ID to mark as scraped
        db_path: Optional database path

    Returns:
        True if the channel was updated, False if not found

    Raises:
        sqlite3.Error: For database errors
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            UPDATE competitor_channels
            SET last_scraped = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (channel_id,)
        )
        conn.commit()

        # Check if any row was updated
        return cursor.rowcount > 0

    except sqlite3.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()
