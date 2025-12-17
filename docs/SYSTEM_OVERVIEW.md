# Content Intelligence System - Overview

## Purpose

A self-hosted, multi-niche content intelligence and production platform for YouTube creators. Designed to support faceless channel creation at scale, from competitor research through to content publication.

## Owner Profile

- **Experience Level:** Beginner coder, learning through building
- **IDE:** Visual Studio Code
- **Current Hardware:** 2023 Dell laptop, Core i7, 16GB RAM, 4GB VRAM
- **Future Hardware:** Planning workstation upgrade (target: RTX 3090 24GB or RTX 4070 Ti 16GB)
- **Subscriptions:** Claude Pro
- **Goal:** Build multiple faceless YouTube channels generating £2-3k/month within 12-18 months

## Goals

1. Systematize niche discovery and evaluation
2. Track competitor channels and identify content gaps
3. Store and semantically search source material (books, docs, wikis)
4. Clean and analyse competitor transcripts
5. Generate content ideas informed by data
6. Assist script drafting with proper citations
7. Manage visual assets and track usage
8. Monitor own channel performance
9. Support cross-platform content (Shorts, TikTok, Twitter)

## Architecture Decisions

### Stack

| Layer | Technology | Reason |
|-------|------------|--------|
| Structured Database | SQLite | Simple, file-based, reliable, no server needed |
| Vector Database | LanceDB | Local-first, good filtering, Python-native |
| Backend | Python + FastAPI | Lightweight, good LLM library support |
| Frontend | Streamlit (Phase 1) | Fast to build, Python-native, upgradeable later |
| Automation (Later) | n8n on Raspberry Pi | Self-hosted workflows, no subscription |

### LLM Strategy

| Task | Tool | Runs | Cost |
|------|------|------|------|
| Transcript cleaning | Claude Haiku API or GPT-4o-mini | Cloud | ~£0.001 per transcript |
| Embeddings | all-MiniLM-L6-v2 or nomic-embed-text | Locally on CPU | Free |
| Interactive ideation/scripting | Claude Projects | Browser | Included in Pro |
| Automated content tasks | Claude Haiku/Sonnet API | Cloud | Variable |

### Image Generation Strategy

| Phase | Tool | Cost |
|-------|------|------|
| Starting | Leonardo.ai free tier | Free |
| Growing | Midjourney or SD API | £10/month or per-image |
| Hardware acquired | Local Stable Diffusion (SDXL) | Free (electricity only) |

### Hardware Constraints (Current)

- 4GB VRAM limits local LLM use
- Embedding models run fine on CPU
- No local image generation until upgrade
- All heavy LLM work via API for now

### Hardware Upgrade Targets

| GPU | VRAM | Used Price | Unlocks |
|-----|------|------------|---------|
| RTX 3060 12GB | 12GB | £150-200 | Local 7B LLMs, SDXL (slow) |
| RTX 3090 24GB | 24GB | £500-700 | Local 13B LLMs, SDXL comfortable |
| RTX 4070 Ti 16GB | 16GB | £400-500 | Good balance of performance/efficiency |

## System Phases

### Phase 1: Scout (Later Build)
- Discover profitable niches suitable for faceless content
- Evaluate competition and feasibility
- Score by CPM potential, saturation, resource requirements

### Phase 2: Niche Setup
- Configure new niche (name, taxonomy, tags)
- Add competitor channels to track
- Ingest source material (canon)
- Build glossary for transcript cleaning

### Phase 3: Intelligence
- Monitor competitor uploads and performance
- Detect trends and content gaps
- Semantic search across canon and transcripts
- Thumbnail analysis
- Cross-niche queries

### Phase 4: Production
- Ideation: Generate video ideas from data
- Scripting: Structure and draft with citations
- Asset management: Track images, avoid reuse
- Publishing: Track across platforms

## Dashboard Screens

1. **Home** - Overview stats, recent activity, alerts
2. **Niche Setup** - Manage niches, sources, competitors, glossaries
3. **Competitive Intel** - Competitor videos, topics, gaps, thumbnails
4. **Research** - Semantic search across all stored content
5. **Ideation** - LLM-powered idea generation
6. **Production** - Video pipeline from idea to published
7. **Asset Library** - Images, usage tracking, gap identification
8. **My Analytics** - Own channel performance, cross-platform tracking
9. **Settings** - API keys, schedules, database admin
10. **Scout** (Phase 2) - Niche discovery and evaluation

## Key Design Principles

1. **Niche-agnostic:** System works for any topic (fiction, crypto, cooking, etc.)
2. **Cross-niche capable:** Can query across multiple niches (e.g., "compare swordsmen across fantasy universes")
3. **Cost-conscious:** Local where possible, cheap APIs where necessary
4. **Upgrade-ready:** Architecture supports moving to local LLMs when hardware allows
5. **Maximum automation:** Reduce manual work while maintaining quality

## Estimated Monthly Costs (Current Hardware)

| Item | Cost |
|------|------|
| Transcript cleaning (200 videos) | £0.20 |
| API content tasks | £2-5 |
| Embeddings | Free |
| Database/Search | Free |
| Claude Pro (existing) | Already subscribed |
| Image generation (free tier) | Free |
| **Total additional** | **~£3-6/month** |

## File Structure (Planned)

```
content-intelligence-system/
├── data/
│   ├── content.db              # SQLite database
│   ├── vectors/                # LanceDB storage
│   ├── sources/                # PDF/text source files
│   ├── assets/                 # Generated images
│   └── thumbnails/             # Downloaded/created thumbnails
├── src/
│   ├── database/               # DB setup and queries
│   ├── scrapers/               # YouTube scraping
│   ├── pipeline/               # Cleaning, chunking, embedding
│   ├── api/                    # FastAPI backend
│   └── ui/                     # Streamlit frontend
├── config/
│   └── settings.py             # API keys, paths, settings
├── glossaries/                 # Per-niche term lists
└── docs/                       # Reference documentation
```

## Reference Documents

- **SYSTEM_OVERVIEW.md** (this file) - Architecture and decisions
- **DATA_MODEL.md** - Database schema details
- **PIPELINE.md** - Processing flow from scrape to publish
- **UI_SPEC.md** - Screen designs and features

## Starting Channels (Planned)

1. **LOTR / Tolkien Lore** - Passion project, learning ground, AI imagery heavy

## Notes

- Transcripts require cleaning due to auto-generated errors (e.g., "Boromir" → "borrow mere")
- Glossary per niche enables both cleaning and auto-tagging
- Canon sources seed the glossary automatically
- Thumbnails tracked separately for analysis and inspiration
- Asset usage tracked to prevent repetition across videos
