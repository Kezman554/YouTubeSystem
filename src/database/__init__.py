"""Database module for Content Intelligence System."""

from .schema import init_db, get_connection, DB_PATH
from .production_context import (
    get_or_create_production_context,
    update_production_topic,
    add_canon_passage,
    remove_canon_passage,
    add_transcript_chunk,
    remove_transcript_chunk,
    get_production_context,
    clear_production_context,
    get_production_item_count,
)

__all__ = [
    "init_db",
    "get_connection",
    "DB_PATH",
    "get_or_create_production_context",
    "update_production_topic",
    "add_canon_passage",
    "remove_canon_passage",
    "add_transcript_chunk",
    "remove_transcript_chunk",
    "get_production_context",
    "clear_production_context",
    "get_production_item_count",
]
