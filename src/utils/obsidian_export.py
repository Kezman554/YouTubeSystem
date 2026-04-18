"""Export competitor transcripts to the Obsidian vault as markdown notes."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

OBSIDIAN_BASE_PATH = r"C:\Dev\Alfred-Vault\2-projects\LOTR\Rival Transcripts"

_INVALID_FILENAME_CHARS = set(':?/\\"<>|')


def _sanitize_filename(name: str) -> str:
    """Strip characters that are invalid in Windows filenames."""
    cleaned = "".join(c for c in name if c not in _INVALID_FILENAME_CHARS)
    cleaned = cleaned.strip().rstrip(".")
    return cleaned or "untitled"


def _escape_yaml(value: str) -> str:
    """Escape double quotes for a YAML double-quoted scalar."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def export_transcript_to_obsidian(
    video_title: str,
    channel_name: str,
    youtube_id: str,
    views: Optional[int],
    niche_name: str,
    transcript_text: str,
) -> Optional[Path]:
    """Write a transcript to the Obsidian vault as a markdown note.

    Returns the path written to, or None if the file already existed.
    Raises OSError if the write itself fails.
    """
    base = Path(OBSIDIAN_BASE_PATH)
    channel_dir = base / _sanitize_filename(channel_name)
    file_path = channel_dir / f"{_sanitize_filename(video_title)}.md"

    if file_path.exists():
        return None

    channel_dir.mkdir(parents=True, exist_ok=True)

    views_value = views if isinstance(views, int) else 0
    date_scraped = datetime.now().strftime("%Y-%m-%d")

    frontmatter = (
        "---\n"
        f'video_title: "{_escape_yaml(video_title)}"\n'
        f'channel: "{_escape_yaml(channel_name)}"\n'
        f'youtube_id: "{_escape_yaml(youtube_id)}"\n'
        f"views: {views_value}\n"
        f'niche: "{_escape_yaml(niche_name)}"\n'
        "source: competitor_transcript\n"
        f"date_scraped: {date_scraped}\n"
        "---\n\n"
    )

    file_path.write_text(frontmatter + transcript_text, encoding="utf-8")
    return file_path
