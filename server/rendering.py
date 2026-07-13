from __future__ import annotations

import shutil
import subprocess
import uuid
from pathlib import Path

from server.config import PDFTOPPM, RENDER_DIR, SOFFICE, ensure_dirs


def render_document(path: Path) -> dict:
    ensure_dirs()
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return render_pdf(path)
    if suffix == ".docx":
        return render_docx(path)
    raise ValueError(f"Rendering is supported for PDF and DOCX, not {suffix or 'unknown'}")


def render_pdf(path: Path) -> dict:
    if not PDFTOPPM.exists():
        raise RuntimeError(f"pdftoppm not found at {PDFTOPPM}")
    output_dir = RENDER_DIR / f"{path.stem}-{uuid.uuid4().hex[:8]}"
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = output_dir / "page"
    subprocess.run(
        [str(PDFTOPPM), "-png", "-r", "120", str(path), str(prefix)],
        check=True,
        capture_output=True,
        text=True,
    )
    pages = sorted(output_dir.glob("page-*.png"))
    return {
        "filename": path.name,
        "kind": "pdf",
        "output_dir": str(output_dir),
        "page_count": len(pages),
        "pages": [str(page) for page in pages[:12]],
    }


def render_docx(path: Path) -> dict:
    if not SOFFICE.exists():
        raise RuntimeError(f"soffice not found at {SOFFICE}")
    output_dir = RENDER_DIR / f"{path.stem}-{uuid.uuid4().hex[:8]}"
    output_dir.mkdir(parents=True, exist_ok=True)
    profile = output_dir / "lo-profile"
    profile.mkdir(exist_ok=True)
    subprocess.run(
        [
            str(SOFFICE),
            "--headless",
            f"-env:UserInstallation=file://{profile}",
            "--convert-to",
            "pdf",
            "--outdir",
            str(output_dir),
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    pdf = output_dir / f"{path.stem}.pdf"
    if not pdf.exists():
        candidates = sorted(output_dir.glob("*.pdf"))
        if not candidates:
            raise RuntimeError("DOCX conversion finished without producing a PDF.")
        pdf = candidates[0]
    rendered = render_pdf(pdf)
    final_pages = output_dir / "pages"
    final_pages.mkdir(exist_ok=True)
    for page in Path(rendered["output_dir"]).glob("*.png"):
        shutil.copy2(page, final_pages / page.name)
    pages = sorted(final_pages.glob("page-*.png"))
    return {
        "filename": path.name,
        "kind": "docx",
        "output_dir": str(output_dir),
        "pdf": str(pdf),
        "page_count": len(pages),
        "pages": [str(page) for page in pages[:12]],
    }
