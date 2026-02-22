"""
Tests for production context export formatting.
"""

from src.ui.pages.production import format_export


def _make_ctx(
    topic="Test Topic",
    angle="Test Angle",
    canon_passages=None,
    transcript_chunks=None,
):
    return {
        "id": 1,
        "topic": topic,
        "angle": angle,
        "canon_passages": canon_passages or [],
        "transcript_chunks": transcript_chunks or [],
    }


class TestFormatExportHeader:
    def test_topic_and_angle(self):
        result = format_export(_make_ctx(topic="My Video", angle="Hot take"))
        assert result.startswith("# My Video\nAngle: Hot take\n")

    def test_no_angle(self):
        result = format_export(_make_ctx(angle=""))
        assert "Angle:" not in result

    def test_no_topic_shows_untitled(self):
        result = format_export(_make_ctx(topic=None))
        assert result.startswith("# Untitled\n")


class TestFormatExportCanonPassages:
    def test_grouped_by_source_title(self):
        passages = [
            {"id": 1, "source_title": "Book B", "chapter": "Ch1", "page": 10,
             "authority_score": 90, "text": "Text from B"},
            {"id": 2, "source_title": "Book A", "chapter": "Ch1", "page": 5,
             "authority_score": 80, "text": "Text from A"},
        ]
        result = format_export(_make_ctx(canon_passages=passages))
        # Book A should come before Book B (sorted)
        assert result.index("### Book A") < result.index("### Book B")

    def test_sorted_by_chapter_then_page_within_source(self):
        passages = [
            {"id": 1, "source_title": "Book", "chapter": "Ch2", "page": 1,
             "authority_score": None, "text": "Second chapter"},
            {"id": 2, "source_title": "Book", "chapter": "Ch1", "page": 20,
             "authority_score": None, "text": "First chapter p20"},
            {"id": 3, "source_title": "Book", "chapter": "Ch1", "page": 5,
             "authority_score": None, "text": "First chapter p5"},
        ]
        result = format_export(_make_ctx(canon_passages=passages))
        # Within "Book": Ch1 p5, Ch1 p20, Ch2 p1
        assert result.index("First chapter p5") < result.index("First chapter p20")
        assert result.index("First chapter p20") < result.index("Second chapter")

    def test_location_line_formatting(self):
        passages = [
            {"id": 1, "source_title": "Src", "chapter": "Chapter 3", "page": 42,
             "authority_score": 95, "text": "Passage text"},
        ]
        result = format_export(_make_ctx(canon_passages=passages))
        assert "[Chapter 3 | p.42 | authority 95]" in result

    def test_missing_metadata_omitted(self):
        passages = [
            {"id": 1, "source_title": "Src", "chapter": None, "page": None,
             "authority_score": None, "text": "Just text"},
        ]
        result = format_export(_make_ctx(canon_passages=passages))
        # No location line should appear
        assert "[" not in result or "### Src" in result

    def test_unknown_source_fallback(self):
        passages = [
            {"id": 1, "source_title": None, "chapter": None, "page": None,
             "authority_score": None, "text": "Orphan text"},
        ]
        result = format_export(_make_ctx(canon_passages=passages))
        assert "### Unknown Source" in result

    def test_empty_passages_no_section(self):
        result = format_export(_make_ctx(canon_passages=[]))
        assert "## Canon Sources" not in result


class TestFormatExportTranscriptChunks:
    def test_grouped_by_video_id(self):
        chunks = [
            {"id": 1, "video_id": 2, "video_title": "Video Two", "channel_name": "Ch",
             "view_count": 100, "chunk_index": 0, "text": "V2 chunk"},
            {"id": 2, "video_id": 1, "video_title": "Video One", "channel_name": "Ch",
             "view_count": 200, "chunk_index": 0, "text": "V1 chunk"},
        ]
        result = format_export(_make_ctx(transcript_chunks=chunks))
        # video_id 1 sorts before video_id 2
        assert result.index("### Video One") < result.index("### Video Two")

    def test_sorted_by_chunk_index_within_video(self):
        chunks = [
            {"id": 1, "video_id": 1, "video_title": "V", "channel_name": "",
             "view_count": None, "chunk_index": 2, "text": "Chunk two"},
            {"id": 2, "video_id": 1, "video_title": "V", "channel_name": "",
             "view_count": None, "chunk_index": 0, "text": "Chunk zero"},
            {"id": 3, "video_id": 1, "video_title": "V", "channel_name": "",
             "view_count": None, "chunk_index": 1, "text": "Chunk one"},
        ]
        result = format_export(_make_ctx(transcript_chunks=chunks))
        assert result.index("Chunk zero") < result.index("Chunk one")
        assert result.index("Chunk one") < result.index("Chunk two")

    def test_attribution_in_header(self):
        chunks = [
            {"id": 1, "video_id": 1, "video_title": "Cool Video",
             "channel_name": "Creator", "view_count": 50000,
             "chunk_index": 0, "text": "Some text"},
        ]
        result = format_export(_make_ctx(transcript_chunks=chunks))
        assert "### Cool Video (Creator | 50,000 views)" in result

    def test_reference_warning(self):
        chunks = [
            {"id": 1, "video_id": 1, "video_title": "V", "channel_name": "",
             "view_count": None, "chunk_index": 0, "text": "T"},
        ]
        result = format_export(_make_ctx(transcript_chunks=chunks))
        assert "do not copy directly" in result.lower()

    def test_empty_chunks_no_section(self):
        result = format_export(_make_ctx(transcript_chunks=[]))
        assert "## Competitor Transcripts" not in result


class TestFormatExportCombined:
    def test_full_context_has_both_sections(self):
        ctx = _make_ctx(
            canon_passages=[
                {"id": 1, "source_title": "Book", "chapter": "Ch1", "page": 1,
                 "authority_score": 80, "text": "Canon text"},
            ],
            transcript_chunks=[
                {"id": 1, "video_id": 1, "video_title": "Vid", "channel_name": "C",
                 "view_count": 1000, "chunk_index": 0, "text": "Transcript text"},
            ],
        )
        result = format_export(ctx)
        assert "## Canon Sources" in result
        assert "## Competitor Transcripts" in result
        # Canon before transcripts
        assert result.index("## Canon Sources") < result.index("## Competitor Transcripts")

    def test_ends_with_newline(self):
        result = format_export(_make_ctx())
        assert result.endswith("\n")
