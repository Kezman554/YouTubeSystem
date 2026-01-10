"""
Home page - Dashboard overview.
"""

import streamlit as st
from src.database.niches import get_all_niches
from src.database.competitor_channels import get_channels_by_niche
from src.database.competitor_videos import get_videos_by_niche
from src.database.canon_sources import get_sources_by_niche
from src.database.glossary import get_glossary_by_niche
from src.pipeline.vectorstore import get_stats


def render():
    """Render the home page."""
    st.title("📊 Dashboard Overview")
    st.divider()

    # Get current niche filter
    current_niche = st.session_state.current_niche

    # Overall statistics
    st.subheader("System Statistics")

    # Get niches
    niches = get_all_niches()

    # Row 1: Main stats
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Niches",
            value=len(niches),
            help="Number of content niches configured"
        )

    # Calculate totals across all niches or current niche
    total_competitors = 0
    total_videos = 0
    total_sources = 0
    total_glossary = 0

    if current_niche:
        # Filter by current niche
        niches_to_count = [n for n in niches if n['id'] == current_niche]
    else:
        # Count all niches
        niches_to_count = niches

    for niche in niches_to_count:
        try:
            competitors = get_channels_by_niche(niche['id'])
            total_competitors += len(competitors)

            videos = get_videos_by_niche(niche['id'])
            total_videos += len(videos)

            sources = get_sources_by_niche(niche['id'])
            total_sources += len(sources)

            glossary = get_glossary_by_niche(niche['id'])
            total_glossary += len(glossary)
        except Exception:
            pass

    with col2:
        st.metric(
            label="Competitors Tracked",
            value=total_competitors,
            help="YouTube channels being monitored"
        )

    with col3:
        st.metric(
            label="Videos Scraped",
            value=f"{total_videos:,}",
            help="Competitor videos in database"
        )

    with col4:
        st.metric(
            label="Canon Sources",
            value=total_sources,
            help="Reference books/documents ingested"
        )

    st.divider()

    # Row 2: Content stats
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Glossary Terms",
            value=f"{total_glossary:,}",
            help="Canonical terms for transcript cleaning"
        )

    # Get vector database stats
    vector_stats = get_stats()
    total_chunks = vector_stats.get('total_chunks', 0)

    with col2:
        st.metric(
            label="Canon Chunks",
            value=f"{total_chunks:,}",
            help="Text chunks embedded for semantic search"
        )

    with col3:
        # Transcripts with content
        videos_with_transcripts = 0
        for niche in niches_to_count:
            try:
                videos = get_videos_by_niche(niche['id'])
                videos_with_transcripts += sum(1 for v in videos if v.get('has_transcript'))
            except Exception:
                pass

        st.metric(
            label="Transcripts",
            value=videos_with_transcripts,
            help="Videos with transcripts imported"
        )

    with col4:
        st.metric(
            label="My Videos",
            value="0",
            help="Videos in production pipeline (Phase 2)"
        )

    st.divider()

    # Niche breakdown
    if not current_niche and niches:
        st.subheader("Niche Breakdown")

        for niche in niches:
            with st.expander(f"📁 {niche['name']}", expanded=False):
                col1, col2, col3 = st.columns(3)

                try:
                    competitors = get_channels_by_niche(niche['id'])
                    videos = get_videos_by_niche(niche['id'])
                    sources = get_sources_by_niche(niche['id'])

                    with col1:
                        st.metric("Competitors", len(competitors))
                        st.metric("Videos", len(videos))

                    with col2:
                        st.metric("Canon Sources", len(sources))
                        ingested = sum(1 for s in sources if s.get('ingested'))
                        st.metric("Ingested", ingested)

                    with col3:
                        glossary = get_glossary_by_niche(niche['id'])
                        st.metric("Glossary Terms", len(glossary))
                        with_transcripts = sum(1 for v in videos if v.get('has_transcript'))
                        st.metric("Transcripts", with_transcripts)

                    # Show type and description
                    if niche.get('type'):
                        st.caption(f"Type: {niche['type']}")
                    if niche.get('description'):
                        st.caption(niche['description'])

                except Exception as e:
                    st.error(f"Error loading niche data: {e}")

    # Quick actions
    st.divider()
    st.subheader("Quick Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("⚙️ Set Up New Niche", use_container_width=True):
            st.session_state.current_page = "Niche Setup"
            st.rerun()

    with col2:
        if st.button("🔍 View Competitors", use_container_width=True):
            st.session_state.current_page = "Competitive Intel"
            st.rerun()

    with col3:
        if st.button("📚 Search Content", use_container_width=True):
            st.session_state.current_page = "Research"
            st.rerun()

    # Recent activity (placeholder)
    st.divider()
    st.subheader("Recent Activity")

    if total_videos == 0 and total_sources == 0:
        st.info("""
        👋 Welcome to the Content Intelligence System!

        Get started:
        1. **Create a niche** in Niche Setup
        2. **Add competitors** to track their videos
        3. **Add canon sources** (PDFs, books) for reference material
        4. **Search and analyze** content in Research

        Use the sidebar to navigate between sections.
        """)
    else:
        st.success("System is configured and ready to use!")

        # Show some stats
        if total_videos > 0:
            st.write(f"✓ Tracking {total_videos:,} competitor videos")
        if total_sources > 0:
            st.write(f"✓ {total_sources} canon sources available")
        if total_chunks > 0:
            st.write(f"✓ {total_chunks:,} text chunks indexed for search")
