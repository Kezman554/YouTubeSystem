# Glossary Extraction Guide

## What's Been Created

The glossary extraction system for building term databases:

1. **src/pipeline/glossary.py** - Core functions:
   - `extract_proper_nouns()` - Finds capitalized terms in text
   - `extract_and_store_glossary()` - Extracts and stores terms
   - `classify_term_type()` - Auto-classifies term types
   - `add_manual_term()` - Manually add terms with phonetic hints
   - `get_glossary_stats()` - Statistics about glossary

2. **scripts/test_glossary.py** - Extraction test script

## Purpose

The glossary serves two main purposes:

1. **Transcript Cleaning** - Fix auto-caption errors
   - "borrow mere" → "Boromir"
   - "silver mill" → "Silmaril"
   - "gahn dalf" → "Gandalf"

2. **Auto-Tagging** - Tag content with relevant terms
   - Identify characters, locations, items mentioned
   - Enable filtered searches by topic

## How It Works

### Automatic Extraction

The system scans canon text for proper nouns:

1. **Finds capitalized words** (not at sentence start)
2. **Groups multi-word terms** (e.g., "Mount Doom")
3. **Counts frequency** (minimum threshold: 3 occurrences)
4. **Auto-classifies** type based on heuristics:
   - Ends with "shire", "mountain" → location
   - Contains "ring", "sword" → item
   - Single word → likely character
   - Has "of the" → concept/title

### Term Types

- **character** - Names of people, beings
- **location** - Places, realms, geographical features
- **item** - Objects, artifacts, weapons
- **concept** - Ideas, titles, abstract terms
- **unknown** - Needs manual classification

## Usage

### Step 1: Ingest Canon Sources

First, add your reference material:

```bash
# Add PDFs to data/sources/
# The Hobbit - J.R.R. Tolkien.pdf
# The Lord of the Rings - J.R.R. Tolkien.pdf

# Ingest them
python scripts/test_ingest.py
```

### Step 2: Extract Glossary

Run the extraction script:

```bash
python scripts/test_glossary.py
```

This will:
1. Load the first canon source
2. Extract text from PDF
3. Find all proper nouns (3+ occurrences)
4. Classify them automatically
5. Store in glossary table
6. Show statistics

### Step 3: Review and Refine

The auto-classification is a starting point. Review and improve:

```python
from src.database.glossary import update_glossary_entry

# Reclassify a term
update_glossary_entry(
    entry_id=5,
    term_type="location",  # Was "unknown"
    description="The dark fortress of Sauron"
)
```

### Step 4: Add Phonetic Hints

For transcript cleaning, add phonetic variations:

```python
from src.pipeline.glossary import add_manual_term

# Add term with phonetic hints
add_manual_term(
    niche_id=1,
    term="Gandalf",
    term_type="character",
    phonetic_hints="gan-dalf,gahn-dalf,gan-dolf,gand-off",
    aliases='["Mithrandir", "The Grey Wizard", "The White Rider"]',
    description="Istari wizard, member of the Fellowship"
)
```

## Example Output

```
================================================================================
GLOSSARY EXTRACTION TEST
================================================================================

Niche: Middle-earth (ID: 1)

Found 1 canon source(s):
  - The Hobbit by J.R.R. Tolkien

--------------------------------------------------------------------------------
Extracting glossary from: The Hobbit
--------------------------------------------------------------------------------

Step 1: Extracting text from PDF...
  ✓ Extracted 305 pages
  ✓ Total characters: 287,234

Step 2: Analyzing text for proper nouns...
  ✓ Found 89 terms (appearing 10+ times)

  Top 20 terms by frequency:
    Bilbo: 452 occurrences
    Gandalf: 287 occurrences
    Thorin: 198 occurrences
    Smaug: 156 occurrences
    Gollum: 142 occurrences
    Misty Mountains: 87 occurrences
    Lonely Mountain: 76 occurrences
    ...

Step 3: Storing terms in glossary...
  Using minimum frequency: 3 occurrences

  ✓ Added 234 new terms
  ✓ Skipped 0 existing terms

--------------------------------------------------------------------------------
GLOSSARY STATISTICS
--------------------------------------------------------------------------------
Total terms: 234
  Characters: 87
  Locations: 42
  Items: 18
  Concepts: 31
  Unknown: 56

--------------------------------------------------------------------------------
SAMPLE GLOSSARY ENTRIES
--------------------------------------------------------------------------------

CHARACTERS (showing up to 10):
  - Bilbo: Appears 452 times in source
  - Gandalf: Appears 287 times in source
  - Thorin: Appears 198 times in source
  - Smaug: Appears 156 times in source
  - Gollum: Appears 142 times in source
  ...

LOCATIONS (showing up to 10):
  - Misty Mountains: Appears 87 times in source
  - Lonely Mountain: Appears 76 times in source
  - Rivendell: Appears 64 times in source
  ...
```

## Database Schema

Terms are stored in the `glossary` table:

```sql
CREATE TABLE glossary (
    id INTEGER PRIMARY KEY,
    niche_id INTEGER NOT NULL,
    term TEXT NOT NULL,
    term_type TEXT,  -- character/location/item/concept
    phonetic_hints TEXT,  -- "gan-dalf,gahn-dalf"
    aliases TEXT,  -- JSON: ["Mithrandir", "The Grey"]
    description TEXT,
    source_id INTEGER,
    created_at TIMESTAMP
);
```

## Limitations

**Auto-classification is not perfect:**
- Some terms may be misclassified
- Multi-word proper nouns may be split
- Common names might be missed
- Fantasy terms don't follow normal rules

**Manual review recommended:**
- Check "unknown" terms first
- Add phonetic hints for audio transcription errors
- Add aliases for nicknames and alternate names
- Refine descriptions

## Next Steps

1. **Extract from all sources**
   - Run test script for each book/doc
   - Build comprehensive term database

2. **Add phonetic hints**
   - Research common mishearings
   - Add variations for transcript cleaning

3. **Implement transcript cleaning**
   - Use glossary to fix auto-caption errors
   - Match phonetic hints to errors

4. **Use for auto-tagging**
   - Tag video transcripts with glossary terms
   - Enable search by character/location/topic
