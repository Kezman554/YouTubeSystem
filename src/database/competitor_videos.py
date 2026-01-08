"""
CRUD operations for the competitor_videos table.

Manages metadata for scraped competitor videos.
"""

import sqlite3
from typing import Optional
from pathlib import Path

from .schema import get_connection


def create_competitor_video(
    channel_id: int,
    niche_id: int,
    youtube_id: str,
    title: str,
    description: Optional[str] = None,
    published_at: Optional[str] = None,
    duration_seconds: Optional[int] = None,
    view_count: Optional[int] = None,
    like_count: Optional[int] = None,
    comment_count: Optional[int] = None,
    thumbnail_url: Optional[str] = None,
    thumbnail_path: Optional[str] = None,
    views_per_sub: Optional[float] = None,
    topic_tags: Optional[str] = None,
    has_transcript: bool = False,
    transcript_cleaned: bool = False,
    db_path: Optional[Path] = None
) -> int:
    """
    Create a new competitor video.

    Args:
        channel_id: ID of the channel this video belongs to
        niche_id: ID of the niche this video belongs to
        youtube_id: YouTube video ID (must be unique)
        title: Video title
        description: Video description
        published_at: Publication timestamp
        duration_seconds: Video duration in seconds
        view_count: Number of views
        like_count: Number of likes
        comment_count: Number of comments
        thumbnail_url: URL to thumbnail
        thumbnail_path: Local path if thumbnail downloaded
        views_per_sub: Calculated metric (view_count / channel subs at time)
        topic_tags: JSON string of detected topics
        has_transcript: Whether video has a transcript
        transcript_cleaned: Whether transcript has been cleaned
        db_path: Optional database path

    Returns:
        The ID of the newly created competitor video

    Raises:
        sqlite3.IntegrityError: If channel_id/niche_id don't exist or youtube_id is duplicate
        sqlite3.Error: For other database errors
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO competitor_videos
            (channel_id, niche_id, youtube_id, title, description, published_at,
             duration_seconds, view_count, like_count, comment_count, thumbnail_url,
             thumbnail_path, views_per_sub, topic_tags, has_transcript, transcript_cleaned,
             first_scraped, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (channel_id, niche_id, youtube_id, title, description, published_at,
             duration_seconds, view_count, like_count, comment_count, thumbnail_url,
             thumbnail_path, views_per_sub, topic_tags, has_transcript, transcript_cleaned)
        )
        conn.commit()
        video_id = cursor.lastrowid
        return video_id
    except sqlite3.IntegrityError as e:
        conn.rollback()
        error_msg = str(e).lower()
        if "youtube_id" in error_msg or "unique" in error_msg:
            raise sqlite3.IntegrityError(f"Video with YouTube ID '{youtube_id}' already exists") from e
        elif "channel" in error_msg:
            raise sqlite3.IntegrityError(f"Channel with ID {channel_id} does not exist") from e
        elif "niche" in error_msg:
            raise sqlite3.IntegrityError(f"Niche with ID {niche_id} does not exist") from e
        raise
    except sqlite3.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_competitor_video(video_id: int, db_path: Optional[Path] = None) -> Optional[dict]:
    """
    Retrieve a competitor video by ID.

    Args:
        video_id: The competitor video ID to look up
        db_path: Optional database path

    Returns:
        Dictionary with competitor video data, or None if not found
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, channel_id, niche_id, youtube_id, title, description, published_at,
                   duration_seconds, view_count, like_count, comment_count, thumbnail_url,
                   thumbnail_path, views_per_sub, topic_tags, has_transcript, transcript_cleaned,
                   first_scraped, last_updated, created_at
            FROM competitor_videos
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
            "published_at": row[6],
            "duration_seconds": row[7],
            "view_count": row[8],
            "like_count": row[9],
            "comment_count": row[10],
            "thumbnail_url": row[11],
            "thumbnail_path": row[12],
            "views_per_sub": row[13],
            "topic_tags": row[14],
            "has_transcript": bool(row[15]),
            "transcript_cleaned": bool(row[16]),
            "first_scraped": row[17],
            "last_updated": row[18],
            "created_at": row[19]
        }
    finally:
        conn.close()


def get_competitor_video_by_youtube_id(
    youtube_id: str,
    db_path: Optional[Path] = None
) -> Optional[dict]:
    """
    Retrieve a competitor video by YouTube ID.

    Args:
        youtube_id: The YouTube video ID to look up
        db_path: Optional database path

    Returns:
        Dictionary with competitor video data, or None if not found
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, channel_id, niche_id, youtube_id, title, description, published_at,
                   duration_seconds, view_count, like_count, comment_count, thumbnail_url,
                   thumbnail_path, views_per_sub, topic_tags, has_transcript, transcript_cleaned,
                   first_scraped, last_updated, created_at
            FROM competitor_videos
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
            "published_at": row[6],
            "duration_seconds": row[7],
            "view_count": row[8],
            "like_count": row[9],
            "comment_count": row[10],
            "thumbnail_url": row[11],
            "thumbnail_path": row[12],
            "views_per_sub": row[13],
            "topic_tags": row[14],
            "has_transcript": bool(row[15]),
            "transcript_cleaned": bool(row[16]),
            "first_scraped": row[17],
            "last_updated": row[18],
            "created_at": row[19]
        }
    finally:
        conn.close()


def get_videos_by_channel(
    channel_id: int,
    limit: Optional[int] = None,
    db_path: Optional[Path] = None
) -> list[dict]:
    """
    Retrieve all competitor videos for a specific channel.

    Args:
        channel_id: The channel ID to filter by
        limit: Optional limit on number of results
        db_path: Optional database path

    Returns:
        List of dictionaries, each containing competitor video data
        Ordered by published_at descending (newest first)
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        if limit:
            cursor.execute(
                """
                SELECT id, channel_id, niche_id, youtube_id, title, description, published_at,
                       duration_seconds, view_count, like_count, comment_count, thumbnail_url,
                       thumbnail_path, views_per_sub, topic_tags, has_transcript, transcript_cleaned,
                       first_scraped, last_updated, created_at
                FROM competitor_videos
                WHERE channel_id = ?
                ORDER BY published_at DESC
                LIMIT ?
                """,
                (channel_id, limit)
            )
        else:
            cursor.execute(
                """
                SELECT id, channel_id, niche_id, youtube_id, title, description, published_at,
                       duration_seconds, view_count, like_count, comment_count, thumbnail_url,
                       thumbnail_path, views_per_sub, topic_tags, has_transcript, transcript_cleaned,
                       first_scraped, last_updated, created_at
                FROM competitor_videos
                WHERE channel_id = ?
                ORDER BY published_at DESC
                """,
                (channel_id,)
            )

        rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "channel_id": row[1],
                "niche_id": row[2],
                "youtube_id": row[3],
                "title": row[4],
                "description": row[5],
                "published_at": row[6],
                "duration_seconds": row[7],
                "view_count": row[8],
                "like_count": row[9],
                "comment_count": row[10],
                "thumbnail_url": row[11],
                "thumbnail_path": row[12],
                "views_per_sub": row[13],
                "topic_tags": row[14],
                "has_transcript": bool(row[15]),
                "transcript_cleaned": bool(row[16]),
                "first_scraped": row[17],
                "last_updated": row[18],
                "created_at": row[19]
            }
            for row in rows
        ]
    finally:
        conn.close()


def get_videos_by_niche(
    niche_id: int,
    limit: Optional[int] = None,
    db_path: Optional[Path] = None
) -> list[dict]:
    """
    Retrieve all competitor videos for a specific niche.

    Args:
        niche_id: The niche ID to filter by
        limit: Optional limit on number of results
        db_path: Optional database path

    Returns:
        List of dictionaries, each containing competitor video data
        Ordered by published_at descending (newest first)
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        if limit:
            cursor.execute(
                """
                SELECT id, channel_id, niche_id, youtube_id, title, description, published_at,
                       duration_seconds, view_count, like_count, comment_count, thumbnail_url,
                       thumbnail_path, views_per_sub, topic_tags, has_transcript, transcript_cleaned,
                       first_scraped, last_updated, created_at
                FROM competitor_videos
                WHERE niche_id = ?
                ORDER BY published_at DESC
                LIMIT ?
                """,
                (niche_id, limit)
            )
        else:
            cursor.execute(
                """
                SELECT id, channel_id, niche_id, youtube_id, title, description, published_at,
                       duration_seconds, view_count, like_count, comment_count, thumbnail_url,
                       thumbnail_path, views_per_sub, topic_tags, has_transcript, transcript_cleaned,
                       first_scraped, last_updated, created_at
                FROM competitor_videos
                WHERE niche_id = ?
                ORDER BY published_at DESC
                """,
                (niche_id,)
            )

        rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "channel_id": row[1],
                "niche_id": row[2],
                "youtube_id": row[3],
                "title": row[4],
                "description": row[5],
                "published_at": row[6],
                "duration_seconds": row[7],
                "view_count": row[8],
                "like_count": row[9],
                "comment_count": row[10],
                "thumbnail_url": row[11],
                "thumbnail_path": row[12],
                "views_per_sub": row[13],
                "topic_tags": row[14],
                "has_transcript": bool(row[15]),
                "transcript_cleaned": bool(row[16]),
                "first_scraped": row[17],
                "last_updated": row[18],
                "created_at": row[19]
            }
            for row in rows
        ]
    finally:
        conn.close()


def update_competitor_video(
    video_id: int,
    db_path: Optional[Path] = None,
    **fields
) -> bool:
    """
    Update a competitor video's fields.

    Args:
        video_id: The competitor video ID to update
        db_path: Optional database path
        **fields: Field names and new values
                 Valid fields: channel_id, niche_id, youtube_id, title, description,
                              published_at, duration_seconds, view_count, like_count,
                              comment_count, thumbnail_url, thumbnail_path, views_per_sub,
                              topic_tags, has_transcript, transcript_cleaned

    Returns:
        True if the video was updated, False if not found

    Raises:
        ValueError: If invalid field names are provided
        sqlite3.IntegrityError: If foreign key or unique constraints violated
        sqlite3.Error: For other database errors

    Example:
        update_competitor_video(1, view_count=50000, like_count=1000)
    """
    valid_fields = {
        "channel_id", "niche_id", "youtube_id", "title", "description",
        "published_at", "duration_seconds", "view_count", "like_count",
        "comment_count", "thumbnail_url", "thumbnail_path", "views_per_sub",
        "topic_tags", "has_transcript", "transcript_cleaned", "transcript"
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
        set_clause += ", last_updated = CURRENT_TIMESTAMP"
        values = list(fields.values()) + [video_id]

        cursor.execute(
            f"UPDATE competitor_videos SET {set_clause} WHERE id = ?",
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
                f"Video with YouTube ID '{fields['youtube_id']}' already exists"
            ) from e
        elif "channel_id" in fields and "channel" in error_msg:
            raise sqlite3.IntegrityError(f"Channel with ID {fields['channel_id']} does not exist") from e
        elif "niche_id" in fields and "niche" in error_msg:
            raise sqlite3.IntegrityError(f"Niche with ID {fields['niche_id']} does not exist") from e
        raise
    except sqlite3.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_competitor_video(video_id: int, db_path: Optional[Path] = None) -> bool:
    """
    Delete a competitor video by ID.

    Args:
        video_id: The competitor video ID to delete
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
        cursor.execute("DELETE FROM competitor_videos WHERE id = ?", (video_id,))
        conn.commit()

        # Check if any row was deleted
        return cursor.rowcount > 0

    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise sqlite3.IntegrityError(
            f"Cannot delete competitor video {video_id}: has related records"
        ) from e
    except sqlite3.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def mark_transcript_cleaned(video_id: int, db_path: Optional[Path] = None) -> bool:
    """
    Mark a competitor video's transcript as cleaned.

    Args:
        video_id: The competitor video ID to mark
        db_path: Optional database path

    Returns:
        True if the video was updated, False if not found

    Raises:
        sqlite3.Error: For database errors
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            UPDATE competitor_videos
            SET transcript_cleaned = TRUE, last_updated = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (video_id,)
        )
        conn.commit()

        # Check if any row was updated
        return cursor.rowcount > 0

    except sqlite3.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()
