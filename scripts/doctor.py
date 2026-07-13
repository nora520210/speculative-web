from __future__ import annotations

import importlib.util
import os
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = Path(
    os.environ.get(
        "CODEX_RUNTIME_ROOT",
        "/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies",
    )
)
CHECKS = [
    ("pdfplumber", "PDF text extraction"),
    ("docx", "DOCX text extraction"),
    ("PIL", "image utilities"),
]


def main() -> int:
    print(f"Python: {sys.version.split()[0]}")
    print(f"Project: {ROOT}")
    failures = 0
    for module, label in CHECKS:
        ok = importlib.util.find_spec(module) is not None
        print(f"{'ok' if ok else 'missing'}  {module:<12} {label}")
        failures += 0 if ok else 1

    binaries = {
        "python3": [shutil.which("python3"), str(RUNTIME_ROOT / "python" / "bin" / "python3")],
        "node": [shutil.which("node"), str(RUNTIME_ROOT / "node" / "bin" / "node")],
        "pdftoppm": [shutil.which("pdftoppm"), str(RUNTIME_ROOT / "bin" / "pdftoppm")],
        "soffice": [shutil.which("soffice"), str(RUNTIME_ROOT / "bin" / "soffice")],
    }
    for binary, candidates in binaries.items():
        found = next((candidate for candidate in candidates if candidate and Path(candidate).exists()), None)
        print(f"{'ok' if found else 'missing'}  {binary:<12} {found or ''}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
