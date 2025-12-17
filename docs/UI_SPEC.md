# Content Intelligence System - UI Specification

## Overview

The dashboard is built with Streamlit (Phase 1) for rapid development. It provides access to all system functions through a sidebar navigation.

**Tech stack:**
- Streamlit (Python)
- Runs locally at `http://localhost:8501`
- Connects to SQLite + LanceDB backends

---

## Navigation Structure

```
┌─────────────────────────────────────────────────────────────────┐
│  SIDEBAR                        MAIN CONTENT AREA               │
├─────────────────────────────────────────────────────────────────┤
│  ┌───────────────────┐         ┌──────────────────────────────┐│
│  │ 📊 Home           │         │                              ││
│  │ ⚙️  Niche Setup    │         │  [Content changes based on   ││
│  │ 🔍 Competitive Intel│        │   selected nav item]         ││
│  │ 📚 Research        │         │                              ││
│  │ 💡 Ideation        │         │                              ││
│  │ 🎬 Production      │         │                              ││
│  │ 🖼️  Asset Library   │         │                              ││
│  │ 📈 My Analytics    │         │                              ││
│  │ ⚡ Settings        │         │                              ││
│  │ ─────────────────  │         │                              ││
│  │ 🔭 Scout (Phase 2) │         │                              ││
│  └───────────────────┘         └──────────────────────────────┘│
│                                                                 │
│  ┌───────────────────┐                                         │
│  │ Current Niche:    │                                         │
│  │ [Dropdown]        │                                         │
│  └───────────────────┘                                         │
└─────────────────────────────────────────────────────────────────┘
```

**Global element:** Niche selector dropdown appears on all screens. Filters data to selected niche, or "All Niches" for cross-niche views.

---

## Screen 1: Home

**Purpose:** Quick overview and alerts.

**Components:**
- Stat cards: Niches count, Competitors tracked, Canon sources, My videos
- Recent activity feed (last 24-48 hours of actions)
- Alerts panel (trends, competitor uploads, recommendations)
- Production queue table (videos in progress)

**Key features:**
- At-a-glance system health
- Quick access to in-progress work
- Proactive alerts about opportunities

---

## Screen 2: Niche Setup

**Purpose:** Configure and manage niches, sources, competitors.

**Tabs:**
1. **Niches** - List/add/edit/delete niches
2. **Canon Sources** - Manage books/docs per niche, trigger ingestion
3. **Competitors** - Add/remove channels, view scrape status
4. **Glossary** - View/edit terms, add phonetic hints, auto-extract from canon

**Key features:**
- CRUD for all entities
- Status indicators (ingested, scraped, pending)
- Bulk actions (re-scrape, re-ingest)
- Auto-extract glossary from canon sources

---

## Screen 3: Competitive Intel

**Purpose:** Analyse competitor content and find opportunities.

**Tabs:**
1. **Videos** - Browse all competitor videos with filters (channel, date, views, topic)
2. **Topics** - Topic analysis showing video count, avg views, trend direction
3. **Gaps** - Topics rich in canon but sparse in competitor coverage
4. **Thumbnails** - Gallery view with performance metrics

**Key features:**
- Rich filtering and sorting
- Expandable rows for video details
- Gap analysis with opportunity scoring
- Thumbnail gallery with style analysis
- "Generate idea" button from gap analysis

---

## Screen 4: Research

**Purpose:** Semantic search across all content.

**Components:**
- Search bar with semantic query input
- Toggle: Canon / Transcripts / Both
- Niche filter (or all niches for cross-niche)
- Results list with relevance scores
- Source attribution (book/chapter or video/channel)
- Copy/Use buttons per result

**Key features:**
- Cross-niche semantic search
- Relevance scoring
- "Use" button adds to ideation context
- Full passage view with surrounding context

---

## Screen 5: Ideation

**Purpose:** Generate and manage video ideas.

**Components:**
- Generation controls: checkboxes for gaps/trends/performance
- Focus area input (optional topic constraint)
- Generate button
- Generated ideas list with rationale
- Save/Reject/Start Production buttons
- Saved ideas backlog

**Key features:**
- LLM-powered idea generation
- Ideas include "why" reasoning
- Suggested angles based on data
- Direct path to production pipeline

---

## Screen 6: Production

**Purpose:** Manage videos from idea to published.

**Components:**
- Kanban pipeline: Idea → Research → Script → Edit → Published
- Drag-and-drop status changes
- Selected video detail panel with tabs:
  - Overview (title, status, dates)
  - Research (relevant passages, competitor coverage)
  - Script (editor with LLM generation)
  - Assets (linked images, gap detection)
  - Notes (freeform)

**Key features:**
- Visual pipeline management
- LLM script generation (outline or full draft)
- Auto-detect image requirements from script
- Link to asset library for fulfillment

---

## Screen 7: Asset Library

**Purpose:** Manage images and track usage.

**Components:**
- Filter bar: subject, style, usage count, source
- Grid view with thumbnails
- Usage count badges
- Selected asset detail panel:
  - Large preview
  - Metadata (source, prompt, created date)
  - Tags (editable)
  - Usage history (which videos, timestamps)

**Key features:**
- Visual browsing
- Usage tracking to prevent repetition
- Prompt preservation for AI-generated images
- Gap identification (script needs image you don't have)

---

## Screen 8: My Analytics

**Purpose:** Track your channel performance.

**Components:**
- Channel selector dropdown
- Period selector (7d, 28d, 90d, custom)
- Overview stat cards: Views, Watch time, Subs, Avg CTR
- Video performance table with status indicators
- Cross-platform summary (Shorts, TikTok, Twitter)
- Recommendations panel (LLM-generated insights)

**Key features:**
- Multi-channel support
- Trend indicators on all metrics
- Performance status per video
- Cross-platform tracking
- Actionable recommendations

---

## Screen 9: Settings

**Purpose:** Configure system settings and API keys.

**Tabs:**
1. **API Keys** - Manage Anthropic, YouTube, OpenAI keys with validation
2. **Scraping** - Configure schedules, rate limits
3. **Database** - Stats, backup/restore, clear data
4. **About** - Version info, documentation links

**Key features:**
- Secure key storage
- Validation indicators
- Quota tracking (YouTube API)
- Database backup/restore

---

## Screen 10: Scout (Phase 2)

**Purpose:** Discover and evaluate new niches.

**Components:**
- Discovery criteria checkboxes (faceless suitable, CPM range, growth trend)
- Category filter
- Scan button
- Opportunities table with scores
- Manual niche evaluator input

**Key features:**
- Automated opportunity discovery
- Scoring system (CPM, competition, trend)
- Detailed breakdown on click
- Direct "Create niche" from opportunity

---

## Streamlit Project Structure

```
ui/
├── app.py                 # Main entry, navigation
├── pages/
│   ├── home.py
│   ├── niche_setup.py
│   ├── competitive_intel.py
│   ├── research.py
│   ├── ideation.py
│   ├── production.py
│   ├── asset_library.py
│   ├── analytics.py
│   ├── settings.py
│   └── scout.py
├── components/
│   ├── video_card.py
│   ├── thumbnail_grid.py
│   ├── search_bar.py
│   ├── stat_card.py
│   └── pipeline_board.py
└── utils/
    ├── database.py        # SQLite queries
    ├── vectors.py         # LanceDB operations
    ├── search.py          # Semantic search
    └── llm.py             # Claude/OpenAI calls
```

---

## Build Order (Recommended)

1. **Settings** - API key management (needed for everything else)
2. **Niche Setup** - Create niches, add sources/competitors
3. **Research** - Basic search functionality
4. **Competitive Intel** - View scraped data
5. **Production** - Video pipeline
6. **Asset Library** - Image management
7. **Ideation** - LLM-powered ideas
8. **Home** - Dashboard overview
9. **My Analytics** - Performance tracking
10. **Scout** - Niche discovery (Phase 2)

---

## State Management

```python
import streamlit as st

# Initialize session state
if 'current_niche' not in st.session_state:
    st.session_state.current_niche = None

if 'selected_video' not in st.session_state:
    st.session_state.selected_video = None

if 'research_context' not in st.session_state:
    st.session_state.research_context = []
```

---

## Component Patterns

### Stat Card

```python
def stat_card(title: str, value: str, trend: str = None):
    """Reusable stat card component."""
    st.metric(label=title, value=value, delta=trend)
```

### Video Card

```python
def video_card(video: dict, show_thumbnail: bool = True):
    """Expandable video card with details."""
    with st.expander(f"{video['title']} - {video['views']:,} views"):
        if show_thumbnail and video.get('thumbnail_path'):
            st.image(video['thumbnail_path'])
        st.write(f"Channel: {video['channel_name']}")
        st.write(f"Published: {video['published_at']}")
        st.write(f"Views/Sub: {video['views_per_sub']:.2f}")
```

### Search Results

```python
def search_result(result: dict, source_type: str):
    """Display a search result with actions."""
    st.markdown(f"**{source_type.upper()}:** {result['source']}")
    st.markdown(f"Relevance: {result['score']:.0%}")
    st.text(result['text'][:500] + "...")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Copy", key=f"copy_{result['id']}"):
            st.clipboard(result['text'])
    with col2:
        if st.button("Use", key=f"use_{result['id']}"):
            st.session_state.research_context.append(result)
```
