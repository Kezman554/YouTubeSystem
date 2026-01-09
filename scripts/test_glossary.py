"""
Test script for glossary extraction.

Extracts proper nouns and terms from canon sources and stores them
in the glossary table.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.canon_sources import get_sources_by_niche
from src.database.niches import get_all_niches
from src.database.glossary import get_glossary_by_niche
from src.pipeline.ingest import extract_pdf
from src.pipeline.glossary import (
    extract_proper_nouns,
    extract_and_store_glossary,
    add_manual_term,
    get_glossary_stats
)


def test_glossary_extraction():
    """Test glossary extraction from canon sources."""
    print("=" * 80)
    print("GLOSSARY EXTRACTION TEST")
    print("=" * 80)
    print()

    # Get niches
    niches = get_all_niches()
    if not niches:
        print("ERROR: No niches found")
        return

    niche = niches[0]
    print(f"Niche: {niche['name']} (ID: {niche['id']})")
    print()

    # Get canon sources
    sources = get_sources_by_niche(niche['id'])

    if not sources:
        print("ERROR: No canon sources found")
        print("Run 'python scripts/test_ingest.py' first to add sources")
        return

    print(f"Found {len(sources)} canon source(s):")
    for source in sources:
        print(f"  - {source['title']} by {source['author']}")
    print()

    # Process first source
    source = sources[0]
    print("-" * 80)
    print(f"Extracting glossary from: {source['title']}")
    print("-" * 80)
    print()

    # Extract text
    print("Step 1: Extracting text from PDF...")
    file_path = source['file_path']

    if not file_path or not Path(file_path).exists():
        print(f"ERROR: File not found: {file_path}")
        return

    try:
        full_text, metadata = extract_pdf(file_path)
        print(f"  ✓ Extracted {metadata['page_count']} pages")
        print(f"  ✓ Total characters: {len(full_text):,}")
        print()
    except Exception as e:
        print(f"  ✗ Failed to extract: {e}")
        return

    # Extract proper nouns (preview)
    print("Step 2: Analyzing text for proper nouns...")
    try:
        # Use higher frequency threshold for preview
        terms_preview = extract_proper_nouns(full_text, min_frequency=10)
        print(f"  ✓ Found {len(terms_preview)} terms (appearing 10+ times)")
        print()

        if terms_preview:
            print("  Top 20 terms by frequency:")
            sorted_terms = sorted(terms_preview.items(), key=lambda x: x[1], reverse=True)
            for term, count in sorted_terms[:20]:
                print(f"    {term}: {count} occurrences")
            print()

    except Exception as e:
        print(f"  ✗ Failed to extract terms: {e}")
        return

    # Store in glossary
    print("Step 3: Storing terms in glossary...")
    print(f"  Using minimum frequency: 3 occurrences")
    print()

    try:
        new_count, skipped_count = extract_and_store_glossary(
            text=full_text,
            niche_id=niche['id'],
            source_id=source['id'],
            min_frequency=3,
            auto_classify=True
        )

        print(f"  ✓ Added {new_count} new terms")
        print(f"  ✓ Skipped {skipped_count} existing terms")
        print()

    except Exception as e:
        print(f"  ✗ Failed to store terms: {e}")
        return

    # Show glossary stats
    print("-" * 80)
    print("GLOSSARY STATISTICS")
    print("-" * 80)

    stats = get_glossary_stats(niche['id'])

    print(f"Total terms: {stats['total']}")
    print(f"  Characters: {stats['character']}")
    print(f"  Locations: {stats['location']}")
    print(f"  Items: {stats['item']}")
    print(f"  Concepts: {stats['concept']}")
    print(f"  Unknown: {stats['unknown']}")
    print()

    # Show sample entries by type
    print("-" * 80)
    print("SAMPLE GLOSSARY ENTRIES")
    print("-" * 80)
    print()

    for term_type in ['character', 'location', 'item', 'concept']:
        terms = get_glossary_by_niche(niche['id'], term_type=term_type)
        if terms:
            print(f"{term_type.upper()}S (showing up to 10):")
            for term in terms[:10]:
                desc = term.get('description', '')
                print(f"  - {term['term']}: {desc}")
            print()

    # Demo manual term addition
    print("-" * 80)
    print("MANUAL TERM ADDITION EXAMPLE")
    print("-" * 80)
    print()
    print("You can manually add terms with phonetic hints:")
    print()
    print("Example:")
    print("  >>> from src.pipeline.glossary import add_manual_term")
    print("  >>> add_manual_term(")
    print("  ...     niche_id=1,")
    print("  ...     term='Gandalf',")
    print("  ...     term_type='character',")
    print("  ...     phonetic_hints='gan-dalf,gahn-dalf,gan-dolf',")
    print("  ...     aliases='[\"Mithrandir\", \"The Grey Wizard\"]',")
    print("  ...     description='Istari wizard, member of the Fellowship'")
    print("  ... )")
    print()

    # Summary
    print("=" * 80)
    print("EXTRACTION COMPLETE")
    print("=" * 80)
    print()
    print(f"Source: {source['title']}")
    print(f"New terms added: {new_count}")
    print(f"Total glossary size: {stats['total']} terms")
    print()
    print("Next steps:")
    print("  1. Review unknown terms and reclassify manually")
    print("  2. Add phonetic hints for transcript cleaning")
    print("  3. Process more canon sources")
    print()


if __name__ == "__main__":
    test_glossary_extraction()
