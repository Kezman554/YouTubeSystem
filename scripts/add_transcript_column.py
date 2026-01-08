"""
Add transcript column to competitor_videos table.

This is a one-time migration to add support for storing raw transcripts.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.schema import get_connection


def main():
    print("=" * 80)
    print("ADDING TRANSCRIPT COLUMN TO DATABASE")
    print("=" * 80)
    print()

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(competitor_videos)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'transcript' in columns:
            print("Column 'transcript' already exists. Nothing to do.")
            return

        # Add transcript column
        print("Adding 'transcript' column to competitor_videos table...")
        cursor.execute("""
            ALTER TABLE competitor_videos
            ADD COLUMN transcript TEXT
        """)
        conn.commit()
        print("[OK] Column added successfully")

    except Exception as e:
        print(f"[ERROR] Failed to add column: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

    print()
    print("Migration complete!")


if __name__ == "__main__":
    main()
