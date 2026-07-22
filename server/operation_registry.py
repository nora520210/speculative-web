from __future__ import annotations

"""Registry for operation-node definitions.

Tool packages remain the source of speculative method logic.  Operation definitions
describe graph behavior and UI-independent contracts, so future nodes do not have to
be folded into a permanent Modify super-node.
"""

from copy import deepcopy
import json
from pathlib import Path

from server.config import ROOT


OPERATION_DEFINITION_DIR = ROOT / "operation_definitions"


def _manifest_paths() -> list[Path]:
    if not OPERATION_DEFINITION_DIR.exists():
        return []
    return sorted(OPERATION_DEFINITION_DIR.glob("*/manifest.json"))


def normalize_definition(value: dict) -> dict:
    if not isinstance(value, dict) or not value.get("id") or not value.get("label"):
        raise ValueError("Operation definitions need an id and label.")
    input_ports = []
    for port in value.get("input_ports", []):
        if not isinstance(port, dict) or not port.get("id"):
            continue
        input_ports.append(
            {
                "id": str(port["id"]),
                "label": str(port.get("label") or port["id"]),
                "accepted_modalities": [str(item) for item in port.get("accepted_modalities", ["text"])],
                "cardinality": port.get("cardinality") if port.get("cardinality") in {"one", "many"} else "many",
                "required": bool(port.get("required", False)),
            }
        )
    output_profiles = []
    for profile in value.get("output_profiles", []):
        if not isinstance(profile, dict) or not profile.get("id"):
            continue
        output_profiles.append(
            {
                "id": str(profile["id"]),
                "label": str(profile.get("label") or profile["id"]),
                "modalities": [str(item) for item in profile.get("modalities", ["text"])],
                "artifact_kind": str(profile.get("artifact_kind") or "artifact"),
            }
        )
    if not output_profiles:
        output_profiles = [{"id": "text", "label": "Text", "modalities": ["text"], "artifact_kind": "artifact"}]
    selector = value.get("tool_selector") if isinstance(value.get("tool_selector"), dict) else {}
    return {
        "id": str(value["id"]),
        "version": str(value.get("version") or "0.1.0"),
        "label": str(value["label"]),
        "description": str(value.get("description") or ""),
        "category_path": [str(item) for item in value.get("category_path", []) if str(item)],
        "input_ports": input_ports,
        "output_profiles": output_profiles,
        "tool_selector": {
            "selection_mode": selector.get("selection_mode") if selector.get("selection_mode") in {"none", "one", "many"} else "many",
            "accepted_layers": [str(item) for item in selector.get("accepted_layers", ["tool"])],
        },
        "execution": deepcopy(value.get("execution") if isinstance(value.get("execution"), dict) else {"kind": "model"}),
        "ui": deepcopy(value.get("ui") if isinstance(value.get("ui"), dict) else {}),
        "package_path": str(value.get("package_path") or ""),
    }


def list_operation_definitions() -> list[dict]:
    definitions = []
    for manifest_path in _manifest_paths():
        try:
            raw = json.loads(manifest_path.read_text(encoding="utf-8"))
            definition = normalize_definition(raw)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        definition["package_path"] = str(manifest_path.parent.relative_to(ROOT))
        definitions.append(definition)
    return definitions


def get_operation_definition(definition_id: str | None) -> dict | None:
    return next((item for item in list_operation_definitions() if item["id"] == definition_id), None)


def default_operation_definition() -> dict:
    definitions = list_operation_definitions()
    if not definitions:
        raise ValueError("No operation definitions are installed.")
    preferred = next((item for item in definitions if item["id"] == "operation.transform"), None)
    return deepcopy(preferred or definitions[0])


def normalize_operation_config(config: dict | None) -> dict:
    config = config if isinstance(config, dict) else {}
    ref = config.get("definition_ref") if isinstance(config.get("definition_ref"), dict) else {}
    definition = get_operation_definition(ref.get("id")) or default_operation_definition()
    profiles = {profile["id"] for profile in definition["output_profiles"]}
    output_profile = config.get("output_profile") if config.get("output_profile") in profiles else definition["output_profiles"][0]["id"]
    selections = []
    for item in config.get("tool_selections", []):
        if not isinstance(item, dict) or not item.get("tool_id"):
            continue
        selections.append(
            {
                "tool_id": str(item["tool_id"]),
                "version": str(item.get("version") or ""),
                "parameters": deepcopy(item.get("parameters") if isinstance(item.get("parameters"), dict) else {}),
            }
        )
    return {
        **config,
        "definition_ref": {"id": definition["id"], "version": definition["version"]},
        "definition": definition,
        "parameters": deepcopy(config.get("parameters") if isinstance(config.get("parameters"), dict) else {}),
        "tool_selections": selections,
        "output_profile": output_profile,
    }
