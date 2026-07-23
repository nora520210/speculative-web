from __future__ import annotations

"""Registry for backend-owned, versioned interaction workflows.

Workflows sequence existing graph, Scope, ConversationSession, and Operation contracts.
They never create a second canvas or contain model prompts, tool theory, or UI-only state.
"""

from copy import deepcopy
import json
from pathlib import Path

from server.config import ROOT, WORKFLOW_DEFINITION_DIR


STAGE_KINDS = {"input", "derived", "operation", "selection", "conversation", "optional"}


def _manifest_paths() -> list[Path]:
    if not WORKFLOW_DEFINITION_DIR.exists():
        return []
    return sorted(WORKFLOW_DEFINITION_DIR.glob("*/manifest.json"))


def normalize_workflow_definition(value: dict) -> dict:
    if not isinstance(value, dict) or not value.get("id") or not value.get("label"):
        raise ValueError("Workflow definitions need an id and label.")

    stages = []
    seen_stage_ids = set()
    for stage in value.get("stages", []):
        if not isinstance(stage, dict) or not stage.get("id"):
            continue
        stage_id = str(stage["id"])
        if stage_id in seen_stage_ids:
            raise ValueError("Workflow stage ids must be unique.")
        seen_stage_ids.add(stage_id)
        stages.append(
            {
                "id": stage_id,
                "label": str(stage.get("label") or stage_id),
                "kind": stage.get("kind") if stage.get("kind") in STAGE_KINDS else "input",
                "required": bool(stage.get("required", True)),
                "operation_definition_id": str(stage.get("operation_definition_id") or ""),
                "description": str(stage.get("description") or ""),
            }
        )
    if not stages:
        raise ValueError("Workflow definitions need at least one stage.")

    start_input = value.get("start_input") if isinstance(value.get("start_input"), dict) else {}
    return {
        "id": str(value["id"]),
        "version": str(value.get("version") or "0.1.0"),
        "label": str(value["label"]),
        "description": str(value.get("description") or ""),
        "start_input": {
            "required": [str(item) for item in start_input.get("required", []) if str(item)],
            "optional": [str(item) for item in start_input.get("optional", []) if str(item)],
        },
        "stages": stages,
        "ui": deepcopy(value.get("ui") if isinstance(value.get("ui"), dict) else {}),
        "package_path": str(value.get("package_path") or ""),
    }


def list_workflow_definitions() -> list[dict]:
    definitions = []
    for manifest_path in _manifest_paths():
        try:
            raw = json.loads(manifest_path.read_text(encoding="utf-8"))
            definition = normalize_workflow_definition(raw)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        definition["package_path"] = str(manifest_path.parent.relative_to(ROOT))
        definitions.append(definition)
    return definitions


def get_workflow_definition(definition_id: str | None) -> dict | None:
    return next((item for item in list_workflow_definitions() if item["id"] == definition_id), None)


def default_workflow_definition() -> dict:
    definitions = list_workflow_definitions()
    if not definitions:
        raise ValueError("No workflow definitions are installed.")
    preferred = next((item for item in definitions if item["id"] == "workflow.four-futures-foundation"), None)
    return deepcopy(preferred or definitions[0])
