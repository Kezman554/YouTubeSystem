"""
Glossary extraction module.

Extracts proper nouns and terms from canon sources for transcript cleaning
and auto-tagging.
"""

import re
from typing import List, Dict, Tuple, Optional
from collections import Counter

from src.database.glossary import create_glossary_entry, search_glossary_by_term


# Common words to exclude (not proper nouns)
COMMON_WORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
    'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
    'could', 'should', 'may', 'might', 'must', 'can', 'shall', 'i', 'you',
    'he', 'she', 'it', 'we', 'they', 'them', 'their', 'this', 'that',
    'these', 'those', 'what', 'which', 'who', 'when', 'where', 'why', 'how',
    'all', 'each', 'every', 'some', 'any', 'many', 'much', 'more', 'most',
    'said', 'asked', 'told', 'came', 'went', 'saw', 'looked', 'seemed'
}


def extract_proper_nouns(text: str, min_frequency: int = 3) -> Dict[str, int]:
    """
    Extract proper nouns from text based on capitalization patterns.

    Args:
        text: Text to analyze
        min_frequency: Minimum occurrences to include (default 3)

    Returns:
        Dictionary of {term: frequency} for terms meeting minimum frequency

    Algorithm:
        1. Find capitalized words/phrases not at sentence start
        2. Filter out common words
        3. Count frequencies
        4. Return terms above threshold
    """
    # Split into sentences
    sentences = re.split(r'[.!?]+\s+', text)

    proper_nouns = []

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        # Find capitalized words (not first word of sentence)
        words = sentence.split()

        for i in range(1, len(words)):  # Start from 1 to skip sentence start
            word = words[i].strip('",\'();:')

            # Check if capitalized and not a common word
            if word and word[0].isupper() and word.lower() not in COMMON_WORDS:
                # Check for multi-word proper nouns (consecutive capitalized)
                phrase = [word]
                j = i + 1
                while j < len(words):
                    next_word = words[j].strip('",\'();:')
                    if next_word and next_word[0].isupper() and next_word.lower() not in COMMON_WORDS:
                        phrase.append(next_word)
                        j += 1
                    else:
                        break

                # Store the phrase
                proper_noun = ' '.join(phrase)
                proper_nouns.append(proper_noun)

    # Count frequencies
    frequency_counter = Counter(proper_nouns)

    # Filter by minimum frequency
    filtered = {term: count for term, count in frequency_counter.items()
                if count >= min_frequency}

    return filtered


def classify_term_type(term: str) -> str:
    """
    Attempt basic classification of term type.

    This is a simple heuristic. Manual review is recommended.

    Args:
        term: The term to classify

    Returns:
        Likely term type: "character", "location", "item", "concept", or "unknown"

    Heuristics:
        - Ends with common location suffixes -> "location"
        - Contains "of" -> often a title or concept
        - Single capitalized word -> likely character
        - Multi-word -> could be location or concept
    """
    term_lower = term.lower()

    # Location indicators
    location_suffixes = ['shire', 'land', 'realm', 'kingdom', 'city', 'town',
                         'mountain', 'forest', 'river', 'sea', 'lake', 'valley',
                         'hill', 'tower', 'gate', 'bridge', 'cave', 'island']

    for suffix in location_suffixes:
        if term_lower.endswith(suffix):
            return "location"

    # Title/concept indicators
    if ' of ' in term_lower or ' the ' in term_lower:
        # Could be a title like "King of Gondor" or item like "Ring of Power"
        if 'ring' in term_lower or 'sword' in term_lower or 'stone' in term_lower:
            return "item"
        return "concept"

    # Single word likely a character name
    if ' ' not in term:
        return "character"

    # Multi-word - default to unknown for manual review
    return "unknown"


def extract_and_store_glossary(
    text: str,
    niche_id: int,
    source_id: int,
    min_frequency: int = 3,
    auto_classify: bool = True
) -> Tuple[int, int]:
    """
    Extract terms from text and store in glossary.

    Args:
        text: Text to extract terms from
        niche_id: ID of the niche
        source_id: ID of the canon source
        min_frequency: Minimum occurrences to include (default 3)
        auto_classify: Attempt automatic term_type classification (default True)

    Returns:
        Tuple of (new_terms_added, existing_terms_skipped)

    Example:
        >>> text = "Gandalf went to Rivendell. Gandalf met Elrond..."
        >>> new, skipped = extract_and_store_glossary(text, niche_id=1, source_id=1)
        >>> print(f"Added {new} terms, skipped {skipped} existing")
    """
    # Extract proper nouns
    terms = extract_proper_nouns(text, min_frequency)

    if not terms:
        return 0, 0

    new_count = 0
    skipped_count = 0

    for term, frequency in terms.items():
        # Check if term already exists
        existing = search_glossary_by_term(niche_id, term)

        if existing:
            # Term already in glossary
            skipped_count += 1
            continue

        # Classify term type
        term_type = classify_term_type(term) if auto_classify else "unknown"

        # Create description with frequency info
        description = f"Appears {frequency} times in source"

        try:
            create_glossary_entry(
                niche_id=niche_id,
                term=term,
                term_type=term_type,
                description=description,
                source_id=source_id
            )
            new_count += 1
        except Exception as e:
            print(f"Failed to add term '{term}': {e}")

    return new_count, skipped_count


def add_manual_term(
    niche_id: int,
    term: str,
    term_type: str,
    phonetic_hints: Optional[str] = None,
    aliases: Optional[str] = None,
    description: Optional[str] = None,
    source_id: Optional[int] = None
) -> int:
    """
    Manually add a term to the glossary with full metadata.

    Args:
        niche_id: ID of the niche
        term: The canonical term (e.g., "Gandalf")
        term_type: Type ("character", "location", "item", "concept", "brand")
        phonetic_hints: Comma-separated phonetic variations
                       (e.g., "gan-dalf,gan-dolf")
        aliases: JSON string of aliases
                (e.g., '["Mithrandir", "The Grey Wizard"]')
        description: Description of the term
        source_id: ID of canon source (optional)

    Returns:
        ID of the created glossary entry

    Example:
        >>> entry_id = add_manual_term(
        ...     niche_id=1,
        ...     term="Gandalf",
        ...     term_type="character",
        ...     phonetic_hints="gan-dalf,gan-dolf,gahn-dalf",
        ...     aliases='["Mithrandir", "The Grey Wizard", "The White Rider"]',
        ...     description="Istari wizard, member of the Fellowship"
        ... )
    """
    return create_glossary_entry(
        niche_id=niche_id,
        term=term,
        term_type=term_type,
        phonetic_hints=phonetic_hints,
        aliases=aliases,
        description=description,
        source_id=source_id
    )


def generate_phonetic_hints(term: str) -> str:
    """
    Generate basic phonetic variations for a term.

    This is a simple helper. Manual refinement recommended.

    Args:
        term: The term to generate hints for

    Returns:
        Comma-separated phonetic variations

    Example:
        >>> generate_phonetic_hints("Gandalf")
        'gan-dalf,gahn-dalf,gan-dolf'
    """
    # Very basic phonetic variations
    # This is a placeholder - real implementation would need phonetic library

    variations = [term.lower()]

    # Add hyphenated version
    if ' ' not in term and len(term) > 4:
        mid = len(term) // 2
        variations.append(f"{term[:mid]}-{term[mid:]}".lower())

    # Add some common substitutions
    term_lower = term.lower()

    # a -> ah
    if 'a' in term_lower:
        variations.append(term_lower.replace('a', 'ah'))

    # f -> ph
    if 'f' in term_lower:
        variations.append(term_lower.replace('f', 'ph'))

    return ','.join(set(variations))


def get_glossary_stats(niche_id: int) -> Dict[str, int]:
    """
    Get statistics about glossary for a niche.

    Args:
        niche_id: ID of the niche

    Returns:
        Dictionary with counts by term_type and total
    """
    from src.database.glossary import get_glossary_by_niche

    all_terms = get_glossary_by_niche(niche_id)

    stats = {
        "total": len(all_terms),
        "character": 0,
        "location": 0,
        "item": 0,
        "concept": 0,
        "unknown": 0
    }

    for term in all_terms:
        term_type = term.get('term_type', 'unknown')
        if term_type in stats:
            stats[term_type] += 1
        else:
            stats['unknown'] += 1

    return stats
