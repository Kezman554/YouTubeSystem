# Pipeline Test Instructions

## What's Been Created

The complete chunking and embedding pipeline:

1. **src/pipeline/chunk.py** - Text chunking with sentence-aware overlap
2. **src/pipeline/embed.py** - Embeddings using all-MiniLM-L6-v2 (local, free)
3. **src/pipeline/vectorstore.py** - LanceDB storage for semantic search
4. **scripts/test_chunking.py** - Complete pipeline test

## How to Test

### Step 1: Add Your PDFs

Place your PDFs in `data/sources/`:
```bash
data/sources/
  The Hobbit - J.R.R. Tolkien.pdf
  The Lord of the Rings - J.R.R. Tolkien.pdf
```

### Step 2: Ingest PDFs

Run the ingestion script:
```bash
python scripts/test_ingest.py
```

This will:
- Extract text from each PDF
- Store in `canon_sources` table
- Mark as ready for processing

### Step 3: Chunk and Embed

Run the chunking pipeline:
```bash
python scripts/test_chunking.py
```

This will:
1. Load the first non-ingested source
2. Extract text from PDF
3. Chunk into ~2000 character segments
4. Generate 384-dim embeddings (local, free)
5. Store in LanceDB
6. Show count of chunks created

Run it again to process the next source.

## Technical Details

**Chunking:**
- Chunk size: 2000 chars (~500 tokens)
- Overlap: 200 chars (~50 tokens)
- Method: Sentence-aware (no mid-sentence cuts)

**Embeddings:**
- Model: all-MiniLM-L6-v2
- Dimensions: 384
- Speed: ~100 chunks/second
- Runs locally on CPU (no API costs)

**Storage:**
- Database: LanceDB (local vector DB)
- Location: `data/vectors/`
- Table: `canon_passages`

## What You'll See

When you run `test_chunking.py`, you'll see:
```
Processing: The Hobbit
Step 1: Extracting text from PDF...
  ✓ Extracted 305 pages
  ✓ Total characters: 287,234

Step 2: Chunking text...
  ✓ Created 156 chunks
  ✓ Average chunk size: 1841 characters

Step 3: Generating embeddings...
  ✓ Generated 156 embedding vectors
  ✓ Vector dimension: 384

Step 4: Storing in LanceDB...
  ✓ Stored 156 chunks in vector database

PIPELINE COMPLETE
Chunks created: 156
```
