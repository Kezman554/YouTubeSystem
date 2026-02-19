"""
CRUD operations for the production context tables.

Manages the single active production context—the topic, angle, and pinned
source material (canon passages + transcript chunks) for the video currently
being researched or scripted.

Tables:
    production_context           — one row: current topic / angle
    production_canon_passages    — canon passages pinned to that context
    production_transcript_chunks — competitor transcript chunks pinned to that context
"""

import sqlite3
from typing import Optional
from pathlib import Path

from .schema import get_connection


# ---------------------------------------------------------------------------
# Context lifecycle
# ---------------------------------------------------------------------------

def get_or_create_production_context(db_path: Optional[Path] = None) -> dict:
    """
    Return the single production context row, creating it if it doesn't exist.

    The system maintains exactly one active production context at a time.

    Returns:
        dict with keys: id, topic, angle, created_at, updated_at
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT id, topic, angle, created_at, updated_at FROM production_context LIMIT 1"
        )
        row = cursor.fetchone()

        if row is not None:
            return {
                "id": row[0],
                "topic": row[1],
                "angle": row[2],
                "created_at": row[3],
                "updated_at": row[4],
            }

        # No context yet — create a blank one
        cursor.execute(
            """
            INSERT INTO production_context (topic, angle, created_at, updated_at)
            VALUES (NULL, NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """
        )
        conn.commit()
        context_id = cursor.lastrowid

        cursor.execute(
            "SELECT id, topic, angle, created_at, updated_at FROM production_context WHERE id = ?",
            (context_id,)
        )
        row = cursor.fetchone()
        return {
            "id": row[0],
            "topic": row[1],
            "angle": row[2],
            "created_at": row[3],
            "updated_at": row[4],
        }
    except sqlite3.Error:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_production_topic(
    topic: str,
    angle: str,
    db_path: Optional[Path] = None
) -> bool:
    """
    Set the topic and angle on the active production context.

    Creates the context row if it doesn't exist yet.

    Args:
        topic: The video topic (e.g., "The Fall of Númenor")
        angle: The creative angle (e.g., "Why Ar-Pharazôn was actually right")

    Returns:
        True on success
    """
    ctx = get_or_create_production_context(db_path)

    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            UPDATE production_context
            SET topic = ?, angle = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (topic, angle, ctx["id"])
        )
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Canon passages
# ---------------------------------------------------------------------------

def add_canon_passage(
    passage_data: dict,
    db_path: Optional[Path] = None
) -> int:
    """
    Pin a canon passage to the active production context.

    Args:
        passage_data: dict with keys:
            chunk_id (str, optional)       — LanceDB chunk ID
            source_title (str, optional)   — e.g. "The Silmarillion"
            chapter (str, optional)        — chapter or section name
            page (int, optional)           — page number
            authority_score (float, optional) — relevance / authority score
            text (str, required)           — the passage text

    Returns:
        ID of the newly inserted row

    Raises:
        ValueError: If 'text' is missing from passage_data
        sqlite3.Error: For database errors
    """
    if not passage_data.get("text"):
        raise ValueError("passage_data must include 'text'")

    ctx = get_or_create_production_context(db_path)

    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO production_canon_passages
                (context_id, chunk_id, source_title, chapter, page, authority_score, text)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ctx["id"],
                passage_data.get("chunk_id"),
                passage_data.get("source_title"),
                passage_data.get("chapter"),
                passage_data.get("page"),
                passage_data.get("authority_score"),
                passage_data["text"],
            )
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error:
        conn.rollback()
        raise
    finally:
        conn.close()


def remove_canon_passage(passage_id: int, db_path: Optional[Path] = None) -> bool:
    """
    Remove a pinned canon passage by its row ID.

    Args:
        passage_id: The production_canon_passages row ID

    Returns:
        True if a row was deleted, False if not found
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "DELETE FROM production_canon_passages WHERE id = ?",
            (passage_id,)
        )
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Transcript chunks
# ---------------------------------------------------------------------------

def add_transcript_chunk(
    chunk_data: dict,
    db_path: Optional[Path] = None
) -> int:
    """
    Pin a competitor transcript chunk to the active production context.

    Args:
        chunk_data: dict with keys:
            chunk_id (str, optional)      — LanceDB chunk ID
            video_id (int, optional)      — competitor_videos row ID
            video_title (str, optional)   — denormalised video title
            channel_name (str, optional)  — denormalised channel name
            view_count (int, optional)    — snapshot view count
            chunk_index (int, optional)   — order within video
            text (str, required)          — the transcript text

    Returns:
        ID of the newly inserted row

    Raises:
        ValueError: If 'text' is missing from chunk_data
        sqlite3.Error: For database errors
    """
    if not chunk_data.get("text"):
        raise ValueError("chunk_data must include 'text'")

    ctx = get_or_create_production_context(db_path)

    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO production_transcript_chunks
                (context_id, chunk_id, video_id, video_title, channel_name,
                 view_count, chunk_index, text)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ctx["id"],
                chunk_data.get("chunk_id"),
                chunk_data.get("video_id"),
                chunk_data.get("video_title"),
                chunk_data.get("channel_name"),
                chunk_data.get("view_count"),
                chunk_data.get("chunk_index"),
                chunk_data["text"],
            )
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error:
        conn.rollback()
        raise
    finally:
        conn.close()


def remove_transcript_chunk(chunk_id: int, db_path: Optional[Path] = None) -> bool:
    """
    Remove a pinned transcript chunk by its row ID.

    Args:
        chunk_id: The production_transcript_chunks row ID

    Returns:
        True if a row was deleted, False if not found
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "DELETE FROM production_transcript_chunks WHERE id = ?",
            (chunk_id,)
        )
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Read / aggregation
# ---------------------------------------------------------------------------

def get_production_context(db_path: Optional[Path] = None) -> dict:
    """
    Return the full active production context: topic, angle, and all pinned items.

    Returns:
        dict with keys:
            id, topic, angle, created_at, updated_at
            canon_passages     — list of dicts (id, chunk_id, source_title, chapter,
                                 page, authority_score, text)
            transcript_chunks  — list of dicts (id, chunk_id, video_id, video_title,
                                 channel_name, view_count, chunk_index, text)
    """
    ctx = get_or_create_production_context(db_path)

    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, chunk_id, source_title, chapter, page, authority_score, text
            FROM production_canon_passages
            WHERE context_id = ?
            ORDER BY id ASC
            """,
            (ctx["id"],)
        )
        canon_rows = cursor.fetchall()

        cursor.execute(
            """
            SELECT id, chunk_id, video_id, video_title, channel_name,
                   view_count, chunk_index, text
            FROM production_transcript_chunks
            WHERE context_id = ?
            ORDER BY id ASC
            """,
            (ctx["id"],)
        )
        transcript_rows = cursor.fetchall()

    finally:
        conn.close()

    ctx["canon_passages"] = [
        {
            "id": r[0],
            "chunk_id": r[1],
            "source_title": r[2],
            "chapter": r[3],
            "page": r[4],
            "authority_score": r[5],
            "text": r[6],
        }
        for r in canon_rows
    ]

    ctx["transcript_chunks"] = [
        {
            "id": r[0],
            "chunk_id": r[1],
            "video_id": r[2],
            "video_title": r[3],
            "channel_name": r[4],
            "view_count": r[5],
            "chunk_index": r[6],
            "text": r[7],
        }
        for r in transcript_rows
    ]

    return ctx


def clear_production_context(db_path: Optional[Path] = None) -> None:
    """
    Delete all pinned passages and transcript chunks, and reset the topic/angle.

    The context row itself is kept so the ID stays stable; only the content is
    cleared.
    """
    ctx = get_or_create_production_context(db_path)

    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "DELETE FROM production_canon_passages WHERE context_id = ?",
            (ctx["id"],)
        )
        cursor.execute(
            "DELETE FROM production_transcript_chunks WHERE context_id = ?",
            (ctx["id"],)
        )
        cursor.execute(
            """
            UPDATE production_context
            SET topic = NULL, angle = NULL, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (ctx["id"],)
        )
        conn.commit()
    except sqlite3.Error:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_production_item_count(db_path: Optional[Path] = None) -> int:
    """
    Return the total number of pinned items (canon passages + transcript chunks).

    Used for the navigation badge in the dashboard.

    Returns:
        Total count across both tables for the active context
    """
    ctx = get_or_create_production_context(db_path)

    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT COUNT(*) FROM production_canon_passages WHERE context_id = ?",
            (ctx["id"],)
        )
        canon_count = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM production_transcript_chunks WHERE context_id = ?",
            (ctx["id"],)
        )
        transcript_count = cursor.fetchone()[0]

        return canon_count + transcript_count
    finally:
        conn.close()
