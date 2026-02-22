"""
Production page - View and manage the active production context.

Shows the staged canon passages and transcript chunks that have been
pinned from Research and Competitive Intel pages, along with the
video topic and angle.
"""

import streamlit as st

from src.database.production_context import (
    get_production_context,
    update_production_topic,
    remove_canon_passage,
    remove_transcript_chunk,
    clear_production_context,
)


def _render_video_details(ctx: dict):
    """Render topic and angle inputs with auto-save on change."""
    st.subheader("Video Details")

    topic = st.text_input(
        "Topic",
        value=ctx.get("topic") or "",
        placeholder="e.g. The Fall of Númenor",
        key="prod_topic",
    )
    angle = st.text_input(
        "Angle",
        value=ctx.get("angle") or "",
        placeholder="e.g. Why Ar-Pharazôn was actually right",
        key="prod_angle",
    )

    stored_topic = ctx.get("topic") or ""
    stored_angle = ctx.get("angle") or ""

    if topic != stored_topic or angle != stored_angle:
        update_production_topic(topic, angle)
        st.caption("Saved.")


def _render_canon_passages(passages: list):
    """Render the canon passages section."""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"Canon Passages ({len(passages)})")
    with col2:
        if passages and st.button("Clear Section", key="clear_canon"):
            for p in passages:
                remove_canon_passage(p["id"])
            st.rerun()

    if not passages:
        st.info("No canon passages pinned yet. Use Research to find and add passages.")
        return

    for p in passages:
        # Build label
        parts = []
        if p.get("source_title"):
            parts.append(p["source_title"])
        if p.get("chapter"):
            parts.append(p["chapter"])
        if p.get("page"):
            parts.append(f"p.{p['page']}")
        label = " / ".join(parts) if parts else "Passage"

        # Authority badge
        if p.get("authority_score") is not None:
            label += f"  \u2014  Authority: {p['authority_score']:.0f}"

        preview = p["text"][:200] + ("..." if len(p["text"]) > 200 else "")

        with st.expander(f"{label}  \u2014  {preview}"):
            st.markdown(p["text"])
            if st.button("Remove", key=f"rm_canon_{p['id']}"):
                remove_canon_passage(p["id"])
                st.rerun()


def _render_transcript_chunks(chunks: list):
    """Render the competitor transcript chunks section."""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"Competitor Transcripts ({len(chunks)})")
    with col2:
        if chunks and st.button("Clear Section", key="clear_transcripts"):
            for c in chunks:
                remove_transcript_chunk(c["id"])
            st.rerun()

    if not chunks:
        st.info("No transcript chunks pinned yet. Use Competitive Intel to find and add chunks.")
        return

    st.caption("Use competitor transcripts for reference only — never copy directly.")

    # Auto-summary: deduplicate by video_id
    videos = {}
    for c in chunks:
        vid = c.get("video_id")
        if vid and vid not in videos:
            videos[vid] = c

    if videos:
        summary_lines = [f"From **{len(videos)} video{'s' if len(videos) != 1 else ''}:**"]
        for v in videos.values():
            title = v.get("video_title", "Unknown")
            channel = v.get("channel_name", "")
            views = v.get("view_count")
            line = f"- {title}"
            if channel:
                line += f" ({channel})"
            if views:
                line += f" — {views:,} views"
            summary_lines.append(line)
        st.markdown("\n".join(summary_lines))

    for c in chunks:
        title = c.get("video_title", "Transcript chunk")
        channel = c.get("channel_name", "")
        label = title
        if channel:
            label += f" — {channel}"

        preview = c["text"][:200] + ("..." if len(c["text"]) > 200 else "")

        with st.expander(f"{label}  \u2014  {preview}"):
            st.markdown(c["text"])
            if st.button("Remove", key=f"rm_chunk_{c['id']}"):
                remove_transcript_chunk(c["id"])
                st.rerun()


def render():
    """Render the Production page."""
    st.title("Production")
    st.caption("Manage the source material and details for your current video.")

    ctx = get_production_context()

    _render_video_details(ctx)

    st.divider()
    _render_canon_passages(ctx.get("canon_passages", []))

    st.divider()
    _render_transcript_chunks(ctx.get("transcript_chunks", []))

    # Footer: Clear All
    st.divider()
    total = len(ctx.get("canon_passages", [])) + len(ctx.get("transcript_chunks", []))
    if total > 0:
        if st.button("Clear All", type="primary"):
            clear_production_context()
            st.rerun()
