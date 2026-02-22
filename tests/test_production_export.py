"""
Tests for production context export formatting.
"""

from src.ui.pages.production import format_export, _find_boundary_overlap, _merge_adjacent_texts


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


class TestFindBoundaryOverlap:
    def test_exact_overlap(self):
        a = "the bridge. He lifted his staff."
        b = "He lifted his staff. A blinding light"
        overlap = _find_boundary_overlap(a, b)
        assert overlap == len("He lifted his staff.")

    def test_no_overlap(self):
        assert _find_boundary_overlap("completely different", "text here") == 0

    def test_overlap_below_minimum(self):
        # "staff." is only 6 chars, below default min_overlap=20
        assert _find_boundary_overlap("his staff.", "staff. A light") == 0

    def test_custom_min_overlap(self):
        assert _find_boundary_overlap("his staff.", "staff. A light", min_overlap=6) == 6

    def test_full_overlap(self):
        # b is entirely contained as suffix of a
        assert _find_boundary_overlap("AAABBB", "BBB", min_overlap=3) == 3

    def test_empty_strings(self):
        assert _find_boundary_overlap("", "text") == 0
        assert _find_boundary_overlap("text", "") == 0


class TestMergeAdjacentTexts:
    def test_overlapping_pair_merged(self):
        a = "the bridge. He lifted his staff."
        b = "He lifted his staff. A blinding light shone forth."
        result = _merge_adjacent_texts([a, b])
        assert len(result) == 1
        assert result[0] == "the bridge. He lifted his staff. A blinding light shone forth."

    def test_non_overlapping_stay_separate(self):
        a = "First passage about hobbits."
        b = "Second passage about elves."
        result = _merge_adjacent_texts([a, b])
        assert len(result) == 2
        assert result[0] == a
        assert result[1] == b

    def test_three_way_chain_merge(self):
        a = "Start of the text. Middle section begins."
        b = "Middle section begins. The story continues onward."
        c = "The story continues onward. End of text."
        result = _merge_adjacent_texts([a, b, c])
        assert len(result) == 1
        assert result[0] == "Start of the text. Middle section begins. The story continues onward. End of text."

    def test_mixed_overlap_and_gap(self):
        a = "First chunk. Overlap sentence here."
        b = "Overlap sentence here. Second chunk."
        c = "Totally different third chunk."
        result = _merge_adjacent_texts([a, b, c])
        assert len(result) == 2
        assert result[0] == "First chunk. Overlap sentence here. Second chunk."
        assert result[1] == c

    def test_empty_list(self):
        assert _merge_adjacent_texts([]) == []

    def test_single_item(self):
        assert _merge_adjacent_texts(["only one"]) == ["only one"]


class TestFormatExportMerging:
    def test_adjacent_canon_passages_merged(self):
        """The spec scenario: two adjacent chunks with overlapping boundary text."""
        passages = [
            {"id": 1, "source_title": "Tolkien", "chapter": "Ch5", "page": 100,
             "authority_score": 90,
             "text": "Gandalf stood upon the bridge. He lifted his staff."},
            {"id": 2, "source_title": "Tolkien", "chapter": "Ch5", "page": 101,
             "authority_score": 85,
             "text": "He lifted his staff. A blinding light shone forth."},
        ]
        result = format_export(_make_ctx(canon_passages=passages))
        # Should be merged: no duplicate "He lifted his staff."
        assert "He lifted his staff." in result
        assert result.count("He lifted his staff.") == 1
        assert "Gandalf stood upon the bridge." in result
        assert "A blinding light shone forth." in result

    def test_non_adjacent_canon_passages_stay_separate(self):
        passages = [
            {"id": 1, "source_title": "Tolkien", "chapter": "Ch1", "page": 10,
             "authority_score": None,
             "text": "In a hole in the ground there lived a hobbit."},
            {"id": 2, "source_title": "Tolkien", "chapter": "Ch8", "page": 150,
             "authority_score": None,
             "text": "The dragon lay upon his hoard of gold."},
        ]
        result = format_export(_make_ctx(canon_passages=passages))
        # Both texts should appear fully, no merging
        assert "In a hole in the ground" in result
        assert "The dragon lay upon" in result
        # No merge note
        assert "auto-merged" not in result

    def test_adjacent_transcript_chunks_merged(self):
        chunks = [
            {"id": 1, "video_id": 1, "video_title": "V", "channel_name": "C",
             "view_count": 1000, "chunk_index": 0,
             "text": "Welcome to the video. Today we discuss the topic at hand."},
            {"id": 2, "video_id": 1, "video_title": "V", "channel_name": "C",
             "view_count": 1000, "chunk_index": 1,
             "text": "Today we discuss the topic at hand. Let's get started."},
        ]
        result = format_export(_make_ctx(transcript_chunks=chunks))
        assert result.count("Today we discuss the topic at hand.") == 1
        assert "Welcome to the video." in result
        assert "Let's get started." in result

    def test_merge_note_appears_when_merged(self):
        passages = [
            {"id": 1, "source_title": "Book", "chapter": "Ch1", "page": 1,
             "authority_score": None,
             "text": "the bridge. He lifted his staff."},
            {"id": 2, "source_title": "Book", "chapter": "Ch1", "page": 1,
             "authority_score": None,
             "text": "He lifted his staff. A blinding light."},
        ]
        result = format_export(_make_ctx(canon_passages=passages))
        assert "Adjacent passages auto-merged" in result

    def test_merge_note_absent_when_no_merges(self):
        passages = [
            {"id": 1, "source_title": "Book", "chapter": "Ch1", "page": 1,
             "authority_score": None, "text": "Standalone passage."},
        ]
        result = format_export(_make_ctx(canon_passages=passages))
        assert "auto-merged" not in result

    def test_page_range_in_location_after_merge(self):
        passages = [
            {"id": 1, "source_title": "Book", "chapter": "Ch1", "page": 50,
             "authority_score": None,
             "text": "the bridge. He lifted his staff."},
            {"id": 2, "source_title": "Book", "chapter": "Ch1", "page": 51,
             "authority_score": None,
             "text": "He lifted his staff. A blinding light."},
        ]
        result = format_export(_make_ctx(canon_passages=passages))
        assert "p.50" in result
        assert "to p.51" in result

    def test_different_sources_not_merged(self):
        """Passages from different sources should never merge even if text overlaps."""
        passages = [
            {"id": 1, "source_title": "Book A", "chapter": "Ch1", "page": 1,
             "authority_score": None,
             "text": "the bridge. He lifted his staff."},
            {"id": 2, "source_title": "Book B", "chapter": "Ch1", "page": 1,
             "authority_score": None,
             "text": "He lifted his staff. A blinding light."},
        ]
        result = format_export(_make_ctx(canon_passages=passages))
        # Should appear twice — once under each source
        assert result.count("He lifted his staff.") == 2
