"""
CRUD operations for the my_videos table.

Manages user's own video content with production tracking.
"""

import sqlite3
from typing import Optional
from pathlib import Path

from .schema import get_connection


def create_my_video(
    channel_id: int,
    niche_id: int,
    title: str,
    description: Optional[str] = None,
    youtube_id: Optional[str] = None,
    status: str = "idea",
    script_path: Optional[str] = None,
    notes: Optional[str] = None,
    published_at: Optional[str] = None,
    duration_seconds: Optional[int] = None,
    view_count: Optional[int] = None,
    like_count: Optional[int] = None,
    comment_count: Optional[int] = None,
    ctr: Optional[float] = None,
    avg_view_duration: Optional[float] = None,
    avg_view_percentage: Optional[float] = None,
    thumbnail_url: Optional[str] = None,
    thumbnail_path: Optional[str] = None,
    db_path: Optional[Path] = None
) -> int:
    """
    Create a new video.

    Args:
        channel_id: ID of the channel this video belongs to
        niche_id: ID of the niche this video belongs to
        title: Video title
        description: Video description
        youtube_id: YouTube video ID (optional, NULL until published)
        status: Production status (default "idea": "idea", "researching", "scripting", "production", "published")
        script_path: Local path to script file
        notes: Production notes
        published_at: Publication timestamp
        duration_seconds: Video duration in seconds
        view_count: Number of views
        like_count: Number of likes
        comment_count: Number of comments
        ctr: Click-through rate
        avg_view_duration: Average view duration in seconds
        avg_view_percentage: AVD as percentage of video length
        thumbnail_url: URL to thumbnail
        thumbnail_path: Local path to thumbnail
        db_path: Optional database path

    Returns:
        The ID of the newly created video

    Raises:
        sqlite3.IntegrityError: If channel_id/niche_id don't exist
        sqlite3.Error: For other database errors
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO my_videos
            (channel_id, niche_id, youtube_id, title, description, status, script_path, notes,
             published_at, duration_seconds, view_count, like_count, comment_count,
             ctr, avg_view_duration, avg_view_percentage, thumbnail_url, thumbnail_path,
             created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (channel_id, niche_id, youtube_id, title, description, status, script_path, notes,
             published_at, duration_seconds, view_count, like_count, comment_count,
             ctr, avg_view_duration, avg_view_percentage, thumbnail_url, thumbnail_path)
        )
        conn.commit()
        video_id = cursor.lastrowid
        return video_id
    except sqlite3.IntegrityError as e:
        conn.rollback()
        error_msg = str(e).lower()
        if "channel" in error_msg:
            raise sqlite3.IntegrityError(f"Channel with ID {channel_id} does not exist") from e
        elif "niche" in error_msg:
            raise sqlite3.IntegrityError(f"Niche with ID {niche_id} does not exist") from e
        raise
    except sqlite3.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_my_video(video_id: int, db_path: Optional[Path] = None) -> Optional[dict]:
    """
    Retrieve a video by ID.

    Args:
        video_id: The video ID to look up
        db_path: Optional database path

    Returns:
        Dictionary with video data, or None if not found
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, channel_id, niche_id, youtube_id, title, description, status,
                   script_path, notes, published_at, duration_seconds, view_count,
                   like_count, comment_count, ctr, avg_view_duration, avg_view_percentage,
                   thumbnail_url, thumbnail_path, created_at, updated_at
            FROM my_videos
            WHERE id = ?
            """,
            (video_id,)
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return {
            "id": row[0],
            "channel_id": row[1],
            "niche_id": row[2],
            "youtube_id": row[3],
            "title": row[4],
            "description": row[5],
            "status": row[6],
            "script_path": row[7],
            "notes": row[8],
            "published_at": row[9],
            "duration_seconds": row[10],
            "view_count": row[11],
            "like_count": row[12],
            "comment_count": row[13],
            "ctr": row[14],
            "avg_view_duration": row[15],
            "avg_view_percentage": row[16],
            "thumbnail_url": row[17],
            "thumbnail_path": row[18],
            "created_at": row[19],
            "updated_at": row[20]
        }
    finally:
        conn.close()


def get_my_video_by_youtube_id(
    youtube_id: str,
    db_path: Optional[Path] = None
) -> Optional[dict]:
    """
    Retrieve a video by YouTube ID.

    Args:
        youtube_id: The YouTube video ID to look up
        db_path: Optional database path

    Returns:
        Dictionary with video data, or None if not found
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, channel_id, niche_id, youtube_id, title, description, status,
                   script_path, notes, published_at, duration_seconds, view_count,
                   like_count, comment_count, ctr, avg_view_duration, avg_view_percentage,
                   thumbnail_url, thumbnail_path, created_at, updated_at
            FROM my_videos
            WHERE youtube_id = ?
            """,
            (youtube_id,)
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return {
            "id": row[0],
            "channel_id": row[1],
            "niche_id": row[2],
            "youtube_id": row[3],
            "title": row[4],
            "description": row[5],
            "status": row[6],
            "script_path": row[7],
            "notes": row[8],
            "published_at": row[9],
            "duration_seconds": row[10],
            "view_count": row[11],
            "like_count": row[12],
            "comment_count": row[13],
            "ctr": row[14],
            "avg_view_duration": row[15],
            "avg_view_percentage": row[16],
            "thumbnail_url": row[17],
            "thumbnail_path": row[18],
            "created_at": row[19],
            "updated_at": row[20]
        }
    finally:
        conn.close()


def get_videos_by_channel(
    channel_id: int,
    limit: Optional[int] = None,
    db_path: Optional[Path] = None
) -> list[dict]:
    """
    Retrieve all videos for a specific channel.

    Args:
        channel_id: The channel ID to filter by
        limit: Optional limit on number of results
        db_path: Optional database path

    Returns:
        List of dictionaries, each containing video data
        Ordered by created_at descending (newest first)
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        if limit:
            cursor.execute(
                """
                SELECT id, channel_id, niche_id, youtube_id, title, description, status,
                       script_path, notes, published_at, duration_seconds, view_count,
                       like_count, comment_count, ctr, avg_view_duration, avg_view_percentage,
                       thumbnail_url, thumbnail_path, created_at, updated_at
                FROM my_videos
                WHERE channel_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (channel_id, limit)
            )
        else:
            cursor.execute(
                """
                SELECT id, channel_id, niche_id, youtube_id, title, description, status,
                       script_path, notes, published_at, duration_seconds, view_count,
                       like_count, comment_count, ctr, avg_view_duration, avg_view_percentage,
                       thumbnail_url, thumbnail_path, created_at, updated_at
                FROM my_videos
                WHERE channel_id = ?
                ORDER BY created_at DESC
                """,
                (channel_id,)
            )

        rows = cursor.fetchall()
        return _rows_to_dicts(rows)
    finally:
        conn.close()


def get_videos_by_niche(
    niche_id: int,
    limit: Optional[int] = None,
    db_path: Optional[Path] = None
) -> list[dict]:
    """
    Retrieve all videos for a specific niche.

    Args:
        niche_id: The niche ID to filter by
        limit: Optional limit on number of results
        db_path: Optional database path

    Returns:
        List of dictionaries, each containing video data
        Ordered by created_at descending (newest first)
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        if limit:
            cursor.execute(
                """
                SELECT id, channel_id, niche_id, youtube_id, title, description, status,
                       script_path, notes, published_at, duration_seconds, view_count,
                       like_count, comment_count, ctr, avg_view_duration, avg_view_percentage,
                       thumbnail_url, thumbnail_path, created_at, updated_at
                FROM my_videos
                WHERE niche_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (niche_id, limit)
            )
        else:
            cursor.execute(
                """
                SELECT id, channel_id, niche_id, youtube_id, title, description, status,
                       script_path, notes, published_at, duration_seconds, view_count,
                       like_count, comment_count, ctr, avg_view_duration, avg_view_percentage,
                       thumbnail_url, thumbnail_path, created_at, updated_at
                FROM my_videos
                WHERE niche_id = ?
                ORDER BY created_at DESC
                """,
                (niche_id,)
            )

        rows = cursor.fetchall()
        return _rows_to_dicts(rows)
    finally:
        conn.close()


def get_videos_by_status(
    status: str,
    limit: Optional[int] = None,
    db_path: Optional[Path] = None
) -> list[dict]:
    """
    Retrieve all videos with a specific production status.

    Args:
        status: The status to filter by (e.g., "idea", "researching", "scripting", "production", "published")
        limit: Optional limit on number of results
        db_path: Optional database path

    Returns:
        List of dictionaries, each containing video data
        Ordered by created_at descending (newest first)
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        if limit:
            cursor.execute(
                """
                SELECT id, channel_id, niche_id, youtube_id, title, description, status,
                       script_path, notes, published_at, duration_seconds, view_count,
                       like_count, comment_count, ctr, avg_view_duration, avg_view_percentage,
                       thumbnail_url, thumbnail_path, created_at, updated_at
                FROM my_videos
                WHERE status = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (status, limit)
            )
        else:
            cursor.execute(
                """
                SELECT id, channel_id, niche_id, youtube_id, title, description, status,
                       script_path, notes, published_at, duration_seconds, view_count,
                       like_count, comment_count, ctr, avg_view_duration, avg_view_percentage,
                       thumbnail_url, thumbnail_path, created_at, updated_at
                FROM my_videos
                WHERE status = ?
                ORDER BY created_at DESC
                """,
                (status,)
            )

        rows = cursor.fetchall()
        return _rows_to_dicts(rows)
    finally:
        conn.close()


def update_my_video(
    video_id: int,
    db_path: Optional[Path] = None,
    **fields
) -> bool:
    """
    Update a video's fields.

    Args:
        video_id: The video ID to update
        db_path: Optional database path
        **fields: Field names and new values
                 Valid fields: channel_id, niche_id, youtube_id, title, description,
                              status, script_path, notes, published_at, duration_seconds,
                              view_count, like_count, comment_count, ctr, avg_view_duration,
                              avg_view_percentage, thumbnail_url, thumbnail_path

    Returns:
        True if the video was updated, False if not found

    Raises:
        ValueError: If invalid field names are provided
        sqlite3.IntegrityError: If foreign key constraints violated
        sqlite3.Error: For other database errors

    Example:
        update_my_video(1, status="production", script_path="/path/to/script.md")
    """
    valid_fields = {
        "channel_id", "niche_id", "youtube_id", "title", "description",
        "status", "script_path", "notes", "published_at", "duration_seconds",
        "view_count", "like_count", "comment_count", "ctr", "avg_view_duration",
        "avg_view_percentage", "thumbnail_url", "thumbnail_path"
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
        values = list(fields.values()) + [video_id]

        cursor.execute(
            f"UPDATE my_videos SET {set_clause} WHERE id = ?",
            values
        )
        conn.commit()

        # Check if any row was updated
        return cursor.rowcount > 0

    except sqlite3.IntegrityError as e:
        conn.rollback()
        error_msg = str(e).lower()
        if "channel_id" in fields and "channel" in error_msg:
            raise sqlite3.IntegrityError(f"Channel with ID {fields['channel_id']} does not exist") from e
        elif "niche_id" in fields and "niche" in error_msg:
            raise sqlite3.IntegrityError(f"Niche with ID {fields['niche_id']} does not exist") from e
        raise
    except sqlite3.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_my_video(video_id: int, db_path: Optional[Path] = None) -> bool:
    """
    Delete a video by ID.

    Args:
        video_id: The video ID to delete
        db_path: Optional database path

    Returns:
        True if the video was deleted, False if not found

    Raises:
        sqlite3.IntegrityError: If video has related records (foreign key constraint)
        sqlite3.Error: For other database errors
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM my_videos WHERE id = ?", (video_id,))
        conn.commit()

        # Check if any row was deleted
        return cursor.rowcount > 0

    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise sqlite3.IntegrityError(
            f"Cannot delete video {video_id}: has related records"
        ) from e
    except sqlite3.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_status(
    video_id: int,
    status: str,
    db_path: Optional[Path] = None
) -> bool:
    """
    Update a video's production status.

    Convenience function for updating just the status.

    Args:
        video_id: The video ID to update
        status: New status (e.g., "idea", "researching", "scripting", "production", "published")
        db_path: Optional database path

    Returns:
        True if the video was updated, False if not found

    Raises:
        sqlite3.Error: For database errors
    """
    return update_my_video(video_id, status=status, db_path=db_path)


def mark_as_published(
    video_id: int,
    youtube_id: str,
    published_at: str,
    db_path: Optional[Path] = None
) -> bool:
    """
    Mark a video as published.

    Updates status to "published" and sets youtube_id and published_at.

    Args:
        video_id: The video ID to mark as published
        youtube_id: YouTube video ID
        published_at: Publication timestamp
        db_path: Optional database path

    Returns:
        True if the video was updated, False if not found

    Raises:
        sqlite3.Error: For database errors
    """
    return update_my_video(
        video_id,
        status="published",
        youtube_id=youtube_id,
        published_at=published_at,
        db_path=db_path
    )


def _rows_to_dicts(rows: list) -> list[dict]:
    """Helper function to convert database rows to dictionaries."""
    return [
        {
            "id": row[0],
            "channel_id": row[1],
            "niche_id": row[2],
            "youtube_id": row[3],
            "title": row[4],
            "description": row[5],
            "status": row[6],
            "script_path": row[7],
            "notes": row[8],
            "published_at": row[9],
            "duration_seconds": row[10],
            "view_count": row[11],
            "like_count": row[12],
            "comment_count": row[13],
            "ctr": row[14],
            "avg_view_duration": row[15],
            "avg_view_percentage": row[16],
            "thumbnail_url": row[17],
            "thumbnail_path": row[18],
            "created_at": row[19],
            "updated_at": row[20]
        }
        for row in rows
    ]
