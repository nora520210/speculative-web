from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STYLE_FILES = [ROOT / "static" / "styles.css"]
FORBIDDEN = [
    (re.compile(r"#(?:4f46e5|6366f1|7c3aed|8b5cf6|9333ea|3b82f6)", re.I), "blue/purple token"),
    (re.compile(r"radial-gradient", re.I), "decorative gradient"),
    (re.compile(r"box-shadow\\s*:", re.I), "box shadow"),
    (re.compile(r"letter-spacing\\s*:\\s*-", re.I), "negative letter spacing"),
]


def main() -> int:
    failures = []
    for path in STYLE_FILES:
        text = path.read_text(encoding="utf-8")
        for pattern, label in FORBIDDEN:
            if pattern.search(text):
                failures.append(f"{path}: forbidden {label}")
    if failures:
        print("visual token check failed")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("visual tokens ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
