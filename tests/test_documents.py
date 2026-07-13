from server.documents import compact_preview


def test_compact_preview_truncates():
    preview = compact_preview("alpha " * 100, limit=24)
    assert preview.endswith("…")
    assert len(preview) <= 24


def test_compact_preview_preserves_short_text():
    assert compact_preview("one two", limit=20) == "one two"
