from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from server.documents import inspect_document


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect PDF/DOCX/TXT/MD structure and text preview.")
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect_document(args.input), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
