"""
Competitive Intel page - Analyze competitor videos, topics, and channels.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import json

from src.database.niches import get_niche
from src.database.competitor_channels import (
    get_channels_by_niche, get_competitor_channel, create_competitor_channel,
    mark_as_scraped
)
from src.database.competitor_videos import (
    get_videos_by_niche, get_videos_by_channel, get_competitor_video,
    update_competitor_video
)


def render_videos_tab(niche_id: int):
    """Render the Videos tab with filtering, sorting, and transcript import."""
    st.subheader("Competitor Videos")

    # Get all videos for the niche
    all_videos = get_videos_by_niche(niche_id)

    if not all_videos:
        st.info("No videos scraped yet. Add competitors in the Competitors tab and scrape their channels.")
        return

    # Get channels for filter dropdown
    channels = get_channels_by_niche(niche_id)
    channel_map = {ch['id']: ch['name'] for ch in channels}

    # Filters
    st.subheader("Filters")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        channel_filter = st.selectbox(
            "Channel",
            options=["All"] + list(channel_map.values()),
            key="video_channel_filter"
        )

    with col2:
        # Date range filter
        date_filter = st.selectbox(
            "Date Range",
            ["All time", "Last 7 days", "Last 30 days", "Last 90 days", "Last year"],
            key="video_date_filter"
        )

    with col3:
        # Min views filter
        min_views = st.number_input(
            "Min Views",
            min_value=0,
            value=0,
            step=1000,
            key="video_min_views"
        )

    with col4:
        # Transcript filter
        transcript_filter = st.checkbox(
            "Missing transcripts only",
            key="video_transcript_filter"
        )

    # Apply filters
    filtered_videos = all_videos.copy()

    # Channel filter
    if channel_filter != "All":
        channel_id = [k for k, v in channel_map.items() if v == channel_filter][0]
        filtered_videos = [v for v in filtered_videos if v['channel_id'] == channel_id]

    # Date filter
    if date_filter != "All time":
        now = datetime.now()
        if date_filter == "Last 7 days":
            cutoff = now - timedelta(days=7)
        elif date_filter == "Last 30 days":
            cutoff = now - timedelta(days=30)
        elif date_filter == "Last 90 days":
            cutoff = now - timedelta(days=90)
        else:  # Last year
            cutoff = now - timedelta(days=365)

        filtered_videos = [
            v for v in filtered_videos
            if v['published_at'] and datetime.fromisoformat(v['published_at'].replace('Z', '+00:00')) >= cutoff
        ]

    # Min views filter
    if min_views > 0:
        filtered_videos = [v for v in filtered_videos if (v['view_count'] or 0) >= min_views]

    # Transcript filter
    if transcript_filter:
        filtered_videos = [v for v in filtered_videos if not v['has_transcript']]

    st.divider()

    # Sort options
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"Videos ({len(filtered_videos)})")
    with col2:
        sort_by = st.selectbox(
            "Sort by",
            ["Date (newest)", "Date (oldest)", "Views (high)", "Views (low)", "Title (A-Z)", "Title (Z-A)"],
            key="video_sort"
        )

    # Apply sorting
    if sort_by == "Date (newest)":
        filtered_videos.sort(key=lambda x: x['published_at'] or "", reverse=True)
    elif sort_by == "Date (oldest)":
        filtered_videos.sort(key=lambda x: x['published_at'] or "")
    elif sort_by == "Views (high)":
        filtered_videos.sort(key=lambda x: x['view_count'] or 0, reverse=True)
    elif sort_by == "Views (low)":
        filtered_videos.sort(key=lambda x: x['view_count'] or 0)
    elif sort_by == "Title (A-Z)":
        filtered_videos.sort(key=lambda x: x['title'])
    elif sort_by == "Title (Z-A)":
        filtered_videos.sort(key=lambda x: x['title'], reverse=True)

    # Display videos in a table with expandable rows
    for video in filtered_videos:
        channel_name = channel_map.get(video['channel_id'], "Unknown")

        # Format date
        if video['published_at']:
            try:
                pub_date = datetime.fromisoformat(video['published_at'].replace('Z', '+00:00'))
                date_str = pub_date.strftime("%Y-%m-%d")
            except:
                date_str = video['published_at'][:10] if video['published_at'] else "Unknown"
        else:
            date_str = "Unknown"

        # Format views
        views_str = f"{video['view_count']:,}" if video['view_count'] else "N/A"

        # Transcript status
        transcript_icon = "✅" if video['has_transcript'] else "❌"

        # Create expander with video info
        with st.expander(f"{transcript_icon} {video['title'][:80]}... | {channel_name} | {views_str} views | {date_str}"):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.write(f"**Title:** {video['title']}")
                st.write(f"**Channel:** {channel_name}")
                st.write(f"**Published:** {date_str}")
                st.write(f"**Views:** {views_str}")
                st.write(f"**Video ID:** `{video['youtube_id']}`")

                # YouTube link
                youtube_url = f"https://www.youtube.com/watch?v={video['youtube_id']}"
                st.markdown(f"[🔗 Watch on YouTube]({youtube_url})")

                # Copy video ID button
                if st.button("📋 Copy Video ID", key=f"copy_{video['id']}"):
                    st.code(video['youtube_id'])
                    st.info("Video ID displayed above. Copy it manually.")

            with col2:
                st.metric("Likes", f"{video['like_count']:,}" if video['like_count'] else "N/A")
                st.metric("Comments", f"{video['comment_count']:,}" if video['comment_count'] else "N/A")
                st.metric("Duration", f"{video['duration_seconds'] // 60}m {video['duration_seconds'] % 60}s" if video['duration_seconds'] else "N/A")

            # Transcript section
            st.divider()
            st.write("**Transcript**")

            if video['has_transcript']:
                st.success("✅ Transcript available")

                # Option to view/edit transcript
                if st.checkbox("View/Edit Transcript", key=f"view_transcript_{video['id']}"):
                    # Fetch full video details to get transcript
                    video_full = get_competitor_video(video['id'])
                    transcript_text = video_full.get('transcript', '')

                    edited_transcript = st.text_area(
                        "Transcript",
                        value=transcript_text,
                        height=300,
                        key=f"edit_transcript_{video['id']}"
                    )

                    if st.button("Update Transcript", key=f"update_transcript_{video['id']}"):
                        update_competitor_video(video['id'], transcript=edited_transcript, has_transcript=True)
                        st.success("Transcript updated!")
                        st.rerun()
            else:
                st.warning("❌ No transcript yet")

                # Manual transcript input
                transcript_input = st.text_area(
                    "Paste transcript here",
                    height=300,
                    placeholder="Paste the video transcript here...",
                    key=f"transcript_input_{video['id']}"
                )

                if st.button("💾 Save Transcript", key=f"save_transcript_{video['id']}"):
                    if transcript_input.strip():
                        update_competitor_video(
                            video['id'],
                            transcript=transcript_input.strip(),
                            has_transcript=True
                        )
                        st.success("✅ Transcript saved!")
                        st.rerun()
                    else:
                        st.error("Please enter a transcript before saving.")


def render_topics_tab(niche_id: int):
    """Render the Topics tab with aggregate topic analysis."""
    st.subheader("Topic Analysis")

    # Get all videos for the niche
    all_videos = get_videos_by_niche(niche_id)

    if not all_videos:
        st.info("No videos scraped yet. Add competitors and scrape their channels first.")
        return

    # Parse topic tags from videos
    topic_counts = {}
    videos_with_topics = 0

    for video in all_videos:
        if video['topic_tags']:
            try:
                topics = json.loads(video['topic_tags'])
                videos_with_topics += 1
                for topic in topics:
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1
            except json.JSONDecodeError:
                continue

    if not topic_counts:
        st.warning("No topic tags found. Topic extraction is a Phase 2 feature.")
        st.info("""
        **How topic extraction will work:**
        - Analyze video titles and descriptions
        - Extract key themes using NLP
        - Track trending topics over time
        - Identify content gaps
        """)
        return

    # Display topic statistics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Videos", len(all_videos))

    with col2:
        st.metric("Videos with Topics", videos_with_topics)

    with col3:
        st.metric("Unique Topics", len(topic_counts))

    st.divider()

    # Sort topics by frequency
    sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)

    # Display as a table
    st.subheader("Top Topics")

    df_data = []
    for topic, count in sorted_topics[:50]:  # Top 50
        percentage = (count / len(all_videos)) * 100
        df_data.append({
            "Topic": topic,
            "Video Count": count,
            "Coverage": f"{percentage:.1f}%"
        })

    if df_data:
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.divider()

    # Timeline view (placeholder)
    st.subheader("Topic Trends Over Time")
    st.info("📊 Topic timeline visualization coming in Phase 2")


def render_gaps_tab(niche_id: int):
    """Render the Gaps tab for gap analysis."""
    st.subheader("Content Gap Analysis")

    st.info("🚧 Gap analysis feature coming in Phase 2")

    st.markdown("""
    **Planned Gap Analysis Features:**

    1. **Topic Gaps**
       - Identify topics your competitors haven't covered
       - Find underserved topics with high search volume
       - Suggest new video ideas based on gaps

    2. **Performance Gaps**
       - Identify low-performing topics that could be improved
       - Find topics where competitors are weak
       - Suggest remake opportunities

    3. **Trend Gaps**
       - Detect emerging trends before competitors
       - Identify seasonal content opportunities
       - Track topic momentum over time

    4. **Canon Gaps**
       - Compare competitor topics vs your canon sources
       - Find canon material that hasn't been covered by competitors
       - Suggest unique angles from your research
    """)


def render_competitors_tab(niche_id: int):
    """Render the Competitors management tab."""
    st.subheader("Manage Competitor Channels")

    # Get existing channels
    channels = get_channels_by_niche(niche_id)

    # Add new channel section
    with st.expander("➕ Add New Competitor Channel", expanded=False):
        with st.form("add_competitor_form"):
            st.write("Add a new competitor channel to track")

            col1, col2 = st.columns(2)

            with col1:
                channel_input = st.text_input(
                    "Channel URL or ID*",
                    placeholder="https://youtube.com/@channel or UCxxxxxxx",
                    help="Enter a YouTube channel URL or channel ID"
                )

                channel_name = st.text_input(
                    "Channel Name*",
                    placeholder="e.g., Nerd of the Rings"
                )

            with col2:
                max_videos = st.selectbox(
                    "Max Videos to Scrape",
                    options=[50, 100, 200, 500, "All"],
                    index=1  # Default to 100
                )

                sort_by = st.selectbox(
                    "Sort By",
                    options=["Most recent", "Most viewed"],
                    help="Order videos by date or popularity"
                )

            submitted = st.form_submit_button("Add Channel")

            if submitted:
                if not channel_input or not channel_name:
                    st.error("Please provide both channel URL/ID and channel name.")
                else:
                    # Extract channel ID from input
                    # This is a simplified version - the actual scraper has more robust extraction
                    if channel_input.startswith("UC") and len(channel_input) == 24:
                        youtube_id = channel_input
                    elif "@" in channel_input:
                        st.warning("⚠️ Handle format detected. You'll need to convert this to a channel ID first.")
                        youtube_id = None
                    else:
                        youtube_id = channel_input.split("/")[-1] if "/" in channel_input else channel_input

                    if youtube_id:
                        try:
                            channel_id = create_competitor_channel(
                                niche_id=niche_id,
                                youtube_id=youtube_id,
                                name=channel_name,
                                url=channel_input if channel_input.startswith("http") else None
                            )
                            st.success(f"✅ Channel '{channel_name}' added! Now run the scraper to fetch videos.")

                            # Show command to run
                            max_str = "all" if max_videos == "All" else str(max_videos)
                            sort_str = "date" if sort_by == "Most recent" else "views"

                            st.code(f"python scripts/scrape_channel.py {youtube_id} {niche_id} --max {max_str} --sort {sort_str}")

                            st.rerun()
                        except Exception as e:
                            st.error(f"Error adding channel: {e}")

    st.divider()

    # List existing channels
    if channels:
        st.subheader(f"Tracked Channels ({len(channels)})")

        for channel in channels:
            with st.expander(f"📺 {channel['name']} ({channel['subscriber_count']:,} subs)" if channel['subscriber_count'] else f"📺 {channel['name']}"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.write(f"**YouTube ID:** `{channel['youtube_id']}`")
                    st.write(f"**Subscribers:** {channel['subscriber_count']:,}" if channel['subscriber_count'] else "**Subscribers:** N/A")
                    st.write(f"**Total Videos:** {channel['video_count']:,}" if channel['video_count'] else "**Total Videos:** N/A")

                with col2:
                    st.write(f"**Style:** {channel['style']}" if channel['style'] else "**Style:** N/A")
                    st.write(f"**Quality:** {channel['quality_tier']}" if channel['quality_tier'] else "**Quality:** N/A")
                    st.write(f"**Active:** {'✅' if channel['is_active'] else '❌'}")

                with col3:
                    last_scraped = channel['last_scraped']
                    if last_scraped:
                        try:
                            scraped_date = datetime.fromisoformat(last_scraped.replace('Z', '+00:00'))
                            st.write(f"**Last Scraped:** {scraped_date.strftime('%Y-%m-%d %H:%M')}")
                        except:
                            st.write(f"**Last Scraped:** {last_scraped}")
                    else:
                        st.write("**Last Scraped:** Never")

                    # Get video count for this channel
                    channel_videos = get_videos_by_channel(channel['id'])
                    st.write(f"**Scraped Videos:** {len(channel_videos)}")

                st.divider()

                # Re-scrape options
                st.write("**Re-scrape Channel**")

                col1, col2, col3 = st.columns(3)

                with col1:
                    rescrape_max = st.selectbox(
                        "Max Videos",
                        options=[50, 100, 200, 500, "All"],
                        index=1,
                        key=f"rescrape_max_{channel['id']}"
                    )

                with col2:
                    rescrape_sort = st.selectbox(
                        "Sort By",
                        options=["Most recent", "Most viewed"],
                        key=f"rescrape_sort_{channel['id']}"
                    )

                with col3:
                    st.write("")  # Spacing
                    st.write("")  # Spacing
                    if st.button("🔄 Re-scrape", key=f"rescrape_{channel['id']}"):
                        max_str = "all" if rescrape_max == "All" else str(rescrape_max)
                        sort_str = "date" if rescrape_sort == "Most recent" else "views"

                        st.info("Run this command to re-scrape:")
                        st.code(f"python scripts/scrape_channel.py {channel['youtube_id']} {niche_id} --max {max_str} --sort {sort_str}")
    else:
        st.info("No competitor channels added yet. Use the form above to add your first competitor.")


def render():
    """Render the Competitive Intel page."""
    st.title("🔍 Competitive Intelligence")

    # Check if niche is selected
    if not st.session_state.get('current_niche'):
        st.warning("⚠️ Please select a niche from the sidebar first.")
        return

    niche_id = st.session_state.current_niche
    niche = get_niche(niche_id)

    if not niche:
        st.error("Selected niche not found.")
        return

    st.caption(f"Analyzing: **{niche['name']}**")
    st.divider()

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📹 Videos", "🏷️ Topics", "🔍 Gaps", "📺 Competitors"])

    with tab1:
        render_videos_tab(niche_id)

    with tab2:
        render_topics_tab(niche_id)

    with tab3:
        render_gaps_tab(niche_id)

    with tab4:
        render_competitors_tab(niche_id)
