"""
Settings page - Configure system settings and API keys.
"""

import streamlit as st
from pathlib import Path
import os
from dotenv import load_dotenv, set_key
import anthropic
import requests


# Load environment variables
load_dotenv()


def test_youtube_api(api_key: str) -> tuple[bool, str]:
    """
    Test YouTube API key validity.

    Returns:
        (success: bool, message: str)
    """
    try:
        # Simple test: get channel info for a known channel
        url = "https://www.googleapis.com/youtube/v3/channels"
        params = {
            "part": "snippet",
            "id": "UC_x5XG1OV2P6uZZ5FSM9Ttw",  # Google Developers channel
            "key": api_key
        }

        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get("items"):
                return True, "✅ YouTube API key is valid"
            else:
                return False, "❌ API key valid but no data returned"
        elif response.status_code == 400:
            return False, "❌ Invalid API key format"
        elif response.status_code == 403:
            error = response.json().get("error", {})
            if "quotaExceeded" in str(error):
                return True, "⚠️ API key valid but quota exceeded"
            return False, "❌ API key invalid or disabled"
        else:
            return False, f"❌ Error: HTTP {response.status_code}"

    except requests.exceptions.Timeout:
        return False, "❌ Request timeout - check internet connection"
    except Exception as e:
        return False, f"❌ Error: {str(e)}"


def test_anthropic_api(api_key: str) -> tuple[bool, str]:
    """
    Test Anthropic API key validity.

    Returns:
        (success: bool, message: str)
    """
    try:
        client = anthropic.Anthropic(api_key=api_key)

        # Simple test: list available models (doesn't consume credits)
        # Actually, we'll just try to create a minimal message
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=10,
            messages=[{"role": "user", "content": "test"}]
        )

        if response:
            return True, "✅ Anthropic API key is valid"

    except anthropic.AuthenticationError:
        return False, "❌ Invalid API key"
    except anthropic.PermissionDeniedError:
        return False, "❌ API key lacks required permissions"
    except anthropic.RateLimitError:
        return True, "⚠️ API key valid but rate limited"
    except Exception as e:
        return False, f"❌ Error: {str(e)}"

    return False, "❌ Unknown error"


def save_api_key(key_name: str, key_value: str) -> bool:
    """
    Save API key to .env file.

    Args:
        key_name: Name of the key (e.g., "YOUTUBE_API_KEY")
        key_value: Value of the key

    Returns:
        True if successful, False otherwise
    """
    try:
        env_path = Path(__file__).parent.parent.parent.parent / ".env"

        # Create .env if it doesn't exist
        if not env_path.exists():
            env_path.touch()

        # Update or create the key
        set_key(str(env_path), key_name, key_value)

        return True
    except Exception as e:
        st.error(f"Error saving API key: {e}")
        return False


def get_database_stats() -> dict:
    """Get statistics about the database."""
    from src.database.schema import get_connection
    from src.pipeline.vectorstore import get_stats

    stats = {
        "sqlite": {},
        "lancedb": {}
    }

    # SQLite stats
    db_path = Path(__file__).parent.parent.parent.parent / "data" / "content.db"
    if db_path.exists():
        stats["sqlite"]["size"] = db_path.stat().st_size / (1024 * 1024)  # MB
        stats["sqlite"]["path"] = str(db_path)

        # Get table counts
        try:
            conn = get_connection()
            cursor = conn.cursor()

            tables = [
                "niches", "canon_sources", "glossary", "competitor_channels",
                "competitor_videos", "performance_snapshots", "my_channels",
                "my_videos", "assets", "thumbnails", "tags"
            ]

            counts = {}
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    counts[table] = count
                except Exception:
                    counts[table] = 0

            stats["sqlite"]["table_counts"] = counts
            conn.close()

        except Exception as e:
            stats["sqlite"]["error"] = str(e)

    # LanceDB stats
    try:
        vector_stats = get_stats()
        stats["lancedb"] = vector_stats
    except Exception as e:
        stats["lancedb"]["error"] = str(e)

    return stats


def render():
    """Render the settings page."""
    st.title("⚡ Settings")
    st.divider()

    # Tabs
    tab1, tab2, tab3 = st.tabs(["API Keys", "Database", "About"])

    with tab1:
        st.subheader("API Keys")

        st.info("API keys are stored securely in .env file. They are never displayed in full.")

        # Check for .env file
        env_path = Path(__file__).parent.parent.parent.parent / ".env"

        st.divider()

        # YouTube API Key
        st.subheader("YouTube Data API v3")

        col1, col2 = st.columns([3, 1])

        with col1:
            current_yt_key = os.getenv("YOUTUBE_API_KEY", "")

            # Show masked version if key exists
            if current_yt_key:
                masked_key = current_yt_key[:8] + "*" * (len(current_yt_key) - 12) + current_yt_key[-4:]
                st.text_input(
                    "Current API Key:",
                    value=masked_key,
                    disabled=True,
                    help="Your API key is securely stored"
                )

            # Input for new key
            new_yt_key = st.text_input(
                "Enter new YouTube API Key:",
                type="password",
                placeholder="AIza..." if not current_yt_key else "Leave empty to keep current key",
                help="Get your API key from https://console.cloud.google.com/"
            )

            if new_yt_key:
                if st.button("Save YouTube API Key", key="save_yt"):
                    if save_api_key("YOUTUBE_API_KEY", new_yt_key):
                        st.success("✅ YouTube API key saved! Restart the app to use it.")
                        st.rerun()

        with col2:
            st.write("")  # Spacing
            st.write("")  # Spacing
            if current_yt_key:
                if st.button("Test YouTube API", key="test_yt"):
                    with st.spinner("Testing connection..."):
                        success, message = test_youtube_api(current_yt_key)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
            else:
                st.info("No API key configured")

        st.divider()

        # Anthropic API Key
        st.subheader("Anthropic (Claude)")

        col1, col2 = st.columns([3, 1])

        with col1:
            current_anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")

            # Show masked version if key exists
            if current_anthropic_key:
                masked_key = current_anthropic_key[:10] + "*" * (len(current_anthropic_key) - 14) + current_anthropic_key[-4:]
                st.text_input(
                    "Current API Key:",
                    value=masked_key,
                    disabled=True,
                    help="Your API key is securely stored",
                    key="current_anthropic"
                )

            # Input for new key
            new_anthropic_key = st.text_input(
                "Enter new Anthropic API Key:",
                type="password",
                placeholder="sk-ant-..." if not current_anthropic_key else "Leave empty to keep current key",
                help="Get your API key from https://console.anthropic.com/",
                key="new_anthropic"
            )

            if new_anthropic_key:
                if st.button("Save Anthropic API Key", key="save_anthropic"):
                    if save_api_key("ANTHROPIC_API_KEY", new_anthropic_key):
                        st.success("✅ Anthropic API key saved! Restart the app to use it.")
                        st.rerun()

        with col2:
            st.write("")  # Spacing
            st.write("")  # Spacing
            if current_anthropic_key:
                if st.button("Test Anthropic API", key="test_anthropic"):
                    with st.spinner("Testing connection..."):
                        success, message = test_anthropic_api(current_anthropic_key)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
            else:
                st.info("No API key configured")

        st.divider()

        st.caption("⚠️ Restart the Streamlit app after changing API keys for changes to take effect")

    with tab2:
        st.subheader("Database Statistics")

        # Get stats
        stats = get_database_stats()

        # SQLite Database
        st.subheader("SQLite Database (content.db)")

        col1, col2, col3 = st.columns(3)

        if "size" in stats["sqlite"]:
            with col1:
                st.metric("Database Size", f"{stats['sqlite']['size']:.2f} MB")

            with col2:
                if "table_counts" in stats["sqlite"]:
                    total_records = sum(stats["sqlite"]["table_counts"].values())
                    st.metric("Total Records", f"{total_records:,}")

            with col3:
                if "table_counts" in stats["sqlite"]:
                    table_count = len([c for c in stats["sqlite"]["table_counts"].values() if c > 0])
                    st.metric("Active Tables", f"{table_count}/11")

            st.divider()

            # Table breakdown
            if "table_counts" in stats["sqlite"]:
                st.subheader("Table Record Counts")

                table_counts = stats["sqlite"]["table_counts"]

                col1, col2 = st.columns(2)

                with col1:
                    st.write("**Content Tables:**")
                    st.write(f"• Niches: {table_counts.get('niches', 0)}")
                    st.write(f"• Canon Sources: {table_counts.get('canon_sources', 0)}")
                    st.write(f"• Glossary Terms: {table_counts.get('glossary', 0)}")
                    st.write(f"• Competitor Channels: {table_counts.get('competitor_channels', 0)}")
                    st.write(f"• Competitor Videos: {table_counts.get('competitor_videos', 0)}")
                    st.write(f"• Performance Snapshots: {table_counts.get('performance_snapshots', 0)}")

                with col2:
                    st.write("**Production Tables:**")
                    st.write(f"• My Channels: {table_counts.get('my_channels', 0)}")
                    st.write(f"• My Videos: {table_counts.get('my_videos', 0)}")
                    st.write(f"• Assets: {table_counts.get('assets', 0)}")
                    st.write(f"• Thumbnails: {table_counts.get('thumbnails', 0)}")
                    st.write(f"• Tags: {table_counts.get('tags', 0)}")
        else:
            st.info("Database not yet created. Run database initialization scripts first.")

        st.divider()

        # LanceDB
        st.subheader("LanceDB (Vector Database)")

        if "tables" in stats["lancedb"]:
            col1, col2 = st.columns(2)

            with col1:
                st.metric("Vector Tables", len(stats["lancedb"]["tables"]))

            with col2:
                st.metric("Total Chunks", f"{stats['lancedb'].get('total_chunks', 0):,}")

            if stats["lancedb"]["tables"]:
                st.write("**Tables:**")
                for table in stats["lancedb"]["tables"]:
                    st.write(f"• {table['name']}: {table['count']:,} records")
        else:
            st.info("Vector database not yet populated. Run chunking scripts to add data.")

        st.divider()

        st.warning("🚧 Database backup/restore features coming in Phase 2")

    with tab3:
        st.subheader("About")

        col1, col2 = st.columns([1, 2])

        with col1:
            st.image("https://via.placeholder.com/150x150.png?text=CIS", width=150)

        with col2:
            st.markdown("### Content Intelligence System")
            st.markdown("**Version:** 0.1.0 (MVP)")
            st.markdown("**Status:** Development")
            st.caption("Local-first platform for researching, planning, and producing faceless YouTube content")

        st.divider()

        # Tech stack
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Tech Stack")
            st.write("**Database:**")
            st.write("• SQLite (structured data)")
            st.write("• LanceDB (vector search)")
            st.write("")
            st.write("**Backend:**")
            st.write("• Python 3.11+")
            st.write("• FastAPI (future)")
            st.write("")
            st.write("**AI/ML:**")
            st.write("• Claude 3.5 Sonnet (LLM)")
            st.write("• all-MiniLM-L6-v2 (embeddings)")

        with col2:
            st.subheader("Features")
            st.write("**Phase 1 (Current):**")
            st.write("✅ Competitor video tracking")
            st.write("✅ Canon source ingestion")
            st.write("✅ Glossary extraction")
            st.write("✅ Semantic search")
            st.write("✅ Vector embeddings")
            st.write("")
            st.write("**Phase 2 (Planned):**")
            st.write("⏳ Video ideation")
            st.write("⏳ Production pipeline")
            st.write("⏳ Asset management")
            st.write("⏳ Analytics tracking")

        st.divider()

        st.subheader("Documentation")

        docs = [
            ("System Overview", "docs/SYSTEM_OVERVIEW.md"),
            ("Data Model", "docs/DATA_MODEL.md"),
            ("Pipeline", "docs/PIPELINE.md"),
            ("UI Specification", "docs/UI_SPEC.md")
        ]

        cols = st.columns(2)
        for idx, (name, path) in enumerate(docs):
            with cols[idx % 2]:
                st.markdown(f"📄 [{name}]({path})")

        st.divider()

        st.subheader("Project Goal")
        st.info("""
        Build a system that helps create profitable faceless YouTube channels by:
        - Tracking competitor videos and identifying content gaps
        - Storing and searching source material (books, wikis, docs)
        - Cleaning auto-generated transcripts
        - Generating video ideas backed by data
        - Managing the production pipeline

        **Target:** £2-3k/month revenue within 12-18 months
        """)

        st.divider()

        st.caption("Built with ❤️ for content creators")
        st.caption("© 2026 Content Intelligence System")
