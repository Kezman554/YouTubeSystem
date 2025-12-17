# Content Intelligence System - Pipeline

## Overview

This document describes the data processing pipeline from raw sources to usable content.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PIPELINE OVERVIEW                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  INGEST              PROCESS            STORE              USE              │
│  ──────              ───────            ─────              ───              │
│                                                                              │
│  ┌─────────┐        ┌─────────┐        ┌─────────┐        ┌─────────┐      │
│  │ Scrape  │───────►│ Clean   │───────►│ Chunk & │───────►│ Search  │      │
│  │         │        │         │        │ Embed   │        │         │      │
│  └─────────┘        └─────────┘        └─────────┘        └─────────┘      │
│                                                                              │
│  Sources:           Uses:              Stores in:         Enables:          │
│  • YouTube API      • Glossary         • SQLite           • Semantic search │
│  • PDF extraction   • LLM cleaning     • LanceDB          • Gap analysis    │
│  • Web scraping     • Tagging                             • Ideation        │
│                                                           • Scripting       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Pipeline Steps

### Step 1: Scraping

**Purpose:** Collect raw data from external sources.

#### 1A: YouTube Competitor Scraping

```
Input:  Channel ID or URL
Output: Video metadata + raw transcripts
```

**What we collect:**

| Data | Source | Storage |
|------|--------|---------|
| Channel info | YouTube API | SQLite: competitor_channels |
| Video metadata | YouTube API | SQLite: competitor_videos |
| Thumbnails | YouTube (download) | Local files + SQLite path |
| Transcripts | youtube-transcript-api | Temp storage → cleaning |

**Tools:**
- `youtube-transcript-api` — Get auto-generated or manual captions
- `yt-dlp` — Alternative, more features
- YouTube Data API v3 — Official metadata (requires API key)

**Code pattern:**

```python
from youtube_transcript_api import YouTubeTranscriptApi

def get_transcript(video_id: str) -> str:
    """Fetch raw transcript from YouTube."""
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        return ' '.join([entry['text'] for entry in transcript_list])
    except Exception as e:
        return None
```

**Rate limiting:**
- YouTube API: 10,000 quota units/day (free tier)
- Transcript API: No official limit, but be respectful (~1 req/second)

---

#### 1B: Canon Source Ingestion

```
Input:  PDF, EPUB, TXT, or web URL
Output: Extracted text with metadata
```

**Tools:**
- `PyMuPDF` (fitz) — PDF extraction
- `ebooklib` — EPUB extraction
- `beautifulsoup4` — Web scraping
- `trafilatura` — Web article extraction

**Code pattern:**

```python
import fitz  # PyMuPDF

def extract_pdf(file_path: str) -> list[dict]:
    """Extract text from PDF with page numbers."""
    doc = fitz.open(file_path)
    pages = []
    for page_num, page in enumerate(doc, 1):
        text = page.get_text()
        pages.append({
            "page": page_num,
            "text": text
        })
    return pages
```

---

### Step 2: Transcript Cleaning

**Purpose:** Fix auto-generated transcript errors using glossary + LLM.

```
Input:  Raw transcript + niche glossary
Output: Cleaned transcript with corrections
```

**Why needed:**
- Auto-captions mishear fantasy/technical terms
- "Boromir" → "borrow mere"
- "Silmaril" → "silver mill"
- "DFINITY" → "d finicky"

**Process:**

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    Raw      │────►│   Phonetic  │────►│   LLM       │
│  Transcript │     │   Matching  │     │   Cleanup   │
└─────────────┘     └─────────────┘     └─────────────┘
                           │                   │
                           ▼                   ▼
                    ┌─────────────┐     ┌─────────────┐
                    │  Glossary   │     │   Claude    │
                    │  (terms +   │     │   Haiku     │
                    │  phonetics) │     │   API       │
                    └─────────────┘     └─────────────┘
```

**LLM Cleaning Prompt:**

```python
CLEANING_PROMPT = """
You are a transcript cleaner for {niche_name} content.

Here is a glossary of correct terms and their common mishearings:
{glossary}

Clean the following transcript. Fix any misspelled names, places, or 
technical terms. Only fix clear errors - don't change anything you're 
not confident about.

Return ONLY the cleaned transcript, nothing else.

Transcript:
{transcript}
"""
```

**Glossary format:**

```python
glossary_entry = {
    "term": "Boromir",
    "phonetic_hints": ["borrow mere", "bore oh mir", "borrow mirror"],
    "context": "character, son of Denethor, man of Gondor"
}
```

**Cost estimate:**
- Average transcript: ~3,000-5,000 tokens
- Claude Haiku: ~$0.25/million input, $1.25/million output
- Cost per transcript: ~$0.001-0.002

**Code pattern:**

```python
import anthropic

client = anthropic.Anthropic()

def clean_transcript(transcript: str, glossary: list[dict], niche_name: str) -> str:
    """Clean transcript using Claude Haiku."""
    
    glossary_text = "\n".join([
        f"- {g['term']}: often misheard as {', '.join(g['phonetic_hints'])}"
        for g in glossary
    ])
    
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=8000,
        messages=[{
            "role": "user",
            "content": CLEANING_PROMPT.format(
                niche_name=niche_name,
                glossary=glossary_text,
                transcript=transcript
            )
        }]
    )
    
    return response.content[0].text
```

---

### Step 3: Chunking

**Purpose:** Split long texts into searchable segments.

```
Input:  Cleaned text (transcript or canon)
Output: List of chunks with metadata
```

**Parameters:**

| Parameter | Value | Reason |
|-----------|-------|--------|
| Target chunk size | ~500 tokens (~2000 chars) | Balance context vs specificity |
| Overlap | ~50 tokens (~200 chars) | Preserve context at boundaries |
| Method | Sentence-aware | Never cut mid-sentence |

**Code pattern:**

```python
import re

def chunk_text(
    text: str, 
    chunk_size: int = 2000,  # characters
    overlap: int = 200
) -> list[str]:
    """Split text into overlapping chunks at sentence boundaries."""
    
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        sentence_length = len(sentence)
        
        # If adding this sentence exceeds limit, save chunk and start new
        if current_length + sentence_length > chunk_size and current_chunk:
            chunks.append(' '.join(current_chunk))
            
            # Calculate overlap - keep last N characters worth of sentences
            overlap_text = ' '.join(current_chunk)
            if len(overlap_text) > overlap:
                # Find sentences that fit in overlap
                overlap_sentences = []
                overlap_length = 0
                for s in reversed(current_chunk):
                    if overlap_length + len(s) <= overlap:
                        overlap_sentences.insert(0, s)
                        overlap_length += len(s)
                    else:
                        break
                current_chunk = overlap_sentences
                current_length = overlap_length
            else:
                current_chunk = []
                current_length = 0
        
        current_chunk.append(sentence)
        current_length += sentence_length
    
    # Don't forget the last chunk
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks
```

---

### Step 4: Embedding

**Purpose:** Convert text chunks into vectors for semantic search.

```
Input:  Text chunk
Output: Vector (list of floats)
```

**Model:** all-MiniLM-L6-v2
- Runs locally on CPU
- 384 dimensions
- ~80MB model size
- Fast: ~100 embeddings/second on modern CPU

**Code pattern:**

```python
from sentence_transformers import SentenceTransformer

# Initialize once at startup
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def embed_text(text: str) -> list[float]:
    """Generate embedding vector for text."""
    vector = embedding_model.encode(text)
    return vector.tolist()

def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed multiple texts efficiently."""
    vectors = embedding_model.encode(texts)
    return vectors.tolist()
```

**Storage in LanceDB:**

```python
import lancedb

db = lancedb.connect("./data/vectors")

# Create table with schema
table = db.create_table("canon_passages", data=[
    {
        "id": "passage_001",
        "niche_id": 1,
        "source_id": 1,
        "text": "In the beginning Eru, the One, who in the Elvish tongue is named Ilúvatar...",
        "chapter": "Ainulindalë",
        "page": 3,
        "characters": ["Eru", "Ilúvatar"],
        "locations": [],
        "themes": ["creation", "cosmology"],
        "era": "Before Time",
        "vector": embed_text("In the beginning Eru, the One...")
    }
])
```

---

### Step 5: Searching

**Purpose:** Find semantically similar content.

```
Input:  Query string
Output: Ranked list of relevant chunks
```

**Basic search:**

```python
def search_canon(query: str, niche_id: int = None, limit: int = 10) -> list[dict]:
    """Semantic search across canon passages."""
    
    table = db.open_table("canon_passages")
    
    # Embed the query
    query_vector = embed_text(query)
    
    # Search with optional filter
    search = table.search(query_vector)
    
    if niche_id:
        search = search.where(f"niche_id = {niche_id}")
    
    results = search.limit(limit).to_list()
    
    return results
```

**Filtered search (cross-niche example):**

```python
def search_theme_across_niches(theme: str, niches: list[int] = None) -> list[dict]:
    """Find content about a theme across multiple niches."""
    
    table = db.open_table("canon_passages")
    
    query_vector = embed_text(theme)
    
    search = table.search(query_vector)
    
    if niches:
        niche_filter = " OR ".join([f"niche_id = {n}" for n in niches])
        search = search.where(f"({niche_filter})")
    
    return search.limit(20).to_list()

# Example: "tragic heroes" across LOTR and ASOIAF
results = search_theme_across_niches("tragic hero who fell to temptation", niches=[1, 2])
```

---

### Step 6: Content Generation

**Purpose:** Use retrieved context to generate video content.

```
Input:  Topic + retrieved passages + competitor analysis
Output: Script drafts, outlines, ideas
```

**This step happens via:**
1. Claude Projects (interactive) — for ideation and script iteration
2. Claude API (automated) — for bulk generation

**Context assembly:**

```python
def build_script_context(topic: str, niche_id: int) -> str:
    """Assemble context for script generation."""
    
    # Get relevant canon passages
    canon_results = search_canon(topic, niche_id, limit=10)
    
    # Get competitor coverage
    competitor_results = search_transcripts(topic, niche_id, limit=5)
    
    context = f"""
## Canon Sources (use for accuracy)

{format_passages(canon_results)}

## How Competitors Covered This Topic

{format_competitor_coverage(competitor_results)}

## Topic
{topic}
"""
    return context
```

**For Claude Projects:**
- Upload context as a file to the project
- Or paste into the conversation

**For API automation:**

```python
SCRIPT_PROMPT = """
You are writing a script for a YouTube video about {topic} in the {niche_name} niche.

Use the following source material for accuracy. Cite sources where relevant.

{context}

Write a {length}-minute script with:
1. A strong hook (first 30 seconds)
2. Clear structure with transitions
3. Interesting details from the sources
4. A conclusion that encourages engagement

Format with clear section markers for the video editor.
"""
```

---

## Full Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         COMPLETE PIPELINE                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  CANON INGESTION                                                            │
│  ───────────────                                                            │
│  PDF/Text ──► Extract ──► Chunk ──► Embed ──► Store in LanceDB             │
│                  │                                                          │
│                  └──► Extract glossary terms ──► Store in SQLite           │
│                                                                              │
│  COMPETITOR SCRAPING                                                        │
│  ───────────────────                                                        │
│  Channel ──► Get video list ──► Store metadata in SQLite                   │
│                   │                                                         │
│                   └──► For each video:                                      │
│                           │                                                 │
│                           ├──► Download thumbnail ──► Store                │
│                           │                                                 │
│                           └──► Get transcript ──► Clean with LLM           │
│                                                      │                      │
│                                                      └──► Chunk ──► Embed  │
│                                                                 │           │
│                                                                 └──► Store │
│                                                                             │
│  CONTENT CREATION                                                           │
│  ────────────────                                                           │
│  Topic idea ──► Search canon ──► Search competitors ──► Build context      │
│                                                              │              │
│                                                              └──► Generate │
│                                                                    script  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Configuration

**Environment variables / settings:**

```python
# config/settings.py

# API Keys
ANTHROPIC_API_KEY = "sk-ant-..."
YOUTUBE_API_KEY = "AIza..."

# Paths
DATA_DIR = "./data"
SQLITE_PATH = f"{DATA_DIR}/content.db"
LANCEDB_PATH = f"{DATA_DIR}/vectors"
SOURCES_DIR = f"{DATA_DIR}/sources"
ASSETS_DIR = f"{DATA_DIR}/assets"
THUMBNAILS_DIR = f"{DATA_DIR}/thumbnails"

# Embedding
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSIONS = 384

# Chunking
CHUNK_SIZE = 2000  # characters
CHUNK_OVERLAP = 200

# LLM
CLEANING_MODEL = "claude-3-haiku-20240307"
GENERATION_MODEL = "claude-3-5-sonnet-20241022"
```

---

## Error Handling

**Common issues and solutions:**

| Issue | Cause | Solution |
|-------|-------|----------|
| Transcript unavailable | Video has no captions | Mark `has_transcript = False`, skip |
| Rate limited | Too many API calls | Implement exponential backoff |
| Cleaning fails | LLM error | Retry once, then store raw with flag |
| PDF extraction fails | Scanned/image PDF | Use OCR (pytesseract) or skip |
| Embedding OOM | Batch too large | Reduce batch size |

**Retry pattern:**

```python
import time

def with_retry(func, max_retries=3, base_delay=1):
    """Retry a function with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)
            time.sleep(delay)
```

---

## Batch Processing

For efficiency when processing many items:

```python
def process_channel_videos(channel_id: int, batch_size: int = 10):
    """Process all videos from a channel in batches."""
    
    # Get unprocessed videos
    videos = get_unprocessed_videos(channel_id)
    
    for i in range(0, len(videos), batch_size):
        batch = videos[i:i + batch_size]
        
        # Fetch transcripts
        transcripts = [get_transcript(v.youtube_id) for v in batch]
        
        # Clean in parallel (if using async) or sequential
        cleaned = [clean_transcript(t, glossary, niche_name) for t in transcripts]
        
        # Chunk all
        all_chunks = []
        for video, transcript in zip(batch, cleaned):
            chunks = chunk_text(transcript)
            for idx, chunk in enumerate(chunks):
                all_chunks.append({
                    "video_id": video.id,
                    "chunk_index": idx,
                    "text": chunk
                })
        
        # Embed in batch (much faster)
        texts = [c["text"] for c in all_chunks]
        vectors = embed_batch(texts)
        
        # Store
        for chunk, vector in zip(all_chunks, vectors):
            chunk["vector"] = vector
        
        store_transcript_chunks(all_chunks)
        
        # Mark videos as processed
        mark_videos_processed([v.id for v in batch])
```
