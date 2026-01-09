"""
Canon source ingestion module.

Handles extraction of text from various file formats and storage
in the database.
"""

from pathlib import Path
from typing import Optional
import fitz  # PyMuPDF

from src.database.canon_sources import create_canon_source


def extract_pdf(file_path: str) -> tuple[str, dict]:
    """
    Extract text from PDF with metadata.

    Args:
        file_path: Path to the PDF file

    Returns:
        Tuple of (full_text, metadata) where:
        - full_text: All text from PDF concatenated
        - metadata: Dict with page_count, pages (list of page texts)

    Raises:
        FileNotFoundError: If PDF file doesn't exist
        Exception: If PDF extraction fails
    """
    pdf_path = Path(file_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    try:
        doc = fitz.open(str(pdf_path))
        pages = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            pages.append({
                "page": page_num + 1,
                "text": text
            })

        doc.close()

        # Concatenate all text
        full_text = "\n\n".join([p["text"] for p in pages])

        metadata = {
            "page_count": len(pages),
            "pages": pages
        }

        return full_text, metadata

    except Exception as e:
        raise Exception(f"Failed to extract PDF: {e}") from e


def ingest_pdf(
    file_path: str,
    niche_id: int,
    title: str,
    author: Optional[str] = None,
    priority: int = 1
) -> int:
    """
    Ingest a PDF file into the system.

    This function:
    1. Extracts text from the PDF
    2. Stores the source in canon_sources table
    3. Returns the source_id for further processing

    Args:
        file_path: Path to the PDF file
        niche_id: ID of the niche this source belongs to
        title: Title of the source (e.g., "The Hobbit")
        author: Author name (e.g., "J.R.R. Tolkien")
        priority: Priority level (higher = more authoritative), default 1

    Returns:
        The ID of the newly created canon source

    Raises:
        FileNotFoundError: If PDF file doesn't exist
        Exception: If extraction or database insertion fails

    Example:
        >>> source_id = ingest_pdf(
        ...     "/path/to/hobbit.pdf",
        ...     niche_id=1,
        ...     title="The Hobbit",
        ...     author="J.R.R. Tolkien",
        ...     priority=5
        ... )
        >>> print(f"Ingested source ID: {source_id}")
    """
    # Validate file exists
    pdf_path = Path(file_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    # Extract text to validate PDF is readable
    try:
        full_text, metadata = extract_pdf(file_path)
        page_count = metadata["page_count"]

        print(f"Extracted {page_count} pages from PDF")
        print(f"Total characters: {len(full_text):,}")

    except Exception as e:
        raise Exception(f"Failed to extract PDF: {e}") from e

    # Store in database
    try:
        source_id = create_canon_source(
            niche_id=niche_id,
            title=title,
            author=author,
            source_type="book",
            file_path=str(pdf_path.absolute()),
            priority=priority
        )

        print(f"Created canon source with ID: {source_id}")
        return source_id

    except Exception as e:
        raise Exception(f"Failed to store source in database: {e}") from e


def ingest_text_file(
    file_path: str,
    niche_id: int,
    title: str,
    author: Optional[str] = None,
    priority: int = 1
) -> int:
    """
    Ingest a plain text file into the system.

    Args:
        file_path: Path to the text file
        niche_id: ID of the niche this source belongs to
        title: Title of the source
        author: Author name
        priority: Priority level (higher = more authoritative), default 1

    Returns:
        The ID of the newly created canon source

    Raises:
        FileNotFoundError: If text file doesn't exist
        Exception: If database insertion fails
    """
    text_path = Path(file_path)

    if not text_path.exists():
        raise FileNotFoundError(f"Text file not found: {file_path}")

    # Read text file
    try:
        with open(text_path, 'r', encoding='utf-8') as f:
            content = f.read()

        print(f"Read text file: {len(content):,} characters")

    except Exception as e:
        raise Exception(f"Failed to read text file: {e}") from e

    # Store in database
    try:
        source_id = create_canon_source(
            niche_id=niche_id,
            title=title,
            author=author,
            source_type="text",
            file_path=str(text_path.absolute()),
            priority=priority
        )

        print(f"Created canon source with ID: {source_id}")
        return source_id

    except Exception as e:
        raise Exception(f"Failed to store source in database: {e}") from e
