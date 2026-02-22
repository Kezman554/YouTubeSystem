"""
Content Intelligence System - Streamlit Dashboard

Main entry point for the UI.
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.database.niches import get_all_niches
from src.database.production_context import get_production_item_count


# Page configuration
st.set_page_config(
    page_title="Content Intelligence System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


def init_session_state():
    """Initialize session state variables, restoring from URL query params if present."""
    params = st.query_params

    if 'current_page' not in st.session_state:
        st.session_state.current_page = params.get("page", "Home")

    if 'current_niche' not in st.session_state:
        niche_param = params.get("niche")
        st.session_state.current_niche = int(niche_param) if niche_param else None

    if 'selected_video' not in st.session_state:
        st.session_state.selected_video = None

    if 'research_context' not in st.session_state:
        st.session_state.research_context = []


def _sync_query_params():
    """Sync current session state to URL query params for persistence across refreshes."""
    params = {}
    if st.session_state.current_page and st.session_state.current_page != "Home":
        params["page"] = st.session_state.current_page
    if st.session_state.current_niche is not None:
        params["niche"] = str(st.session_state.current_niche)
    st.query_params.update(params)
    # Clear params that are no longer set
    for key in list(st.query_params.keys()):
        if key not in params:
            del st.query_params[key]


def render_sidebar():
    """Render sidebar with navigation and niche selector."""
    with st.sidebar:
        st.title("📊 Content Intel")

        st.divider()

        # Navigation menu
        st.subheader("Navigation")

        pages = {
            "📊 Home": "Home",
            "⚙️ Niche Setup": "Niche Setup",
            "🔍 Competitive Intel": "Competitive Intel",
            "📚 Research": "Research",
            "⚡ Settings": "Settings"
        }

        # Production item count for nav badge
        try:
            prod_count = get_production_item_count()
        except Exception:
            prod_count = 0

        prod_label = f"🎬 Production ({prod_count})" if prod_count > 0 else "🎬 Production"

        # Phase 2 pages (disabled for now)
        phase_2_pages = {
            prod_label: "Production",
            "💡 Ideation": "Ideation",
            "🖼️ Asset Library": "Asset Library",
            "📈 My Analytics": "My Analytics",
            "🔭 Scout": "Scout"
        }

        # Render active pages
        for label, page_name in pages.items():
            if st.button(label, key=f"nav_{page_name}", use_container_width=True):
                st.session_state.current_page = page_name

        st.divider()
        st.caption("Phase 2 (Coming Soon)")

        # Render phase 2 pages (disabled)
        for label, page_name in phase_2_pages.items():
            st.button(label, key=f"nav_{page_name}", use_container_width=True, disabled=True)

        st.divider()

        # Niche selector
        st.subheader("Current Niche")

        try:
            niches = get_all_niches()

            if niches:
                niche_options = ["All Niches"] + [n['name'] for n in niches]
                niche_ids = [None] + [n['id'] for n in niches]

                # Get current selection index
                current_niche = st.session_state.current_niche
                if current_niche is None:
                    default_index = 0
                else:
                    try:
                        default_index = niche_ids.index(current_niche)
                    except ValueError:
                        default_index = 0

                selected = st.selectbox(
                    "Filter by niche:",
                    options=niche_options,
                    index=default_index,
                    key="niche_selector"
                )

                # Update session state
                selected_index = niche_options.index(selected)
                st.session_state.current_niche = niche_ids[selected_index]

                # Show niche info
                if st.session_state.current_niche:
                    niche = niches[selected_index - 1]  # -1 because of "All Niches"
                    st.caption(f"Type: {niche.get('type', 'N/A')}")
                    if niche.get('description'):
                        st.caption(f"{niche['description'][:100]}...")
            else:
                st.info("No niches created yet. Go to Niche Setup to create one.")

        except Exception as e:
            st.error(f"Error loading niches: {e}")


def route_to_page():
    """Route to the selected page."""
    page = st.session_state.current_page

    # Import and render the appropriate page
    if page == "Home":
        from pages import home
        home.render()

    elif page == "Niche Setup":
        from pages import niche_setup
        niche_setup.render()

    elif page == "Competitive Intel":
        from pages import competitive_intel
        competitive_intel.render()

    elif page == "Research":
        from pages import research
        research.render()

    elif page == "Settings":
        from pages import settings
        settings.render()

    else:
        st.warning(f"Page '{page}' not yet implemented")
        st.info("This page is coming in a future update!")


def main():
    """Main application entry point."""
    # Initialize session state
    init_session_state()

    # Render sidebar
    render_sidebar()

    # Sync state to URL so refresh preserves page + niche
    _sync_query_params()

    # Route to selected page
    route_to_page()


if __name__ == "__main__":
    main()
