"""Quick script to check database contents."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.niches import get_all_niches

print("Existing niches:")
print()
niches = get_all_niches()
if not niches:
    print("  No niches found!")
else:
    for niche in niches:
        print(f"  ID {niche['id']}: {niche['name']} ({niche['slug']})")
