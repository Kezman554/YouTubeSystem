"""
Production page - View and manage the active production context.

Shows the staged canon passages and transcript chunks that have been
pinned from Research and Competitive Intel pages, along with the
video topic and angle.
"""

from collections import defaultdict

import streamlit as st

from src.database.production_context import (
    get_production_context,
    update_production_topic,
    remove_canon_passage,
    remove_transcript_chunk,
    clear_production_context,
)


def _find_boundary_overlap(text_a: str, text_b: str, min_overlap: int = 20) -> int:
    """
    Find the longest suffix of text_a that matches a prefix of text_b.

    Checks all possible overlap lengths from longest to shortest, returning
    the first (longest) match found. Returns 0 if no overlap of at least
    min_overlap characters exists.

    Args:
        text_a: The preceding text.
        text_b: The following text.
        min_overlap: Minimum number of characters to consider a valid overlap.

    Returns:
        Length of the overlapping substring, or 0 if none found.
    """
    max_possible = min(len(text_a), len(text_b))
    for length in range(max_possible, min_overlap - 1, -1):
        if text_a.endswith(text_b[:length]):
            return length
    return 0


def _merge_adjacent_texts(texts: list[str], min_overlap: int = 20) -> list[str]:
    """
    Merge a sorted list of text strings, removing boundary overlaps.

    Walks the list pairwise. When an overlap is found between the end of one
    text and the start of the next, the two are merged into one with the
    duplicate removed. Non-overlapping texts are kept separate.

    Args:
        texts: Ordered list of text strings to merge.
        min_overlap: Minimum characters for an overlap to count.

    Returns:
        New list with overlapping adjacent texts merged.
    """
    if not texts:
        return []

    merged = [texts[0]]
    for text in texts[1:]:
        overlap = _find_boundary_overlap(merged[-1], text, min_overlap)
        if overlap > 0:
            merged[-1] = merged[-1] + text[overlap:]
        else:
            merged.append(text)
    return merged


def format_export(ctx: dict) -> str:
    """
    Format the full production context as structured text for export.

    Groups canon passages by source_title, sorted by chapter then page within
    each source. Groups transcript chunks by video_id, sorted by chunk_index
    within each video. Includes headers and attribution throughout.

    Args:
        ctx: The dict returned by get_production_context().

    Returns:
        Formatted plain-text string ready for clipboard or file export.
    """
    lines: list[str] = []

    # Header
    topic = ctx.get("topic") or "Untitled"
    angle = ctx.get("angle") or ""
    lines.append(f"# {topic}")
    if angle:
        lines.append(f"Angle: {angle}")
    lines.append("")

    # --- Canon passages grouped by source_title ---
    passages = ctx.get("canon_passages", [])
    any_merged = False
    if passages:
        lines.append("## Canon Sources")
        lines.append("")

        by_source: dict[str, list[dict]] = defaultdict(list)
        for p in passages:
            key = p.get("source_title") or "Unknown Source"
            by_source[key].append(p)

        for source_title in sorted(by_source):
            group = by_source[source_title]
            # Sort by chapter (string, None-safe) then page (int, None-safe)
            group.sort(key=lambda p: (p.get("chapter") or "", p.get("page") or 0))

            # Merge overlapping adjacent passages
            raw_texts = [p["text"] for p in group]
            merged_texts = _merge_adjacent_texts(raw_texts)
            if len(merged_texts) < len(raw_texts):
                any_merged = True

            lines.append(f"### {source_title}")
            lines.append("")

            # Build location lines from the first passage of each merged run
            text_idx = 0
            for merged_text in merged_texts:
                # Find all original passages that were merged into this text
                span_start = text_idx
                consumed = 0
                while text_idx < len(group) and consumed < len(merged_text):
                    consumed += len(group[text_idx]["text"])
                    text_idx += 1

                # Use the first passage in the span for the location line
                p = group[span_start]
                loc_parts = []
                if p.get("chapter"):
                    loc_parts.append(p["chapter"])
                if p.get("page"):
                    loc_parts.append(f"p.{p['page']}")
                if p.get("authority_score") is not None:
                    loc_parts.append(f"authority {p['authority_score']:.0f}")
                # If span covers multiple passages, note the range
                end_p = group[text_idx - 1]
                if end_p.get("page") and end_p["page"] != (p.get("page") or 0):
                    loc_parts.append(f"to p.{end_p['page']}")
                if loc_parts:
                    lines.append(f"[{' | '.join(loc_parts)}]")

                lines.append(merged_text)
                lines.append("")

    # --- Transcript chunks grouped by video_id ---
    chunks = ctx.get("transcript_chunks", [])
    if chunks:
        lines.append("## Competitor Transcripts")
        lines.append("(Reference only — do not copy directly)")
        lines.append("")

        by_video: dict[str, list[dict]] = defaultdict(list)
        for c in chunks:
            # Use video_id as key; fall back to video_title for ungrouped chunks
            key = str(c.get("video_id") or c.get("video_title") or "unknown")
            by_video[key].append(c)

        for key in sorted(by_video):
            group = by_video[key]
            group.sort(key=lambda c: c.get("chunk_index") or 0)

            # Build header from first chunk's metadata
            first = group[0]
            title = first.get("video_title") or "Unknown Video"
            channel = first.get("channel_name") or ""
            views = first.get("view_count")

            header = f"### {title}"
            attr_parts = []
            if channel:
                attr_parts.append(channel)
            if views:
                attr_parts.append(f"{views:,} views")
            if attr_parts:
                header += f" ({' | '.join(attr_parts)})"

            lines.append(header)
            lines.append("")

            # Merge overlapping adjacent chunks
            raw_texts = [c["text"] for c in group]
            merged_texts = _merge_adjacent_texts(raw_texts)
            if len(merged_texts) < len(raw_texts):
                any_merged = True

            for text in merged_texts:
                lines.append(text)
                lines.append("")

    if any_merged:
        lines.append("Note: Adjacent passages auto-merged. Occasional overlap may remain at boundaries.")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


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
