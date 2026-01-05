"""
Database schema for Content Intelligence System.

Creates all SQLite tables as defined in docs/DATA_MODEL.md.
Database stored at: data/content.db
"""

import sqlite3
from pathlib import Path
from typing import Optional


# Database path configuration
DB_DIR = Path(__file__).parent.parent.parent / "data"
DB_PATH = DB_DIR / "content.db"


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """
    Get a database connection with foreign keys enabled.

    Args:
        db_path: Optional path to database file. Defaults to data/content.db

    Returns:
        SQLite connection with foreign keys enabled
    """
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Optional[Path] = None) -> None:
    """
    Initialize the database with all tables and indexes.

    Creates:
    - 14 SQLite tables
    - 8 recommended indexes
    - Enables foreign key constraints

    Args:
        db_path: Optional path to database file. Defaults to data/content.db
    """
    # Ensure data directory exists
    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = get_connection(path)
    cursor = conn.cursor()

    # 1. niches
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS niches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            type TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. canon_sources
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS canon_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            niche_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            author TEXT,
            source_type TEXT,
            file_path TEXT,
            url TEXT,
            priority INTEGER DEFAULT 1,
            ingested BOOLEAN DEFAULT FALSE,
            ingested_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (niche_id) REFERENCES niches(id)
        )
    """)

    # 3. glossary
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS glossary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            niche_id INTEGER NOT NULL,
            term TEXT NOT NULL,
            term_type TEXT,
            phonetic_hints TEXT,
            aliases TEXT,
            description TEXT,
            source_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (niche_id) REFERENCES niches(id),
            FOREIGN KEY (source_id) REFERENCES canon_sources(id)
        )
    """)

    # 4. competitor_channels
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS competitor_channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            niche_id INTEGER NOT NULL,
            youtube_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            url TEXT,
            subscriber_count INTEGER,
            video_count INTEGER,
            style TEXT,
            quality_tier TEXT,
            notes TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            last_scraped TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (niche_id) REFERENCES niches(id)
        )
    """)

    # 5. competitor_videos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS competitor_videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id INTEGER NOT NULL,
            niche_id INTEGER NOT NULL,
            youtube_id TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            published_at TIMESTAMP,
            duration_seconds INTEGER,
            view_count INTEGER,
            like_count INTEGER,
            comment_count INTEGER,
            thumbnail_url TEXT,
            thumbnail_path TEXT,
            views_per_sub REAL,
            topic_tags TEXT,
            has_transcript BOOLEAN DEFAULT FALSE,
            transcript_cleaned BOOLEAN DEFAULT FALSE,
            first_scraped TIMESTAMP,
            last_updated TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (channel_id) REFERENCES competitor_channels(id),
            FOREIGN KEY (niche_id) REFERENCES niches(id)
        )
    """)

    # 6. performance_snapshots
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS performance_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER NOT NULL,
            view_count INTEGER,
            like_count INTEGER,
            comment_count INTEGER,
            captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (video_id) REFERENCES competitor_videos(id)
        )
    """)

    # 7. my_channels
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS my_channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            niche_id INTEGER NOT NULL,
            youtube_id TEXT UNIQUE,
            name TEXT NOT NULL,
            url TEXT,
            subscriber_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (niche_id) REFERENCES niches(id)
        )
    """)

    # 8. my_videos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS my_videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id INTEGER NOT NULL,
            niche_id INTEGER NOT NULL,
            youtube_id TEXT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'idea',
            script_path TEXT,
            notes TEXT,
            published_at TIMESTAMP,
            duration_seconds INTEGER,
            view_count INTEGER,
            like_count INTEGER,
            comment_count INTEGER,
            ctr REAL,
            avg_view_duration REAL,
            avg_view_percentage REAL,
            thumbnail_url TEXT,
            thumbnail_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (channel_id) REFERENCES my_channels(id),
            FOREIGN KEY (niche_id) REFERENCES niches(id)
        )
    """)

    # 9. assets
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            niche_id INTEGER NOT NULL,
            file_path TEXT NOT NULL,
            file_type TEXT,
            source TEXT,
            prompt TEXT,
            description TEXT,
            subject_tags TEXT,
            mood_tags TEXT,
            style_tags TEXT,
            times_used INTEGER DEFAULT 0,
            last_used_in INTEGER,
            last_used_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (niche_id) REFERENCES niches(id),
            FOREIGN KEY (last_used_in) REFERENCES my_videos(id)
        )
    """)

    # 10. asset_usage
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS asset_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id INTEGER NOT NULL,
            video_id INTEGER NOT NULL,
            timestamp_start REAL,
            timestamp_end REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (asset_id) REFERENCES assets(id),
            FOREIGN KEY (video_id) REFERENCES my_videos(id)
        )
    """)

    # 11. thumbnails
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS thumbnails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            niche_id INTEGER NOT NULL,
            file_path TEXT NOT NULL,
            source_type TEXT,
            competitor_video_id INTEGER,
            my_video_id INTEGER,
            analysis TEXT,
            style_tags TEXT,
            effectiveness REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (niche_id) REFERENCES niches(id),
            FOREIGN KEY (competitor_video_id) REFERENCES competitor_videos(id),
            FOREIGN KEY (my_video_id) REFERENCES my_videos(id)
        )
    """)

    # 12. tags
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            niche_id INTEGER,
            name TEXT NOT NULL,
            tag_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (niche_id) REFERENCES niches(id),
            UNIQUE(niche_id, name, tag_type)
        )
    """)

    # 13. video_tags
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS video_tags (
            video_id INTEGER NOT NULL,
            video_type TEXT NOT NULL,
            tag_id INTEGER NOT NULL,
            confidence REAL,
            PRIMARY KEY (video_id, video_type, tag_id),
            FOREIGN KEY (tag_id) REFERENCES tags(id)
        )
    """)

    # 14. cross_platform_posts
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cross_platform_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            my_video_id INTEGER,
            niche_id INTEGER NOT NULL,
            platform TEXT NOT NULL,
            platform_id TEXT,
            url TEXT,
            title TEXT,
            posted_at TIMESTAMP,
            view_count INTEGER,
            like_count INTEGER,
            comment_count INTEGER,
            click_throughs INTEGER,
            last_updated TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (my_video_id) REFERENCES my_videos(id),
            FOREIGN KEY (niche_id) REFERENCES niches(id)
        )
    """)

    # Create indexes for query performance
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_competitor_videos_niche
        ON competitor_videos(niche_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_competitor_videos_channel
        ON competitor_videos(channel_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_competitor_videos_published
        ON competitor_videos(published_at)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_my_videos_status
        ON my_videos(status)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_my_videos_niche
        ON my_videos(niche_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_assets_niche
        ON assets(niche_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_glossary_niche
        ON glossary(niche_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_tags_niche
        ON tags(niche_id)
    """)

    conn.commit()
    conn.close()

    print(f"[OK] Database initialized at {path}")
    print(f"[OK] Created 14 tables")
    print(f"[OK] Created 8 indexes")
    print(f"[OK] Foreign key constraints enabled")


if __name__ == "__main__":
    init_db()
