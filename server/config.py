from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / ".env"
DATA_DIR = Path(
    os.environ.get(
        "SPEC_WEB_DATA_DIR",
        "/tmp/speculative-web" if os.environ.get("VERCEL") else str(ROOT / "data"),
    )
)
UPLOAD_DIR = DATA_DIR / "uploads"
RENDER_DIR = DATA_DIR / "renders"
GENERATED_IMAGE_DIR = DATA_DIR / "generated"
TOOL_REGISTRY_FILE = DATA_DIR / "tool_registry.json"
TOOL_PACKAGE_DIR = ROOT / "tool_packages"
MAX_JSON_BODY_BYTES = int(os.environ.get("SPEC_WEB_MAX_JSON_BODY_BYTES", str(1_000_000)))
MAX_UPLOAD_BYTES = int(os.environ.get("SPEC_WEB_MAX_UPLOAD_BYTES", str(25_000_000)))


def storage_mode() -> str:
    if os.environ.get("SPEC_WEB_DATA_DIR"):
        return "configured"
    if os.environ.get("VERCEL"):
        return "ephemeral"
    return "local"

RUNTIME_ROOT = Path(
    os.environ.get(
        "CODEX_RUNTIME_ROOT",
        "/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies",
    )
)

BUNDLED_PYTHON = RUNTIME_ROOT / "python" / "bin" / "python3"
BUNDLED_NODE = RUNTIME_ROOT / "node" / "bin" / "node"
POPPLER_BIN = RUNTIME_ROOT / "bin"
PDFTOPPM = POPPLER_BIN / "pdftoppm"
PDFINFO = POPPLER_BIN / "pdfinfo"
SOFFICE = RUNTIME_ROOT / "bin" / "soffice"


def load_env_file(path: Path = ENV_FILE) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def ensure_dirs() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    UPLOAD_DIR.mkdir(exist_ok=True)
    RENDER_DIR.mkdir(exist_ok=True)
    GENERATED_IMAGE_DIR.mkdir(exist_ok=True)
