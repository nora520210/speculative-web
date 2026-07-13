from __future__ import annotations

from pathlib import Path


def inspect_document(path: Path) -> dict:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return inspect_pdf(path)
    if suffix == ".docx":
        return inspect_docx(path)
    if suffix in {".txt", ".md"}:
        text = path.read_text(encoding="utf-8", errors="replace")
        return summarize_text(path, text, kind=suffix.lstrip("."))
    raise ValueError(f"Unsupported document type: {suffix or 'unknown'}")


def inspect_pdf(path: Path) -> dict:
    import pdfplumber

    pages = []
    full_text = []
    with pdfplumber.open(path) as pdf:
        for index, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            full_text.append(text)
            pages.append(
                {
                    "page": index,
                    "characters": len(text),
                    "preview": compact_preview(text),
                }
            )

    return {
        "filename": path.name,
        "kind": "pdf",
        "page_count": len(pages),
        "characters": sum(page["characters"] for page in pages),
        "preview": compact_preview("\n".join(full_text), limit=900),
        "pages": pages[:12],
    }


def inspect_docx(path: Path) -> dict:
    from docx import Document

    document = Document(path)
    paragraphs = [p.text.strip() for p in document.paragraphs if p.text.strip()]
    tables = []
    for table_index, table in enumerate(document.tables, start=1):
        tables.append(
            {
                "table": table_index,
                "rows": len(table.rows),
                "columns": len(table.columns),
            }
        )

    text = "\n".join(paragraphs)
    return {
        "filename": path.name,
        "kind": "docx",
        "paragraph_count": len(paragraphs),
        "table_count": len(tables),
        "characters": len(text),
        "preview": compact_preview(text, limit=900),
        "tables": tables[:12],
    }


def summarize_text(path: Path, text: str, kind: str) -> dict:
    return {
        "filename": path.name,
        "kind": kind,
        "line_count": len(text.splitlines()),
        "characters": len(text),
        "preview": compact_preview(text, limit=900),
    }


def compact_preview(text: str, limit: int = 220) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"
