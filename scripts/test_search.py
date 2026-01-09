"""
Test script for semantic search.

Tests searching canon passages and transcripts for specific queries.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline.search import search_canon, search_transcripts, search_both, format_result
from src.database.niches import get_all_niches
from src.pipeline.vectorstore import get_stats


def test_search():
    """Test semantic search across canon passages and transcripts."""
    print("=" * 80)
    print("SEMANTIC SEARCH TEST")
    print("=" * 80)
    print()

    # Check vector database status
    stats = get_stats()
    print("Vector Database Status:")
    if not stats['tables']:
        print("  No tables found - vector database is empty")
        print()
        print("To populate the database:")
        print("  1. Add PDFs to data/sources/")
        print("  2. Run: python scripts/test_ingest.py")
        print("  3. Run: python scripts/test_chunking.py")
        return

    for table in stats['tables']:
        print(f"  Table '{table['name']}': {table['count']} records")
    print()

    # Get niches
    niches = get_all_niches()
    if not niches:
        print("ERROR: No niches found")
        return

    niche = niches[0]
    print(f"Searching in niche: {niche['name']} (ID: {niche['id']})")
    print()

    # Test queries
    test_queries = [
        "Gandalf",
        "ring of power",
        "journey to Mordor",
        "Bilbo Baggins"
    ]

    for query in test_queries:
        print("=" * 80)
        print(f"QUERY: {query}")
        print("=" * 80)
        print()

        # Search canon passages
        print("-" * 80)
        print("CANON PASSAGES")
        print("-" * 80)

        canon_results = search_canon(query, niche_id=niche['id'], limit=3)

        if not canon_results:
            print("No canon passages found.")
            print("(Have you run 'python scripts/test_chunking.py' yet?)")
        else:
            print(f"Found {len(canon_results)} result(s):")
            print()

            for i, result in enumerate(canon_results, 1):
                print(f"Result {i}:")
                print(format_result(result, result_type="canon"))
                print()

        # Search transcripts
        print("-" * 80)
        print("COMPETITOR TRANSCRIPTS")
        print("-" * 80)

        transcript_results = search_transcripts(query, niche_id=niche['id'], limit=3)

        if not transcript_results:
            print("No transcript chunks found.")
            print("(Transcript chunking not yet implemented)")
        else:
            print(f"Found {len(transcript_results)} result(s):")
            print()

            for i, result in enumerate(transcript_results, 1):
                print(f"Result {i}:")
                print(format_result(result, result_type="transcript"))
                print()

        print()

    # Summary
    print("=" * 80)
    print("SEARCH TEST COMPLETE")
    print("=" * 80)
    print()


def interactive_search():
    """Interactive search mode for testing queries."""
    print("=" * 80)
    print("INTERACTIVE SEARCH")
    print("=" * 80)
    print()
    print("Enter search queries to test semantic search.")
    print("Type 'quit' to exit.")
    print()

    # Get niche
    niches = get_all_niches()
    if not niches:
        print("ERROR: No niches found")
        return

    niche = niches[0]
    print(f"Searching in: {niche['name']}")
    print()

    while True:
        try:
            query = input("Search query: ").strip()

            if query.lower() in ['quit', 'exit', 'q']:
                break

            if not query:
                continue

            print()
            print("-" * 80)

            # Search canon
            results = search_canon(query, niche_id=niche['id'], limit=5)

            if results:
                print(f"Found {len(results)} canon passage(s):")
                print()

                for i, result in enumerate(results, 1):
                    print(f"{i}. {format_result(result, result_type='canon')}")
                    print()
            else:
                print("No results found.")

            print("-" * 80)
            print()

        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except EOFError:
            break


if __name__ == "__main__":
    # Check if interactive mode requested
    if len(sys.argv) > 1 and sys.argv[1] in ['-i', '--interactive']:
        interactive_search()
    else:
        test_search()
