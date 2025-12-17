# Content Intelligence System

A local-first platform for researching, planning, and producing faceless YouTube content across multiple niches.

## Project Goal

Build a system that helps Nick create profitable faceless YouTube channels by:
- Tracking competitor videos and identifying content gaps
- Storing and searching source material (books, wikis, docs)
- Cleaning auto-generated transcripts
- Generating video ideas backed by data
- Managing the production pipeline

Target: £2-3k/month revenue within 12-18 months.

## Tech Stack

| Component | Choice | Why |
|-----------|--------|-----|
| Database | SQLite | Local, simple, no server |
| Vector DB | LanceDB | Local, Python-native |
| Backend | FastAPI | Lightweight |
| Frontend | Streamlit | Fast to build |
| Embeddings | all-MiniLM-L6-v2 | Runs on CPU |
| LLM | Claude API (Haiku/Sonnet) | Quality + cost balance |

**Hardware constraint:** 4GB VRAM laptop. No local LLMs or image generation until GPU upgrade.

## Architecture Docs

Before implementing any feature, read the relevant doc:

- `docs/SYSTEM_OVERVIEW.md` — Architecture decisions, costs, phases
- `docs/DATA_MODEL.md` — Database schema (13 SQLite tables, 2 LanceDB collections)
- `docs/PIPELINE.md` — Processing flow, code patterns, error handling
- `docs/UI_SPEC.md` — Dashboard screens, build order

## Constraints

**Do not suggest:**
- Cloud databases (PostgreSQL, cloud-hosted anything)
- Container orchestration (Docker, Kubernetes)
- Cloud services (AWS, GCP, Azure)
- Heavy frameworks before MVP works

**Always:**
- Use type hints
- Write tests alongside features
- Handle errors for external API calls
- Commit frequently with clear messages

## Builder Context

Nick is a beginner coder learning through building. Explain decisions clearly. Build incrementally. Prefer simple solutions.
