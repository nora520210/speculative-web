from __future__ import annotations

import base64
import mimetypes
from pathlib import Path

from server.config import GENERATED_IMAGE_DIR, MAX_VISION_IMAGE_BYTES, MAX_VISION_IMAGES, UPLOAD_DIR


IMAGE_MIME_TYPES = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp", ".gif": "image/gif"}


def visual_context_for_nodes(canvas: dict, node_ids: list[str]) -> dict:
    by_id = {node["id"]: node for node in canvas.get("nodes", [])}
    references = []
    inputs = []
    for node_id in node_ids:
        node = by_id.get(node_id)
        if not node or node.get("type") not in {"image", "multimodal"}:
            continue
        payload = node.get("payload", {})
        reference = {
            "node_id": node_id,
            "title": node.get("title", "Image input"),
            "image_url": payload.get("image_url", ""),
            "image_file": payload.get("image_file", ""),
            "mime_type": payload.get("mime_type", ""),
            "semantic_summary": payload.get("semantic_summary", ""),
        }
        image_input = image_input_for_reference(reference)
        if image_input and len(inputs) < MAX_VISION_IMAGES:
            references.append(reference)
            inputs.append(image_input)
    return {"references": references, "inputs": inputs}


def image_input_for_reference(reference: dict) -> dict | None:
    path = local_image_path(reference)
    if not path or not path.exists() or not path.is_file():
        return None
    if path.stat().st_size > MAX_VISION_IMAGE_BYTES:
        return None
    mime_type = reference.get("mime_type") or IMAGE_MIME_TYPES.get(path.suffix.lower()) or mimetypes.guess_type(path.name)[0]
    if mime_type not in IMAGE_MIME_TYPES.values():
        return None
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return {
        "node_id": reference.get("node_id", ""),
        "title": reference.get("title", "Image input"),
        "data_url": f"data:{mime_type};base64,{encoded}",
        "detail": "high",
    }


def local_image_path(reference: dict) -> Path | None:
    image_file = str(reference.get("image_file") or "").replace("\\", "/").lstrip("/")
    if image_file.startswith("uploads/"):
        return safe_child(UPLOAD_DIR, image_file.removeprefix("uploads/"))
    if image_file.startswith("generated/"):
        return safe_child(GENERATED_IMAGE_DIR, image_file.removeprefix("generated/"))
    image_url = str(reference.get("image_url") or "")
    if image_url.startswith("/uploads/"):
        return safe_child(UPLOAD_DIR, image_url.removeprefix("/uploads/"))
    if image_url.startswith("/generated/"):
        return safe_child(GENERATED_IMAGE_DIR, image_url.removeprefix("/generated/"))
    return None


def safe_child(root: Path, name: str) -> Path | None:
    candidate = (root / name).resolve()
    resolved_root = root.resolve()
    return candidate if candidate != resolved_root and resolved_root in candidate.parents else None
