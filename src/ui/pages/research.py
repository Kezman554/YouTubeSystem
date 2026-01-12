"""
Research page - Semantic search across canon sources and transcripts.
"""

import streamlit as st
from typing import List, Dict, Any

from src.pipeline.search import search_canon, search_transcripts, search_both
from src.database.niches import get_all_niches
from src.database.canon_sources import get_canon_source
from src.database.competitor_videos import get_competitor_video
from src.database.competitor_channels import get_competitor_channel


def calculate_relevance_percentage(distance: float) -> float:
    """
    Convert distance to relevance percentage.

    Distance is typically 0-2 range (cosine distance).
    Lower distance = higher relevance.
    """
    # Convert distance to similarity (0-1 range)
    similarity = max(0, 1 - (distance / 2))
    return similarity * 100


def render_canon_result(result: Dict[str, Any], index: int):
    """Render a single canon search result as a card."""

    # Calculate relevance
    distance = result.get('_distance', 1.0)
    relevance = calculate_relevance_percentage(distance)

    # Get source attribution
    source_id = result.get('source_id')
    source_title = "Unknown Source"
    source_author = None

    if source_id:
        source = get_canon_source(source_id)
        if source:
            source_title = source.get('title', 'Unknown Source')
            source_author = source.get('author')

    # Build attribution string
    attribution = source_title
    if source_author:
        attribution += f" by {source_author}"

    chapter = result.get('chapter')
    if chapter:
        attribution += f" - {chapter}"

    page = result.get('page')
    if page:
        attribution += f" (p. {page})"

    # Get text
    text = result.get('text', '')

    # Display as card
    with st.container():
        st.markdown(f"### 📖 Canon Result #{index + 1}")

        col1, col2 = st.columns([3, 1])

        with col1:
            st.caption(attribution)

        with col2:
            # Relevance badge
            color = "🟢" if relevance >= 75 else "🟡" if relevance >= 50 else "🔴"
            st.metric("Relevance", f"{color} {relevance:.1f}%")

        # Text snippet (expandable)
        preview = text[:300].replace('\n', ' ').strip()
        if len(text) > 300:
            preview += "..."

        with st.expander(f"**Preview:** {preview}", expanded=False):
            st.write(text)

            # Copy button
            if st.button("📋 Copy Full Text", key=f"copy_canon_{index}_{source_id}"):
                st.code(text)
                st.info("Text displayed above - copy it manually.")

        st.divider()


def render_transcript_result(result: Dict[str, Any], index: int):
    """Render a single transcript search result as a card."""

    # Calculate relevance
    distance = result.get('_distance', 1.0)
    relevance = calculate_relevance_percentage(distance)

    # Get video and channel info
    video_id = result.get('video_id')
    channel_id = result.get('channel_id')

    video_title = result.get('video_title', 'Unknown Video')
    channel_name = result.get('channel_name', 'Unknown Channel')

    # Try to get more info from database if IDs are available
    if video_id:
        video = get_competitor_video(video_id)
        if video:
            video_title = video.get('title', video_title)
            youtube_id = video.get('youtube_id')

    if channel_id:
        channel = get_competitor_channel(channel_id)
        if channel:
            channel_name = channel.get('name', channel_name)

    # Build attribution
    attribution = f"{channel_name} - {video_title}"

    # Timestamp
    timestamp_start = result.get('timestamp_start')
    if timestamp_start:
        mins = int(timestamp_start // 60)
        secs = int(timestamp_start % 60)
        attribution += f" @ {mins}:{secs:02d}"

    # View count
    view_count = result.get('view_count')
    if view_count:
        attribution += f" ({view_count:,} views)"

    # Get text
    text = result.get('text', '')

    # Display as card
    with st.container():
        st.markdown(f"### 🎥 Transcript Result #{index + 1}")

        col1, col2 = st.columns([3, 1])

        with col1:
            st.caption(attribution)
            # YouTube link if available
            if video_id and 'youtube_id' in locals():
                youtube_url = f"https://www.youtube.com/watch?v={youtube_id}"
                if timestamp_start:
                    youtube_url += f"&t={int(timestamp_start)}s"
                st.markdown(f"[🔗 Watch on YouTube]({youtube_url})")

        with col2:
            # Relevance badge
            color = "🟢" if relevance >= 75 else "🟡" if relevance >= 50 else "🔴"
            st.metric("Relevance", f"{color} {relevance:.1f}%")

        # Text snippet (expandable)
        preview = text[:300].replace('\n', ' ').strip()
        if len(text) > 300:
            preview += "..."

        with st.expander(f"**Preview:** {preview}", expanded=False):
            st.write(text)

            # Copy button
            if st.button("📋 Copy Full Text", key=f"copy_transcript_{index}_{video_id}"):
                st.code(text)
                st.info("Text displayed above - copy it manually.")

        st.divider()


def render():
    """Render the research page."""
    st.title("📚 Research")
    st.caption("Semantic search across your knowledge base")

    st.divider()

    # Search bar
    st.subheader("Search")

    query = st.text_input(
        "Enter your research query",
        placeholder="e.g., How did Gandalf defeat the Balrog?",
        label_visibility="collapsed",
        key="research_query"
    )

    # Search options
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        # Source type toggle
        search_type = st.radio(
            "Search in:",
            options=["Both", "Canon Only", "Transcripts Only"],
            horizontal=True,
            key="search_type"
        )

    with col2:
        # Niche filter
        niches = get_all_niches()
        niche_options = ["All Niches"] + [n['name'] for n in niches]
        niche_names_to_ids = {n['name']: n['id'] for n in niches}

        selected_niche_name = st.selectbox(
            "Filter by niche:",
            options=niche_options,
            key="research_niche_filter"
        )

        # Get niche ID
        if selected_niche_name == "All Niches":
            filter_niche_id = None
        else:
            filter_niche_id = niche_names_to_ids.get(selected_niche_name)

    with col3:
        # Number of results
        results_per_page = st.number_input(
            "Results per source:",
            min_value=5,
            max_value=50,
            value=10,
            step=5,
            key="results_limit"
        )

    # Search button
    if st.button("🔍 Search", type="primary", use_container_width=True):
        if not query.strip():
            st.warning("Please enter a search query.")
        else:
            # Store search in session state
            st.session_state.last_query = query
            st.session_state.last_search_type = search_type
            st.session_state.last_niche_id = filter_niche_id
            st.session_state.last_results_limit = results_per_page
            st.session_state.search_performed = True

    st.divider()

    # Display results
    if st.session_state.get('search_performed', False):
        query = st.session_state.get('last_query', '')
        search_type = st.session_state.get('last_search_type', 'Both')
        filter_niche_id = st.session_state.get('last_niche_id')
        results_per_page = st.session_state.get('last_results_limit', 10)

        st.subheader("Search Results")
        st.caption(f"Query: \"{query}\"")

        with st.spinner("Searching..."):
            try:
                # Perform search based on type
                if search_type == "Both":
                    results = search_both(
                        query,
                        niche_id=filter_niche_id,
                        canon_limit=results_per_page,
                        transcript_limit=results_per_page
                    )
                    canon_results = results.get('canon', [])
                    transcript_results = results.get('transcripts', [])

                elif search_type == "Canon Only":
                    canon_results = search_canon(
                        query,
                        niche_id=filter_niche_id,
                        limit=results_per_page
                    )
                    transcript_results = []

                else:  # Transcripts Only
                    canon_results = []
                    transcript_results = search_transcripts(
                        query,
                        niche_id=filter_niche_id,
                        limit=results_per_page
                    )

                # Display results count
                total_results = len(canon_results) + len(transcript_results)

                if total_results == 0:
                    st.info("No results found. Try a different query or check if your data has been ingested and indexed.")

                    # Helpful tips
                    st.write("**Tips:**")
                    st.write("- Make sure you've ingested canon sources (PDFs)")
                    st.write("- Ensure transcripts have been imported")
                    st.write("- Run the chunking and embedding pipeline")
                    st.write("- Try broader search terms")
                else:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Results", total_results)
                    with col2:
                        st.metric("Canon Passages", len(canon_results))
                    with col3:
                        st.metric("Transcript Chunks", len(transcript_results))

                    st.divider()

                    # Display canon results
                    if canon_results:
                        st.markdown("## 📖 Canon Sources")
                        for idx, result in enumerate(canon_results):
                            render_canon_result(result, idx)

                    # Display transcript results
                    if transcript_results:
                        st.markdown("## 🎥 Video Transcripts")
                        for idx, result in enumerate(transcript_results):
                            render_transcript_result(result, idx)

                    # Load more button (pagination placeholder)
                    if total_results >= results_per_page:
                        st.info(f"💡 Showing top {results_per_page} results per source. Adjust 'Results per source' above to see more.")

            except Exception as e:
                st.error(f"Search failed: {str(e)}")
                st.write("**Error details:**")
                st.code(str(e))

                st.write("**Troubleshooting:**")
                st.write("1. Ensure the vector database exists (run ingestion and chunking scripts)")
                st.write("2. Check that the embedding model is loaded correctly")
                st.write("3. Verify that LanceDB tables have been created")
    else:
        # Welcome message
        st.info("👆 Enter a search query above to find relevant passages from your canon sources and video transcripts.")

        st.markdown("""
        **How to use:**
        1. **Enter a question or topic** in the search bar
        2. **Choose where to search**: canon sources, transcripts, or both
        3. **Filter by niche** or search across all niches
        4. **Click Search** to find semantically similar content

        **Examples:**
        - "How did Gandalf defeat the Balrog?"
        - "What is the significance of the One Ring?"
        - "Explain the relationship between Sauron and Morgoth"
        - "Who are the Istari?"

        **Note:** Results are ranked by semantic similarity, not keyword matching.
        """)
