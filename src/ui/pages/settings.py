"""
Settings page - Configure system settings and API keys.
"""

import streamlit as st
from pathlib import Path


def render():
    """Render the settings page."""
    st.title("⚡ Settings")
    st.divider()

    # Tabs
    tab1, tab2, tab3 = st.tabs(["API Keys", "Database", "About"])

    with tab1:
        st.subheader("API Keys")

        st.info("API keys are stored in .env file in the project root")

        # Check for .env file
        env_path = Path(__file__).parent.parent.parent.parent / ".env"

        if env_path.exists():
            st.success(".env file found")
        else:
            st.warning(".env file not found")
            st.write("Create a .env file in the project root with:")
            st.code("""
ANTHROPIC_API_KEY=your_key_here
YOUTUBE_API_KEY=your_key_here
            """)

        st.divider()

        st.caption("API keys configuration is managed via .env file")
        st.caption("Restart the app after changing API keys")

    with tab2:
        st.subheader("Database")

        # Database paths
        db_path = Path(__file__).parent.parent.parent.parent / "data" / "content.db"
        vector_path = Path(__file__).parent.parent.parent.parent / "data" / "vectors"

        col1, col2 = st.columns(2)

        with col1:
            st.metric("SQLite Database", "content.db")
            if db_path.exists():
                size = db_path.stat().st_size / (1024 * 1024)  # MB
                st.caption(f"Size: {size:.2f} MB")
                st.caption(f"Location: {db_path}")
            else:
                st.caption("Not created yet")

        with col2:
            st.metric("Vector Database", "LanceDB")
            if vector_path.exists():
                st.caption(f"Location: {vector_path}")
            else:
                st.caption("Not created yet")

        st.divider()

        st.warning("Database backup/restore features coming soon")

    with tab3:
        st.subheader("About")

        st.write("**Content Intelligence System**")
        st.write("Version: 0.1.0 (MVP)")
        st.divider()

        st.write("**Tech Stack:**")
        st.write("- Database: SQLite + LanceDB")
        st.write("- Backend: Python + FastAPI")
        st.write("- UI: Streamlit")
        st.write("- Embeddings: all-MiniLM-L6-v2")
        st.write("- LLM: Claude (Anthropic)")

        st.divider()

        st.write("**Documentation:**")
        st.write("- [System Overview](../../../docs/SYSTEM_OVERVIEW.md)")
        st.write("- [Data Model](../../../docs/DATA_MODEL.md)")
        st.write("- [Pipeline](../../../docs/PIPELINE.md)")
        st.write("- [UI Spec](../../../docs/UI_SPEC.md)")
