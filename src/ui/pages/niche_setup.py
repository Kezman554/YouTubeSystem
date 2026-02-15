"""
Niche Setup page - Configure niches, sources, competitors, glossary.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import os

from src.database.niches import (
    get_all_niches, create_niche, update_niche, delete_niche, get_niche
)
from src.database.canon_sources import (
    get_sources_by_niche, create_canon_source, update_canon_source,
    delete_canon_source, mark_as_ingested
)
from src.database.competitor_channels import (
    get_channels_by_niche, create_competitor_channel, update_competitor_channel,
    delete_competitor_channel, mark_as_scraped, get_competitor_channel_by_youtube_id
)
from src.pipeline.ingest import extract_pdf
from src.pipeline.chunk import chunk_with_metadata
from src.pipeline.embed import embed_batch
from src.pipeline.vectorstore import get_db, store_canon_chunks
from src.database.glossary import (
    get_glossary_by_niche, create_glossary_entry, delete_glossary_entry,
    update_glossary_entry
)


def render_niches_tab():
    """Render the Niches tab."""
    st.subheader("Manage Niches")

    # Get all niches
    niches = get_all_niches()

    # Add new niche section
    with st.expander("➕ Add New Niche", expanded=False):
        with st.form("add_niche_form"):
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("Name*", placeholder="e.g., Middle-earth")
                slug = st.text_input("Slug*", placeholder="e.g., middle-earth")

            with col2:
                niche_type = st.selectbox(
                    "Type",
                    ["", "fiction", "crypto", "food", "tech", "gaming", "history", "other"]
                )
                description = st.text_area("Description", placeholder="Brief description of this niche")

            submitted = st.form_submit_button("Create Niche")

            if submitted:
                if not name or not slug:
                    st.error("Name and slug are required")
                else:
                    try:
                        niche_id = create_niche(
                            name=name,
                            slug=slug,
                            niche_type=niche_type if niche_type else None,
                            description=description if description else None
                        )
                        st.success(f"✅ Created niche: {name} (ID: {niche_id})")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error creating niche: {e}")

    st.divider()

    # List existing niches
    if not niches:
        st.info("No niches created yet. Add one above to get started!")
    else:
        st.write(f"**Total Niches:** {len(niches)}")

        for niche in niches:
            with st.expander(f"📁 {niche['name']}", expanded=False):
                # Display info
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.write(f"**ID:** {niche['id']}")
                    st.write(f"**Slug:** {niche['slug']}")
                    st.write(f"**Type:** {niche['type'] or 'Not set'}")
                    if niche['description']:
                        st.write(f"**Description:** {niche['description']}")

                with col2:
                    st.caption(f"Created: {niche['created_at']}")
                    st.caption(f"Updated: {niche['updated_at']}")

                st.divider()

                # Edit form
                with st.form(f"edit_niche_{niche['id']}"):
                    st.write("**Edit Niche**")

                    col1, col2 = st.columns(2)

                    with col1:
                        new_name = st.text_input("Name", value=niche['name'], key=f"name_{niche['id']}")
                        new_slug = st.text_input("Slug", value=niche['slug'], key=f"slug_{niche['id']}")

                    with col2:
                        new_type = st.selectbox(
                            "Type",
                            ["", "fiction", "crypto", "food", "tech", "gaming", "history", "other"],
                            index=["", "fiction", "crypto", "food", "tech", "gaming", "history", "other"].index(niche['type']) if niche['type'] in ["fiction", "crypto", "food", "tech", "gaming", "history", "other"] else 0,
                            key=f"type_{niche['id']}"
                        )
                        new_desc = st.text_area("Description", value=niche['description'] or "", key=f"desc_{niche['id']}")

                    col1, col2 = st.columns(2)

                    with col1:
                        update_submitted = st.form_submit_button("Update Niche")

                    with col2:
                        delete_submitted = st.form_submit_button("🗑️ Delete Niche", type="secondary")

                    if update_submitted:
                        try:
                            update_niche(
                                niche['id'],
                                name=new_name,
                                slug=new_slug,
                                type=new_type if new_type else None,
                                description=new_desc if new_desc else None
                            )
                            st.success("✅ Niche updated!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error updating niche: {e}")

                    if delete_submitted:
                        try:
                            delete_niche(niche['id'])
                            st.success("✅ Niche deleted!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting niche: {e}")


def _ingest_source(source_id: int, file_path: str, niche_id: int, title: str) -> tuple:
    """Extract, chunk, embed, and store a canon source PDF.

    Returns:
        (success: bool, chunk_count: int, error_msg: str)
    """
    try:
        full_text, metadata = extract_pdf(file_path)
        if not full_text.strip():
            return False, 0, "PDF contained no extractable text."

        chunks = chunk_with_metadata(
            full_text, chunk_size=2000, overlap=200, source_id=source_id
        )
        if not chunks:
            return False, 0, "No chunks created from PDF text."

        vectors = embed_batch([c["text"] for c in chunks], batch_size=32)

        db = get_db()
        store_canon_chunks(
            chunks=chunks,
            niche_id=niche_id,
            source_id=source_id,
            vectors=vectors,
            chapter=title,
            db=db
        )

        mark_as_ingested(source_id)
        return True, len(chunks), ""
    except Exception as e:
        return False, 0, str(e)


def render_canon_sources_tab():
    """Render the Canon Sources tab."""
    st.subheader("Manage Canon Sources")

    # Get current niche
    current_niche = st.session_state.current_niche

    if not current_niche:
        st.warning("Please select a niche from the sidebar to manage canon sources.")
        return

    # Get sources for this niche
    sources = get_sources_by_niche(current_niche)

    # Add new source section
    with st.expander("➕ Add New Canon Source", expanded=False):
        st.write("Upload a PDF file or link an existing file on disk.")

        # File uploader (outside form — Streamlit limitation)
        uploaded_file = st.file_uploader(
            "Upload PDF",
            type=["pdf"],
            key="canon_pdf_upload"
        )

        with st.form("add_source_form"):
            title = st.text_input("Title*", placeholder="e.g., The Hobbit")
            author = st.text_input("Author", placeholder="e.g., J.R.R. Tolkien")

            col1, col2 = st.columns(2)

            with col1:
                source_type = st.selectbox("Type", ["book", "wiki", "whitepaper", "documentation", "article", "other"])
                priority = st.slider("Priority", 1, 10, 5, help="Higher = more authoritative")

            with col2:
                file_path = st.text_input(
                    "File Path (or use uploader above)",
                    placeholder="/path/to/file.pdf"
                )
                url = st.text_input("URL (optional)", placeholder="https://...")

            submitted = st.form_submit_button("Add Canon Source")

            if submitted:
                if not title:
                    st.error("Title is required")
                elif not uploaded_file and not file_path:
                    st.error("Please upload a PDF or provide a file path.")
                else:
                    try:
                        # If PDF uploaded, save it to data/sources/{niche-slug}/
                        saved_path = file_path
                        if uploaded_file:
                            niche = get_niche(current_niche)
                            sources_dir = Path("data/sources") / niche['slug']
                            sources_dir.mkdir(parents=True, exist_ok=True)
                            saved_path = str(sources_dir / uploaded_file.name)
                            with open(saved_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())

                        source_id = create_canon_source(
                            niche_id=current_niche,
                            title=title,
                            author=author if author else None,
                            source_type=source_type,
                            file_path=saved_path,
                            url=url if url else None,
                            priority=priority
                        )
                        st.success(f"✅ Added canon source: {title} (ID: {source_id})")

                        # Auto-ingest if it's a PDF
                        if saved_path and saved_path.lower().endswith(".pdf"):
                            with st.spinner("Extracting, chunking, and embedding PDF..."):
                                ok, count, err = _ingest_source(
                                    source_id, saved_path, current_niche, title
                                )
                            if ok:
                                st.success(f"✅ Ingested! {count} chunks embedded and searchable.")
                            else:
                                st.warning(f"Source saved but ingestion failed: {err}")

                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding source: {e}")

    st.divider()

    # List sources
    if not sources:
        st.info("No canon sources for this niche. Add one above!")
    else:
        st.write(f"**Total Sources:** {len(sources)}")

        # Create dataframe for display
        df_data = []
        for source in sources:
            df_data.append({
                "ID": source['id'],
                "Title": source['title'],
                "Author": source['author'] or "Unknown",
                "Type": source['source_type'] or "N/A",
                "Priority": source['priority'],
                "Ingested": "✅" if source['ingested'] else "⏳"
            })

        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.divider()

        # Detail view for each source
        for source in sources:
            status_icon = "✅" if source['ingested'] else "⏳"
            with st.expander(f"{status_icon} {source['title']}", expanded=False):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.write(f"**ID:** {source['id']}")
                    st.write(f"**Author:** {source['author'] or 'Unknown'}")
                    st.write(f"**Type:** {source['source_type']}")
                    st.write(f"**Priority:** {source['priority']}/10")
                    if source['file_path']:
                        st.write(f"**File:** `{source['file_path']}`")
                        # Check if file exists
                        if Path(source['file_path']).exists():
                            st.success("File found")
                        else:
                            st.error("File not found")
                    if source['url']:
                        st.write(f"**URL:** {source['url']}")

                with col2:
                    st.metric("Status", "Ingested" if source['ingested'] else "Pending")
                    if source['ingested_at']:
                        st.caption(f"Ingested: {source['ingested_at']}")

                st.divider()

                col1, col2, col3 = st.columns(3)

                with col1:
                    if not source['ingested']:
                        if st.button("🚀 Trigger Ingestion", key=f"ingest_{source['id']}"):
                            with st.spinner("Extracting, chunking, and embedding..."):
                                ok, count, err = _ingest_source(
                                    source['id'], source['file_path'],
                                    current_niche, source['title']
                                )
                            if ok:
                                st.success(f"✅ Ingested! {count} chunks embedded.")
                                st.rerun()
                            else:
                                st.error(f"Ingestion failed: {err}")

                with col2:
                    if st.button("🗑️ Delete Source", key=f"delete_source_{source['id']}"):
                        try:
                            delete_canon_source(source['id'])
                            st.success("✅ Source deleted!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

                with col3:
                    if source['ingested']:
                        if st.button("🔄 Re-ingest", key=f"reingest_{source['id']}"):
                            with st.spinner("Re-ingesting..."):
                                ok, count, err = _ingest_source(
                                    source['id'], source['file_path'],
                                    current_niche, source['title']
                                )
                            if ok:
                                st.success(f"✅ Re-ingested! {count} chunks embedded.")
                                st.rerun()
                            else:
                                st.error(f"Re-ingestion failed: {err}")


def render_competitors_tab():
    """Render the Competitors tab."""
    st.subheader("Manage Competitor Channels")

    # Get current niche
    current_niche = st.session_state.current_niche

    if not current_niche:
        st.warning("Please select a niche from the sidebar to manage competitors.")
        return

    # Get channels for this niche
    channels = get_channels_by_niche(current_niche)

    # Add new competitor
    with st.expander("➕ Add New Competitor Channel", expanded=False):
        with st.form("add_competitor_form"):
            col1, col2 = st.columns(2)

            with col1:
                youtube_id = st.text_input("YouTube Channel ID*", placeholder="UCW0gH2G-cMKAEjEkI4YhnPA")
                name = st.text_input("Channel Name*", placeholder="e.g., Nerd of the Rings")

            with col2:
                url = st.text_input("Channel URL", placeholder="https://youtube.com/@...")
                style = st.text_input("Style", placeholder="e.g., AI voiceover, faceless")

            quality_tier = st.selectbox("Quality Tier", ["", "top", "mid", "low"])
            notes = st.text_area("Notes", placeholder="Any observations about this channel")

            submitted = st.form_submit_button("Add Competitor")

            if submitted:
                if not youtube_id or not name:
                    st.error("Channel ID and Name are required")
                else:
                    try:
                        # Check if already exists
                        existing = get_competitor_channel_by_youtube_id(youtube_id)
                        if existing:
                            st.error(f"Channel already exists: {existing['name']}")
                        else:
                            channel_id = create_competitor_channel(
                                niche_id=current_niche,
                                youtube_id=youtube_id,
                                name=name,
                                url=url if url else None,
                                style=style if style else None,
                                quality_tier=quality_tier if quality_tier else None,
                                notes=notes if notes else None
                            )
                            st.success(f"✅ Added competitor: {name} (ID: {channel_id})")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error adding competitor: {e}")

    st.divider()

    # List competitors
    if not channels:
        st.info("No competitors tracked for this niche. Add one above!")
    else:
        st.write(f"**Total Competitors:** {len(channels)}")

        # Create dataframe
        df_data = []
        for channel in channels:
            df_data.append({
                "ID": channel['id'],
                "Name": channel['name'],
                "YouTube ID": channel['youtube_id'],
                "Subscribers": f"{channel['subscriber_count']:,}" if channel['subscriber_count'] else "N/A",
                "Videos": channel['video_count'] or 0,
                "Quality": channel['quality_tier'] or "N/A",
                "Last Scraped": channel['last_scraped'] if channel['last_scraped'] else "Never"
            })

        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.divider()

        # Detail view
        for channel in channels:
            scraped_icon = "✅" if channel['last_scraped'] else "⏳"
            with st.expander(f"{scraped_icon} {channel['name']}", expanded=False):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.write(f"**ID:** {channel['id']}")
                    st.write(f"**YouTube ID:** `{channel['youtube_id']}`")
                    if channel['url']:
                        st.write(f"**URL:** {channel['url']}")
                    if channel['style']:
                        st.write(f"**Style:** {channel['style']}")
                    if channel['notes']:
                        st.write(f"**Notes:** {channel['notes']}")

                with col2:
                    if channel['subscriber_count']:
                        st.metric("Subscribers", f"{channel['subscriber_count']:,}")
                    if channel['video_count']:
                        st.metric("Videos", channel['video_count'])
                    if channel['quality_tier']:
                        st.metric("Quality", channel['quality_tier'])

                if channel['last_scraped']:
                    st.success(f"Last scraped: {channel['last_scraped']}")
                else:
                    st.info("Never scraped")

                st.divider()

                col1, col2, col3 = st.columns(3)

                with col1:
                    if st.button("🔍 Scrape Channel", key=f"scrape_{channel['id']}"):
                        st.info("Would trigger scraping script here")
                        st.code(f"python scripts/scrape_channel.py {channel['youtube_id']} --niche-id {current_niche}")

                with col2:
                    if st.button("🗑️ Delete Channel", key=f"delete_channel_{channel['id']}"):
                        try:
                            delete_competitor_channel(channel['id'])
                            st.success("✅ Channel deleted!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

                with col3:
                    if channel['last_scraped']:
                        if st.button("🔄 Re-scrape", key=f"rescrape_{channel['id']}"):
                            st.info("Would trigger re-scraping")


def render_glossary_tab():
    """Render the Glossary tab."""
    st.subheader("Manage Glossary")

    # Get current niche
    current_niche = st.session_state.current_niche

    if not current_niche:
        st.warning("Please select a niche from the sidebar to manage glossary.")
        return

    # Get glossary terms
    glossary = get_glossary_by_niche(current_niche)

    # Add new term
    with st.expander("➕ Add New Glossary Term", expanded=False):
        with st.form("add_term_form"):
            col1, col2 = st.columns(2)

            with col1:
                term = st.text_input("Term*", placeholder="e.g., Gandalf")
                term_type = st.selectbox("Type*", ["character", "location", "item", "concept", "brand", "other"])

            with col2:
                phonetic_hints = st.text_input(
                    "Phonetic Hints",
                    placeholder="gan-dalf,gahn-dalf,gan-dolf",
                    help="Comma-separated phonetic variations"
                )
                aliases = st.text_input(
                    "Aliases (JSON)",
                    placeholder='["Mithrandir", "The Grey Wizard"]',
                    help="JSON array of alternative names"
                )

            description = st.text_area("Description", placeholder="Brief description of this term")

            submitted = st.form_submit_button("Add Term")

            if submitted:
                if not term or not term_type:
                    st.error("Term and Type are required")
                else:
                    try:
                        term_id = create_glossary_entry(
                            niche_id=current_niche,
                            term=term,
                            term_type=term_type,
                            phonetic_hints=phonetic_hints if phonetic_hints else None,
                            aliases=aliases if aliases else None,
                            description=description if description else None
                        )
                        st.success(f"✅ Added term: {term} (ID: {term_id})")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding term: {e}")

    st.divider()

    # Filter by type
    col1, col2 = st.columns([3, 1])

    with col1:
        filter_type = st.selectbox(
            "Filter by type:",
            ["All", "character", "location", "item", "concept", "brand", "other", "unknown"]
        )

    with col2:
        st.metric("Total Terms", len(glossary))

    # Filter glossary
    if filter_type != "All":
        filtered_glossary = [t for t in glossary if t['term_type'] == filter_type]
    else:
        filtered_glossary = glossary

    st.write(f"Showing {len(filtered_glossary)} term(s)")

    if not filtered_glossary:
        st.info("No glossary terms found. Add some above or extract from canon sources!")
    else:
        # Group by type
        by_type = {}
        for term in filtered_glossary:
            t_type = term['term_type'] or 'unknown'
            if t_type not in by_type:
                by_type[t_type] = []
            by_type[t_type].append(term)

        # Display by type
        for term_type, terms in sorted(by_type.items()):
            with st.expander(f"📝 {term_type.upper()} ({len(terms)} terms)", expanded=True):
                for term in sorted(terms, key=lambda x: x['term']):
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        st.write(f"**{term['term']}**")
                        if term['description']:
                            st.caption(term['description'])
                        if term['phonetic_hints']:
                            st.caption(f"🔊 Phonetic: {term['phonetic_hints']}")
                        if term['aliases']:
                            st.caption(f"🏷️ Aliases: {term['aliases']}")

                    with col2:
                        if st.button("🗑️", key=f"delete_term_{term['id']}", help="Delete term"):
                            try:
                                delete_glossary_entry(term['id'])
                                st.success("✅ Term deleted!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")

                    st.divider()


def render():
    """Render the niche setup page."""
    st.title("⚙️ Niche Setup")
    st.divider()

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📁 Niches",
        "📚 Canon Sources",
        "🔍 Competitors",
        "📝 Glossary"
    ])

    with tab1:
        render_niches_tab()

    with tab2:
        render_canon_sources_tab()

    with tab3:
        render_competitors_tab()

    with tab4:
        render_glossary_tab()
