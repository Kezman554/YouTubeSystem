# Semantic Search Guide

## What's Been Created

The semantic search system for finding relevant content:

1. **src/pipeline/search.py** - Search functions:
   - `search_canon()` - Search canon passages (books, docs)
   - `search_transcripts()` - Search competitor transcript chunks
   - `search_both()` - Search both at once
   - `format_result()` - Pretty-print results

2. **scripts/test_search.py** - Test script with:
   - Predefined test queries
   - Interactive search mode
   - Formatted results with relevance scores

## How It Works

**Semantic Search** finds content by meaning, not just keywords:
- "Gandalf" finds passages about Gandalf, even without the name
- "ring of power" finds relevant passages about rings, power, corruption
- "journey to Mordor" finds travel, quest, danger passages

**Relevance Scores:**
- 100% = Perfect match
- 80-99% = Very relevant
- 60-79% = Moderately relevant
- <60% = Less relevant

## Usage

### Test Mode (Predefined Queries)

Run the test script:
```bash
python scripts/test_search.py
```

This searches for:
- "Gandalf"
- "ring of power"
- "journey to Mordor"
- "Bilbo Baggins"

### Interactive Mode

For custom queries:
```bash
python scripts/test_search.py -i
```

Then type your search queries:
```
Search query: Tell me about the Balrog
Search query: What happened at Helm's Deep?
Search query: quit
```

## Example Output

```
================================================================================
QUERY: Gandalf
================================================================================

--------------------------------------------------------------------------------
CANON PASSAGES
--------------------------------------------------------------------------------
Found 3 result(s):

Result 1:
Relevance: 94.2%
Source: The Fellowship of the Ring
Page: 42
Source ID: 1

Gandalf the Grey, who was also known as Mithrandir, was a wizard of great
power and wisdom. He traveled throughout Middle-earth, guiding and helping
the Free Peoples in their struggles...

Result 2:
Relevance: 89.7%
Source: The Two Towers
Page: 112
Source ID: 2

The wizard stood upon the bridge, his staff held high. "You cannot pass!"
he cried to the Balrog. "I am a servant of the Secret Fire..."
```

## Prerequisites

Before search works, you need data:

1. **Add PDFs** to `data/sources/`:
   ```
   The Hobbit - J.R.R. Tolkien.pdf
   The Lord of the Rings - J.R.R. Tolkien.pdf
   ```

2. **Ingest PDFs:**
   ```bash
   python scripts/test_ingest.py
   ```

3. **Chunk and embed:**
   ```bash
   python scripts/test_chunking.py
   ```

4. **Now search works!**
   ```bash
   python scripts/test_search.py
   ```

## Programmatic Usage

Use in your own code:

```python
from src.pipeline.search import search_canon, format_result

# Simple search
results = search_canon("Gandalf", niche_id=1, limit=5)

# Display results
for result in results:
    print(format_result(result, result_type="canon"))
    print()

# Get raw data
for result in results:
    print(f"Relevance: {1 - result['_distance']:.1%}")
    print(f"Text: {result['text']}")
    print(f"Source: {result['source_id']}")
```

## Technical Details

**Vector Search:**
- Converts query to 384-dim embedding
- Finds most similar chunks in LanceDB
- Returns sorted by relevance (cosine similarity)

**Filtering:**
- Can filter by `niche_id`
- Limits results to top N matches
- Configurable result count

**Performance:**
- Sub-second search on typical databases
- Scales to millions of chunks
- Local, no API costs

## Next Steps

After testing canon search:
1. Implement transcript chunking
2. Process competitor transcripts
3. Enable `search_transcripts()` function
4. Compare how competitors explain topics
