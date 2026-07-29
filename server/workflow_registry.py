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

DEFAULT_RUNTIME = {
    "input_stage_id": "input",
    "future_stage_id": "four_futures",
    "tools_stage_id": "tools",
    "scenario_stage_id": "scenario",
    "branch_count": 4,
    "branch_selection_mode": "exactly_one",
    "rerun_policy": "supersede_previous_active_line",
}


def _manifest_paths() -> list[Path]:
    if not WORKFLOW_DEFINITION_DIR.exists():
        return []
    return sorted(WORKFLOW_DEFINITION_DIR.glob("*/manifest.json"))


def normalize_workflow_locales(value: object) -> dict:
    """Keep display copy package-owned without making it workflow logic."""

    if not isinstance(value, dict):
        return {}
    locales: dict[str, dict] = {}
    for language, copy in value.items():
        if not isinstance(language, str) or not isinstance(copy, dict):
            continue
        normalized = {
            key: str(copy[key])
            for key in ("label", "description")
            if copy.get(key)
        }
        stages = copy.get("stages") if isinstance(copy.get("stages"), dict) else {}
        stage_copy = {}
        for stage_id, stage in stages.items():
            if isinstance(stage_id, str) and isinstance(stage, dict) and stage.get("label"):
                stage_copy[stage_id] = {"label": str(stage["label"])}
        if stage_copy:
            normalized["stages"] = stage_copy
        ui = copy.get("ui") if isinstance(copy.get("ui"), dict) else {}
        if ui:
            normalized["ui"] = {key: str(item) for key, item in ui.items() if item}
        if normalized:
            locales[language] = normalized
    return locales


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
    raw_runtime = value.get("runtime") if isinstance(value.get("runtime"), dict) else {}
    stage_ids = {stage["id"] for stage in stages}
    runtime = dict(DEFAULT_RUNTIME)
    for key in ("input_stage_id", "future_stage_id", "tools_stage_id", "scenario_stage_id"):
        candidate = str(raw_runtime.get(key) or runtime[key])
        runtime[key] = candidate if candidate in stage_ids else runtime[key]
    try:
        runtime["branch_count"] = max(1, min(12, int(raw_runtime.get("branch_count") or runtime["branch_count"])))
    except (TypeError, ValueError):
        pass
    if raw_runtime.get("branch_selection_mode") in {"exactly_one"}:
        runtime["branch_selection_mode"] = raw_runtime["branch_selection_mode"]
    if raw_runtime.get("rerun_policy") in {"supersede_previous_active_line"}:
        runtime["rerun_policy"] = raw_runtime["rerun_policy"]
    raw_discussion_policy = value.get("discussion_tool_policy") if isinstance(value.get("discussion_tool_policy"), dict) else {}
    try:
        configured_minimum = int(raw_discussion_policy.get("minimum_selected") or 0)
    except (TypeError, ValueError):
        configured_minimum = 0
    recommended_by_branch = {}
    for branch_id, tool_ids in (raw_discussion_policy.get("recommended_by_branch") or {}).items():
        key = str(branch_id or "").strip()
        if not key or not isinstance(tool_ids, list):
            continue
        unique_ids = []
        for tool_id in tool_ids:
            value_id = str(tool_id or "").strip()
            if value_id and value_id not in unique_ids:
                unique_ids.append(value_id)
        if unique_ids:
            recommended_by_branch[key] = unique_ids
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
        "runtime": runtime,
        "discussion_tool_policy": {
            "minimum_selected": min(24, max(0, configured_minimum)),
            "recommended_by_branch": recommended_by_branch,
        },
        "ui": deepcopy(value.get("ui") if isinstance(value.get("ui"), dict) else {}),
        "locales": normalize_workflow_locales(value.get("locales")),
        "package_path": str(value.get("package_path") or ""),
    }


def workflow_runtime_contract(value: dict | None) -> dict:
    """Read a small runtime contract from a frozen workflow snapshot.

    Workflow packages own stage names and branch semantics. Runtime functions use
    this normalised mapping rather than duplicating a presentational stage order.
    Older snapshots receive their historical defaults during migration.
    """

    raw = value.get("runtime") if isinstance(value, dict) and isinstance(value.get("runtime"), dict) else {}
    runtime = dict(DEFAULT_RUNTIME)
    for key in ("input_stage_id", "future_stage_id", "tools_stage_id", "scenario_stage_id"):
        if raw.get(key):
            runtime[key] = str(raw[key])
    try:
        runtime["branch_count"] = max(1, min(12, int(raw.get("branch_count") or runtime["branch_count"])))
    except (TypeError, ValueError):
        pass
    if raw.get("branch_selection_mode") in {"exactly_one"}:
        runtime["branch_selection_mode"] = raw["branch_selection_mode"]
    if raw.get("rerun_policy") in {"supersede_previous_active_line"}:
        runtime["rerun_policy"] = raw["rerun_policy"]
    return runtime


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
