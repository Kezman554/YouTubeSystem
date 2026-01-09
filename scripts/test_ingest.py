"""
Test script for PDF ingestion.

Tests ingesting PDFs into the canon_sources table.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline.ingest import ingest_pdf
from src.database.niches import get_all_niches, get_niche
from src.database.canon_sources import get_sources_by_niche


def list_available_niches():
    """Display available niches."""
    niches = get_all_niches()
    print("Available niches:")
    print()
    if not niches:
        print("  No niches found. Create one first!")
        return []

    for niche in niches:
        print(f"  ID {niche['id']}: {niche['name']} ({niche['slug']})")
    print()
    return niches


def test_ingest():
    """Test PDF ingestion."""
    print("=" * 80)
    print("PDF INGESTION TEST")
    print("=" * 80)
    print()

    # Show available niches
    niches = list_available_niches()
    if not niches:
        return

    # Get niche ID (use Middle-earth by default)
    middle_earth_niche = None
    for niche in niches:
        if niche['slug'] == 'middle-earth':
            middle_earth_niche = niche
            break

    if not middle_earth_niche:
        print("ERROR: Middle-earth niche not found")
        print("Please create it first or specify a different niche")
        return

    niche_id = middle_earth_niche['id']
    print(f"Using niche: {middle_earth_niche['name']} (ID: {niche_id})")
    print()

    # Check for PDFs in data/sources/
    sources_dir = Path(__file__).parent.parent / "data" / "sources"
    sources_dir.mkdir(parents=True, exist_ok=True)

    print(f"Looking for PDFs in: {sources_dir}")
    print()

    pdf_files = list(sources_dir.glob("*.pdf"))

    if not pdf_files:
        print("No PDF files found in data/sources/")
        print()
        print("To test ingestion:")
        print("  1. Place PDF files in data/sources/")
        print("  2. Run this script again")
        print()
        print("Example files to add:")
        print("  - The Hobbit.pdf")
        print("  - The Lord of the Rings.pdf")
        print("  - The Silmarillion.pdf")
        return

    print(f"Found {len(pdf_files)} PDF file(s):")
    for pdf in pdf_files:
        print(f"  - {pdf.name}")
    print()

    # Ingest each PDF
    for pdf_path in pdf_files:
        print("-" * 80)
        print(f"Ingesting: {pdf_path.name}")
        print("-" * 80)

        # Extract title and author from filename
        # Expected format: "Title - Author.pdf" or just "Title.pdf"
        filename = pdf_path.stem  # Remove .pdf extension

        if " - " in filename:
            title, author = filename.split(" - ", 1)
        else:
            title = filename
            author = "J.R.R. Tolkien"  # Default for Middle-earth content

        print(f"Title: {title}")
        print(f"Author: {author}")
        print()

        try:
            source_id = ingest_pdf(
                file_path=str(pdf_path),
                niche_id=niche_id,
                title=title,
                author=author,
                priority=5  # High priority for canonical books
            )

            print()
            print(f"[OK] Successfully ingested: {title}")
            print(f"[OK] Source ID: {source_id}")
            print()

        except Exception as e:
            print(f"[ERROR] Failed to ingest {title}: {e}")
            print()

    # Show summary
    print("=" * 80)
    print("INGESTION COMPLETE")
    print("=" * 80)
    print()

    sources = get_sources_by_niche(niche_id)
    print(f"Total canon sources for {middle_earth_niche['name']}: {len(sources)}")
    print()

    if sources:
        print("Sources:")
        for source in sources:
            ingested_status = "[INGESTED]" if source['ingested'] else "[NOT INGESTED]"
            print(f"  {ingested_status} {source['title']} by {source['author']}")
        print()


if __name__ == "__main__":
    test_ingest()
