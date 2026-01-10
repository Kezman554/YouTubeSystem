# Streamlit Dashboard

## Running the App

Start the Streamlit dashboard:

```bash
python -m streamlit run src/ui/app.py
```

Then open your browser to: **http://localhost:8501**

## Structure

```
ui/
├── app.py                    # Main entry point
├── pages/                    # Page modules
│   ├── home.py              # Dashboard overview
│   ├── niche_setup.py       # Niche configuration
│   ├── competitive_intel.py # Competitor analysis
│   ├── research.py          # Semantic search
│   └── settings.py          # System settings
├── components/              # Reusable UI components (future)
└── utils/                   # Helper functions (future)
```

## Navigation

**Active Pages:**
- 📊 **Home** - Dashboard with system statistics
- ⚙️ **Niche Setup** - Configure niches, sources, competitors (placeholder)
- 🔍 **Competitive Intel** - Analyze competitor content (placeholder)
- 📚 **Research** - Semantic search (placeholder)
- ⚡ **Settings** - API keys, database info, about

**Phase 2 (Coming Soon):**
- 💡 Ideation - Generate video ideas
- 🎬 Production - Video pipeline
- 🖼️ Asset Library - Image management
- 📈 My Analytics - Channel performance
- 🔭 Scout - Niche discovery

## Features

### Home Dashboard

Shows real-time statistics from the database:
- Number of niches configured
- Competitors tracked
- Videos scraped
- Canon sources ingested
- Glossary terms extracted
- Vector chunks indexed
- Transcripts imported

Breakdown by niche when multiple niches exist.

### Niche Selector

Global dropdown in sidebar:
- Filters all data to selected niche
- "All Niches" option for cross-niche view
- Shows niche type and description

### Settings

- View .env status
- Database location and size
- Tech stack information
- Links to documentation

## Development

### Adding a New Page

1. Create `src/ui/pages/your_page.py`:

```python
import streamlit as st

def render():
    st.title("Your Page Title")
    # Your page content here
```

2. Add navigation button in `app.py`:

```python
if st.button("Your Page", key="nav_your_page"):
    st.session_state.current_page = "Your Page"
```

3. Add routing in `route_to_page()`:

```python
elif page == "Your Page":
    from pages import your_page
    your_page.render()
```

### Session State

Available globally:
- `st.session_state.current_niche` - Selected niche ID (or None for all)
- `st.session_state.current_page` - Active page name
- `st.session_state.selected_video` - Selected video (for detail views)
- `st.session_state.research_context` - Research results saved for later use

## Next Steps

1. **Niche Setup Page** - Full CRUD for niches, sources, competitors
2. **Research Page** - Implement semantic search UI
3. **Competitive Intel** - Video browsing, filtering, gap analysis
4. **Production Pipeline** - Kanban board for video workflow (Phase 2)

## Troubleshooting

**Streamlit not found:**
```bash
python -m pip install streamlit
```

**Import errors:**
Make sure you're in the project root when running the command.

**Database errors:**
Run the database initialization and test scripts first to populate data.
