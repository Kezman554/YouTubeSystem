# Content Intelligence System - Data Model

## Overview

The system uses two databases:

| Database | Type | Purpose |
|----------|------|---------|
| **SQLite** | Relational | Structured data: metadata, relationships, stats |
| **LanceDB** | Vector | Semantic content: text chunks with embeddings for similarity search |

Data is linked between them using IDs (niche_id, video_id, source_id).

---

## SQLite Tables

### 1. niches

Top-level container for each content area.

```sql
CREATE TABLE niches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                    -- "Middle-earth", "ICP Ecosystem", "Italian Cooking"
    slug TEXT UNIQUE NOT NULL,             -- "middle-earth", "icp", "italian-cooking"
    type TEXT,                             -- "fiction", "crypto", "food", "tech", etc.
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### 2. canon_sources

Books, documents, wikis—authoritative material for each niche.

```sql
CREATE TABLE canon_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    niche_id INTEGER NOT NULL,
    title TEXT NOT NULL,                   -- "The Silmarillion"
    author TEXT,                           -- "J.R.R. Tolkien"
    source_type TEXT,                      -- "book", "wiki", "whitepaper", "documentation"
    file_path TEXT,                        -- Local path to PDF/text file
    url TEXT,                              -- Web source URL if applicable
    priority INTEGER DEFAULT 1,            -- Higher = more authoritative
    ingested BOOLEAN DEFAULT FALSE,
    ingested_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (niche_id) REFERENCES niches(id)
);
```

---

### 3. glossary

Canonical terms per niche—used for transcript cleaning and auto-tagging.

```sql
CREATE TABLE glossary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    niche_id INTEGER NOT NULL,
    term TEXT NOT NULL,                    -- "Boromir"
    term_type TEXT,                        -- "character", "location", "item", "concept", "brand"
    phonetic_hints TEXT,                   -- "borrow-meer,bore-oh-mir"
    aliases TEXT,                          -- JSON: ["Son of Denethor", "Captain of Gondor"]
    description TEXT,
    source_id INTEGER,                     -- Which canon source this came from
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (niche_id) REFERENCES niches(id),
    FOREIGN KEY (source_id) REFERENCES canon_sources(id)
);
```

---

### 4. competitor_channels

Channels being tracked in each niche.

```sql
CREATE TABLE competitor_channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    niche_id INTEGER NOT NULL,
    youtube_id TEXT UNIQUE NOT NULL,       -- YouTube channel ID
    name TEXT NOT NULL,                    -- "Nerd of the Rings"
    url TEXT,
    subscriber_count INTEGER,
    video_count INTEGER,
    style TEXT,                            -- "AI voiceover", "real person", "documentary"
    quality_tier TEXT,                     -- "top", "mid", "small"
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    last_scraped TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (niche_id) REFERENCES niches(id)
);
```

---

### 5. competitor_videos

Metadata for scraped videos.

```sql
CREATE TABLE competitor_videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id INTEGER NOT NULL,
    niche_id INTEGER NOT NULL,
    youtube_id TEXT UNIQUE NOT NULL,       -- YouTube video ID
    title TEXT NOT NULL,
    description TEXT,
    published_at TIMESTAMP,
    duration_seconds INTEGER,
    view_count INTEGER,
    like_count INTEGER,
    comment_count INTEGER,
    thumbnail_url TEXT,
    thumbnail_path TEXT,                   -- Local path if downloaded
    
    -- Calculated metrics
    views_per_sub REAL,                    -- view_count / channel subs at time
    
    -- Content analysis
    topic_tags TEXT,                       -- JSON array of detected topics
    
    -- Transcript status
    has_transcript BOOLEAN DEFAULT FALSE,
    transcript_cleaned BOOLEAN DEFAULT FALSE,
    
    -- Tracking
    first_scraped TIMESTAMP,
    last_updated TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (channel_id) REFERENCES competitor_channels(id),
    FOREIGN KEY (niche_id) REFERENCES niches(id)
);
```

---

### 6. performance_snapshots

Track video performance over time (for velocity analysis).

```sql
CREATE TABLE performance_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id INTEGER NOT NULL,
    view_count INTEGER,
    like_count INTEGER,
    comment_count INTEGER,
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES competitor_videos(id)
);
```

---

### 7. my_channels

Your own YouTube channels.

```sql
CREATE TABLE my_channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    niche_id INTEGER NOT NULL,
    youtube_id TEXT UNIQUE,                -- NULL until channel created
    name TEXT NOT NULL,
    url TEXT,
    subscriber_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (niche_id) REFERENCES niches(id)
);
```

---

### 8. my_videos

Your content with production tracking.

```sql
CREATE TABLE my_videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id INTEGER NOT NULL,
    niche_id INTEGER NOT NULL,
    youtube_id TEXT,                       -- NULL until published
    title TEXT NOT NULL,
    description TEXT,
    
    -- Production status
    status TEXT DEFAULT 'idea',            -- "idea", "researching", "scripting", "production", "published"
    script_path TEXT,                      -- Local path to script file
    notes TEXT,
    
    -- Publishing
    published_at TIMESTAMP,
    duration_seconds INTEGER,
    
    -- Performance metrics (from YouTube Studio)
    view_count INTEGER,
    like_count INTEGER,
    comment_count INTEGER,
    ctr REAL,                              -- Click-through rate
    avg_view_duration REAL,                -- Average view duration in seconds
    avg_view_percentage REAL,              -- AVD as percentage of video length
    
    -- Thumbnail
    thumbnail_url TEXT,
    thumbnail_path TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (channel_id) REFERENCES my_channels(id),
    FOREIGN KEY (niche_id) REFERENCES niches(id)
);
```

---

### 9. assets

Generated or collected images and media.

```sql
CREATE TABLE assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    niche_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,               -- Local path
    file_type TEXT,                        -- "image", "video", "audio"
    source TEXT,                           -- "stable_diffusion", "midjourney", "leonardo", "stock"
    prompt TEXT,                           -- Generation prompt if AI-created
    description TEXT,                      -- What this depicts
    
    -- Tagging (JSON arrays)
    subject_tags TEXT,                     -- ["gandalf", "staff", "magic"]
    mood_tags TEXT,                        -- ["dramatic", "dark"]
    style_tags TEXT,                       -- ["painted", "cinematic"]
    
    -- Usage tracking
    times_used INTEGER DEFAULT 0,
    last_used_in INTEGER,                  -- FK to my_videos.id
    last_used_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (niche_id) REFERENCES niches(id),
    FOREIGN KEY (last_used_in) REFERENCES my_videos(id)
);
```

---

### 10. asset_usage

Many-to-many tracking of which assets used in which videos.

```sql
CREATE TABLE asset_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,
    video_id INTEGER NOT NULL,
    timestamp_start REAL,                  -- Where in video (seconds)
    timestamp_end REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES assets(id),
    FOREIGN KEY (video_id) REFERENCES my_videos(id)
);
```

---

### 11. thumbnails

Separate tracking for thumbnails (competitors' and yours).

```sql
CREATE TABLE thumbnails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    niche_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    source_type TEXT,                      -- "competitor", "mine"
    competitor_video_id INTEGER,           -- FK if competitor
    my_video_id INTEGER,                   -- FK if mine
    
    -- Analysis (JSON)
    analysis TEXT,                         -- Detected elements, colors, text, faces
    style_tags TEXT,                       -- ["text_heavy", "character_focus", "dark"]
    
    -- Effectiveness
    effectiveness REAL,                    -- CTR for yours, views/sub for competitors
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (niche_id) REFERENCES niches(id),
    FOREIGN KEY (competitor_video_id) REFERENCES competitor_videos(id),
    FOREIGN KEY (my_video_id) REFERENCES my_videos(id)
);
```

---

### 12. tags

Flexible tagging system across niches.

```sql
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    niche_id INTEGER,                      -- NULL for universal tags (themes, moods)
    name TEXT NOT NULL,                    -- "morgoth", "first_age", "betrayal"
    tag_type TEXT,                         -- "character", "era", "location", "theme", "mood"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (niche_id) REFERENCES niches(id),
    UNIQUE(niche_id, name, tag_type)
);
```

---

### 13. video_tags

Links tags to videos (competitor or yours).

```sql
CREATE TABLE video_tags (
    video_id INTEGER NOT NULL,
    video_type TEXT NOT NULL,              -- "competitor" or "mine"
    tag_id INTEGER NOT NULL,
    confidence REAL,                       -- Auto-tagger confidence score
    PRIMARY KEY (video_id, video_type, tag_id),
    FOREIGN KEY (tag_id) REFERENCES tags(id)
);
```

---

### 14. cross_platform_posts

Track supporting content on other platforms.

```sql
CREATE TABLE cross_platform_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    my_video_id INTEGER,                   -- The main video this supports (nullable)
    niche_id INTEGER NOT NULL,
    platform TEXT NOT NULL,                -- "youtube_shorts", "tiktok", "twitter", "instagram"
    platform_id TEXT,                      -- Post ID on that platform
    url TEXT,
    title TEXT,
    posted_at TIMESTAMP,
    view_count INTEGER,
    like_count INTEGER,
    comment_count INTEGER,
    click_throughs INTEGER,                -- If trackable
    last_updated TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (my_video_id) REFERENCES my_videos(id),
    FOREIGN KEY (niche_id) REFERENCES niches(id)
);
```

---

## LanceDB Collections

### 1. canon_passages

Chunked and embedded text from source material.

```python
# Schema
{
    "id": str,                    # Unique identifier
    "niche_id": int,              # Links to SQLite niches
    "source_id": int,             # Links to SQLite canon_sources
    "text": str,                  # The actual passage (500-1000 tokens)
    "chapter": str,               # Book chapter/section
    "page": int,                  # Page number if applicable
    
    # Tagging (for filtered searches)
    "characters": list[str],      # ["Gandalf", "Frodo"]
    "locations": list[str],       # ["Moria", "Khazad-dûm"]
    "themes": list[str],          # ["sacrifice", "friendship"]
    "era": str,                   # "First Age", "Third Age", etc.
    
    "vector": list[float],        # Embedding vector (768 dims for all-MiniLM)
}
```

**Example queries:**
- "Find passages about the fall of Gondolin"
- "Find passages mentioning Morgoth in the First Age"
- "Find content about kingship across all niches"

---

### 2. transcript_chunks

Cleaned and embedded competitor transcript segments.

```python
# Schema
{
    "id": str,
    "video_id": int,              # Links to SQLite competitor_videos
    "niche_id": int,              # Links to SQLite niches
    "channel_id": int,            # Links to SQLite competitor_channels
    "text": str,                  # Cleaned transcript chunk
    "chunk_index": int,           # Order within video
    "timestamp_start": float,     # Start time in video (seconds)
    "timestamp_end": float,       # End time in video (seconds)
    
    # Denormalized for filtering
    "video_title": str,
    "channel_name": str,
    "published_at": str,          # ISO timestamp
    "view_count": int,            # Snapshot at scrape time
    
    # Tagging
    "topics": list[str],          # Detected topics in this chunk
    
    "vector": list[float],        # Embedding vector
}
```

**Example queries:**
- "How do competitors explain Morgoth's origins?"
- "Find high-view videos discussing the Silmarils"
- "What angles has Nerd of the Rings taken on Sauron?"

---

## Relationships Diagram

```
                                    ┌──────────┐
                                    │  niches  │
                                    └────┬─────┘
                                         │
         ┌──────────────┬────────────────┼────────────────┬──────────────┐
         │              │                │                │              │
         ▼              ▼                ▼                ▼              ▼
   ┌───────────┐  ┌──────────┐   ┌─────────────┐  ┌────────────┐  ┌────────┐
   │  canon_   │  │ glossary │   │ competitor_ │  │my_channels │  │ assets │
   │  sources  │  │          │   │  channels   │  │            │  │        │
   └─────┬─────┘  └──────────┘   └──────┬──────┘  └─────┬──────┘  └───┬────┘
         │                              │               │             │
         ▼                              ▼               ▼             │
   ┌───────────┐                 ┌─────────────┐  ┌──────────┐        │
   │ LanceDB:  │                 │ competitor_ │  │my_videos │◄───────┘
   │  canon_   │                 │   videos    │  │          │   (asset_usage)
   │ passages  │                 └──────┬──────┘  └────┬─────┘
   └───────────┘                        │              │
                                        ▼              ▼
                                 ┌───────────┐  ┌──────────────┐
                                 │ LanceDB:  │  │cross_platform│
                                 │transcript_│  │   _posts     │
                                 │  chunks   │  └──────────────┘
                                 └───────────┘
                                 
   Also linked:
   • performance_snapshots → competitor_videos
   • thumbnails → competitor_videos OR my_videos
   • video_tags → tags (for any video type)
```

---

## Embedding Configuration

**Model:** all-MiniLM-L6-v2 (runs locally on CPU)
**Dimensions:** 384
**Alternative:** nomic-embed-text-v1 (768 dimensions, slightly better quality)

```python
from sentence_transformers import SentenceTransformer

# Initialize once
model = SentenceTransformer('all-MiniLM-L6-v2')

# Embed text
vector = model.encode("Boromir was the eldest son of Denethor II")
# Returns: numpy array of 384 floats
```

---

## Chunking Strategy

For both canon sources and transcripts:

| Parameter | Value | Reason |
|-----------|-------|--------|
| Chunk size | ~500 tokens | Balance between context and specificity |
| Overlap | ~50 tokens | Preserve context at boundaries |
| Method | Sentence-aware | Don't cut mid-sentence |

```python
# Pseudocode
def chunk_text(text, chunk_size=500, overlap=50):
    sentences = split_into_sentences(text)
    chunks = []
    current_chunk = []
    current_size = 0
    
    for sentence in sentences:
        if current_size + len(sentence) > chunk_size and current_chunk:
            chunks.append(' '.join(current_chunk))
            # Keep overlap
            current_chunk = current_chunk[-overlap_sentences:]
            current_size = sum(len(s) for s in current_chunk)
        current_chunk.append(sentence)
        current_size += len(sentence)
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks
```

---

## Index Recommendations

For SQLite query performance:

```sql
-- Frequently filtered columns
CREATE INDEX idx_competitor_videos_niche ON competitor_videos(niche_id);
CREATE INDEX idx_competitor_videos_channel ON competitor_videos(channel_id);
CREATE INDEX idx_competitor_videos_published ON competitor_videos(published_at);
CREATE INDEX idx_my_videos_status ON my_videos(status);
CREATE INDEX idx_my_videos_niche ON my_videos(niche_id);
CREATE INDEX idx_assets_niche ON assets(niche_id);
CREATE INDEX idx_glossary_niche ON glossary(niche_id);
CREATE INDEX idx_tags_niche ON tags(niche_id);
```

---

## Notes

- All timestamps stored as ISO 8601 strings or SQLite TIMESTAMP
- JSON fields (aliases, tags) stored as TEXT, parsed in application layer
- LanceDB handles its own indexing for vector search
- Foreign keys enforced via `PRAGMA foreign_keys = ON`
