from server.documents import compact_preview, extract_keywords, extract_named_section, infer_paper_title


def test_compact_preview_truncates():
    preview = compact_preview("alpha " * 100, limit=24)
    assert preview.endswith("…")
    assert len(preview) <= 24


def test_compact_preview_preserves_short_text():
    assert compact_preview("one two", limit=20) == "one two"


def test_paper_section_extractors_find_abstract_and_keywords():
    text = """
    Adaptive AI Triage in Public Clinics
    Abstract This study examines how nurses, patients, and doctors negotiate uncertain AI summaries in crowded clinics.
    Keywords: AI triage; clinical safety; patient trust
    Introduction The remainder of the paper starts here.
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    assert infer_paper_title(lines, "fallback") == "Adaptive AI Triage in Public Clinics"
    abstract = extract_named_section(text, ("abstract", "摘要"), ("keywords", "introduction"))
    assert "uncertain AI summaries" in abstract
    assert extract_keywords(text)[:2] == ["AI triage", "clinical safety"]
