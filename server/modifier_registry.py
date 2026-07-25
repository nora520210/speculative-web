from __future__ import annotations

from copy import deepcopy
import json

from server.config import TOOL_PACKAGE_DIR, TOOL_REGISTRY_FILE


OUTPUT_TYPES = ["text", "image", "multimodal"]

DEFAULT_MODIFIER_TOOLS = [
    {
        "id": "what-if",
        "version": "0.1.0",
        "label": "What-if",
        "accepted_modalities": ["text", "image", "multimodal"],
        "supported_outputs": ["text", "image", "multimodal"],
        "input_contract": {
            "required": ["source_claim_or_scenario"],
            "optional": ["domain_context", "assumption_list"],
        },
        "output_contract": {
            "text": ["what_if_question", "transformed_scenario", "implications"],
            "image": ["visual_brief", "image_prompt"],
            "multimodal": ["written_brief", "visual_brief", "image_prompt"],
        },
        "theory_mapping": {
            "family": "speculative design",
            "method": "what-if reframing",
        },
        "model_constraints": [
            "Make the transformation explicit.",
            "Preserve traceability to the source input.",
        ],
        "selected": True,
        "placeholder": True,
    },
    {
        "id": "futures-wheel",
        "version": "0.1.0",
        "label": "Futures Wheel",
        "accepted_modalities": ["text", "multimodal"],
        "supported_outputs": ["text", "multimodal"],
        "input_contract": {
            "required": ["seed_scenario"],
            "optional": ["stakeholders", "time_horizon"],
        },
        "output_contract": {
            "text": ["first_order_effects", "second_order_effects", "third_order_effects"],
            "multimodal": ["effect_map", "visual_summary_prompt"],
        },
        "theory_mapping": {
            "family": "futures studies",
            "method": "futures wheel",
        },
        "model_constraints": [
            "Separate consequence levels clearly.",
            "Avoid presenting speculative chains as facts.",
        ],
        "selected": False,
        "placeholder": True,
    },
    {
        "id": "counterfactual",
        "version": "0.1.0",
        "label": "Counterfactual",
        "accepted_modalities": ["text", "image", "multimodal"],
        "supported_outputs": ["text", "image", "multimodal"],
        "input_contract": {
            "required": ["current_or_historical_condition"],
            "optional": ["changed_variable", "constraints"],
        },
        "output_contract": {
            "text": ["counterfactual_premise", "world_state", "tensions"],
            "image": ["artifact_prompt", "visual_anomaly_notes"],
            "multimodal": ["scenario_brief", "artifact_prompt", "tensions"],
        },
        "theory_mapping": {
            "family": "critical/speculative design",
            "method": "counterfactual scenario",
        },
        "model_constraints": [
            "Name the altered assumption.",
            "Keep causal changes plausible inside the chosen premise.",
        ],
        "selected": False,
        "placeholder": True,
    },
    {
        "id": "physical-fiction",
        "version": "0.1.0",
        "label": "Physical Fiction",
        "accepted_modalities": ["text", "image", "multimodal"],
        "supported_outputs": ["multimodal", "image", "text"],
        "input_contract": {
            "required": ["scenario_or_concept"],
            "optional": ["material_cues", "use_context", "scale"],
        },
        "output_contract": {
            "text": ["artifact_description", "use_scene", "critical_question"],
            "image": ["object_visual_prompt", "material_palette", "context_prompt"],
            "multimodal": ["artifact_brief", "object_visual_prompt", "semantic_summary"],
        },
        "theory_mapping": {
            "family": "design fiction",
            "method": "physical fictional artifact",
        },
        "model_constraints": [
            "Describe an inspectable artifact, not an abstract mood.",
            "Keep visual output grounded in the generated scenario.",
        ],
        "selected": True,
        "placeholder": True,
    },
]


def _registry_tools() -> list[dict]:
    package_tools = _package_tools()
    if not TOOL_REGISTRY_FILE.exists():
        return merge_tools(DEFAULT_MODIFIER_TOOLS, package_tools)
    try:
        payload = json.loads(TOOL_REGISTRY_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return merge_tools(DEFAULT_MODIFIER_TOOLS, package_tools)
    tools = payload.get("modifier_tools", payload if isinstance(payload, list) else [])
    if not isinstance(tools, list):
        return merge_tools(DEFAULT_MODIFIER_TOOLS, package_tools)
    normalized = []
    for tool in tools:
        if not isinstance(tool, dict) or not tool.get("id") or not tool.get("label"):
            continue
        normalized.append(normalize_registry_tool(tool))
    return merge_tools(DEFAULT_MODIFIER_TOOLS, package_tools, normalized)


def _package_tools() -> list[dict]:
    if not TOOL_PACKAGE_DIR.exists():
        return []
    tools = []
    for manifest_path in sorted(TOOL_PACKAGE_DIR.glob("*/manifest.json")):
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict) or not payload.get("id") or not payload.get("label"):
            continue
        tool = normalize_registry_tool(payload)
        tool["package_path"] = str(manifest_path.parent.relative_to(TOOL_PACKAGE_DIR.parent))
        tools.append(tool)
    return tools


def merge_tools(*tool_lists: list[dict]) -> list[dict]:
    by_id = {}
    order = []
    for tools in tool_lists:
        for tool in tools:
            tool_id = tool.get("id")
            if not tool_id:
                continue
            if tool_id not in by_id:
                order.append(tool_id)
            by_id[tool_id] = normalize_registry_tool(tool)
            if tool.get("package_path"):
                by_id[tool_id]["package_path"] = tool["package_path"]
    return [by_id[tool_id] for tool_id in order]


def normalize_registry_tool(tool: dict) -> dict:
    ui = tool.get("ui") if isinstance(tool.get("ui"), dict) else {}
    normalized = {
        "id": str(tool["id"]),
        "version": str(tool.get("version") or "0.1.0"),
        "label": str(tool["label"]),
        "description": str(tool.get("description") or ui.get("short_description") or ""),
        "locales": normalize_tool_locales(tool.get("locales")),
        "layer": str(tool.get("layer") or "tool"),
        "family": str(tool.get("family") or "speculative design"),
        "compatible_nodes": tool.get("compatible_nodes") or ["modify"],
        "accepted_modalities": tool.get("accepted_modalities") or ["text"],
        "supported_outputs": tool.get("supported_outputs") or ["text"],
        "selected": bool(tool.get("selected", False)),
        "placeholder": bool(tool.get("placeholder", True)),
        "presentation": normalize_tool_presentation(tool.get("presentation"), tool),
    }
    for key in (
        "input_contract",
        "output_contract",
        "theory_mapping",
        "model_constraints",
        "output_budget",
        "executor",
        "parameters",
        "recommendation",
        "text_output_forms",
        "validation",
        "ui",
        "package_path",
    ):
        if key in tool:
            normalized[key] = deepcopy(tool[key])
    return normalized


def normalize_tool_locales(value: object) -> dict:
    """Expose package-owned display copy without coupling it to the frontend.

    Labels and short descriptions are deliberately the only localized fields at
    this layer; theory, contracts, and execution remain canonical package data.
    """

    if not isinstance(value, dict):
        return {}
    locales = {}
    for language, copy in value.items():
        if not isinstance(copy, dict):
            continue
        label = str(copy.get("label") or "").strip()
        description = str(copy.get("description") or "").strip()
        if label or description:
            locales[str(language)] = {
                "label": label[:120],
                "description": description[:420],
            }
    return locales


def normalize_tool_presentation(value, tool: dict) -> dict:
    """Keep card/graphic metadata with the package that owns tool meaning.

    Asset paths are deliberately package-relative. A frontend may map tokens to a design
    system or load the declared package asset, but it cannot use a card to alter a tool's
    theory, executor, or input/output contract.
    """

    value = value if isinstance(value, dict) else {}
    asset = value.get("asset") if isinstance(value.get("asset"), dict) else {}
    asset_kind = asset.get("kind") if asset.get("kind") in {"none", "package-relative"} else "none"
    raw_asset_path = str(asset.get("path") or "").replace("\\", "/").strip()
    asset_path = raw_asset_path.strip("/")
    if raw_asset_path.startswith("/") or any(part == ".." for part in raw_asset_path.split("/")):
        asset_path = ""
        asset_kind = "none"
    elif asset_path and asset_kind != "package-relative":
        asset_kind = "package-relative"
    elif not asset_path:
        asset_kind = "none"
    summary_fields = []
    for field in value.get("summary_fields", []):
        field_name = str(field).strip()
        if field_name and field_name not in summary_fields:
            summary_fields.append(field_name[:96])
    return {
        "card_kind": str(value.get("card_kind") or "method")[:48],
        "icon_token": str(value.get("icon_token") or tool.get("id") or "tool")[:64],
        "accent_token": str(value.get("accent_token") or "neutral")[:48],
        "asset": {"kind": asset_kind, "path": asset_path},
        "summary_fields": summary_fields or ["description", "theory_mapping.method", "recommendation.best_when"],
        "interaction_hint": str(value.get("interaction_hint") or tool.get("description") or "")[:280],
    }


def list_modifier_tools() -> list[dict]:
    return deepcopy(_registry_tools())


def list_output_types() -> list[dict]:
    return [
        {
            "id": "text",
            "label": "Text",
            "node_type": "text",
            "description": "Written speculative transformation.",
        },
        {
            "id": "image",
            "label": "Image",
            "node_type": "image",
            "description": "Visual artifact with semantic metadata.",
        },
        {
            "id": "multimodal",
            "label": "Text+Image",
            "node_type": "multimodal",
            "description": "Written brief plus visual artifact.",
        },
    ]


def default_modifier_tools() -> list[dict]:
    return [
        {
            "id": tool["id"],
            "label": tool["label"],
            "version": tool["version"],
            "description": tool.get("description", ""),
            "locales": deepcopy(tool.get("locales", {})),
            "selected": tool["selected"],
        }
        for tool in _registry_tools()
    ]


def public_modifier_tools() -> list[dict]:
    return [
        {
            "id": tool["id"],
            "label": tool["label"],
            "version": tool["version"],
            "description": tool.get("description", ""),
            "locales": deepcopy(tool.get("locales", {})),
            "layer": tool.get("layer", "tool"),
            "family": tool.get("family", "speculative design"),
            "compatible_nodes": deepcopy(tool.get("compatible_nodes", ["modify"])),
            "accepted_modalities": deepcopy(tool.get("accepted_modalities", ["text"])),
            "supported_outputs": deepcopy(tool.get("supported_outputs", ["text"])),
            "package_path": tool.get("package_path", ""),
            "presentation": deepcopy(tool.get("presentation", {})),
            "selected": tool["selected"],
        }
        for tool in _registry_tools()
    ]


def normalize_modifier_tools(configured_tools: list[dict] | None) -> list[dict]:
    configured_by_id = {
        tool.get("id"): tool
        for tool in configured_tools or []
        if isinstance(tool, dict) and tool.get("id")
    }
    normalized = []
    for registry_tool in _registry_tools():
        configured = configured_by_id.get(registry_tool["id"], {})
        normalized.append(
            {
                "id": registry_tool["id"],
                "label": registry_tool["label"],
                "version": registry_tool["version"],
                "description": registry_tool.get("description", ""),
                "locales": deepcopy(registry_tool.get("locales", {})),
                "layer": registry_tool.get("layer", "tool"),
                "family": registry_tool.get("family", "speculative design"),
                "compatible_nodes": deepcopy(registry_tool.get("compatible_nodes", ["modify"])),
                "accepted_modalities": deepcopy(registry_tool.get("accepted_modalities", ["text"])),
                "supported_outputs": deepcopy(registry_tool.get("supported_outputs", ["text"])),
                "package_path": registry_tool.get("package_path", ""),
                "presentation": deepcopy(registry_tool.get("presentation", {})),
                "selected": bool(configured.get("selected", registry_tool["selected"])),
            }
        )
    return normalized


def normalize_output_type(output_type: str | None) -> str:
    if output_type in OUTPUT_TYPES:
        return output_type
    return "text"


def tool_snapshot(tool_ids: list[str]) -> list[dict]:
    by_id = {tool["id"]: tool for tool in _registry_tools()}
    return [
        {
            "id": tool_id,
            "version": by_id.get(tool_id, {}).get("version", "unknown"),
            "label": by_id.get(tool_id, {}).get("label", tool_id),
            "description": by_id.get(tool_id, {}).get("description", ""),
            "locales": deepcopy(by_id.get(tool_id, {}).get("locales", {})),
            "layer": by_id.get(tool_id, {}).get("layer", "tool"),
            "family": by_id.get(tool_id, {}).get("family", "speculative design"),
            "compatible_nodes": deepcopy(by_id.get(tool_id, {}).get("compatible_nodes", ["modify"])),
            "accepted_modalities": deepcopy(by_id.get(tool_id, {}).get("accepted_modalities", [])),
            "supported_outputs": deepcopy(by_id.get(tool_id, {}).get("supported_outputs", [])),
            "input_contract": deepcopy(by_id.get(tool_id, {}).get("input_contract", {})),
            "output_contract": deepcopy(by_id.get(tool_id, {}).get("output_contract", {})),
            "theory_mapping": deepcopy(by_id.get(tool_id, {}).get("theory_mapping", {})),
            "model_constraints": deepcopy(by_id.get(tool_id, {}).get("model_constraints", [])),
            "executor": deepcopy(by_id.get(tool_id, {}).get("executor", {})),
            "parameters": deepcopy(by_id.get(tool_id, {}).get("parameters", {})),
            "recommendation": deepcopy(by_id.get(tool_id, {}).get("recommendation", {})),
            "text_output_forms": deepcopy(by_id.get(tool_id, {}).get("text_output_forms", {})),
            "output_budget": deepcopy(by_id.get(tool_id, {}).get("output_budget", {})),
            "validation": deepcopy(by_id.get(tool_id, {}).get("validation", {})),
            "presentation": deepcopy(by_id.get(tool_id, {}).get("presentation", {})),
            "package_path": by_id.get(tool_id, {}).get("package_path", ""),
        }
        for tool_id in tool_ids
    ]


def recommend_output(selected_tool_ids: list[str], input_modalities: list[str] | None = None) -> dict:
    input_modalities = input_modalities or ["text"]
    by_id = {tool["id"]: tool for tool in _registry_tools()}
    items = [
        recommendation_for_tool(by_id[tool_id], input_modalities)
        for tool_id in selected_tool_ids
        if tool_id in by_id
    ]
    if items:
        aggregate_type = aggregate_recommendation_type(items)
        warnings = []
        for item in items:
            warnings.extend(item.get("warnings", []))
        if len(items) == 1:
            item = items[0]
            return {
                "type": item["type"],
                "readiness": item["readiness"],
                "reason": item["reason"],
                "warnings": item.get("warnings", []),
                "items": items,
            }
        return {
            "type": aggregate_type,
            "readiness": "mixed",
            "reason": "Selected tools have separate output recommendations; review each tool before running.",
            "warnings": warnings,
            "items": items,
        }
    if "image" in input_modalities:
        return {
            "type": "multimodal",
            "readiness": "medium",
            "reason": "Image inputs should preserve both semantic explanation and visual reinterpretation.",
            "warnings": [],
            "items": [],
        }
    return {
        "type": "text",
        "readiness": "medium",
        "reason": "Early speculative transformations are easier to review as text.",
        "warnings": [],
        "items": [],
    }


def public_recommendation(recommendation: dict) -> dict:
    items = [
        public_recommendation_item(item)
        for item in recommendation.get("items", [])
        if isinstance(item, dict)
    ]
    return {
        "type": normalize_output_type(recommendation.get("type")),
        "readiness": str(recommendation.get("readiness") or "medium"),
        "reason": str(recommendation.get("reason") or ""),
        "warnings": [
            str(warning)
            for warning in recommendation.get("warnings", [])
            if warning
        ],
        "items": items,
    }


def public_recommendation_item(item: dict) -> dict:
    return {
        "tool_id": str(item.get("tool_id") or ""),
        "label": str(item.get("label") or item.get("tool_id") or ""),
        "type": normalize_output_type(item.get("type")),
        "readiness": str(item.get("readiness") or "medium"),
        "reason": str(item.get("reason") or ""),
        "warnings": [
            str(warning)
            for warning in item.get("warnings", [])
            if warning
        ],
    }


def recommendation_for_tool(tool: dict, input_modalities: list[str]) -> dict:
    recommendation = deepcopy(tool.get("recommendation", {}))
    parameters = tool.get("parameters", {}) if isinstance(tool.get("parameters"), dict) else {}
    output_type = normalize_output_type(
        recommendation.get("type")
        or parameters.get("default_output_type")
        or next(iter(tool.get("supported_outputs", []) or ["text"]), "text")
    )
    warnings = list(recommendation.get("warnings", []))
    if "image" in input_modalities and output_type == "text":
        warnings.append("Image input is connected; add semantic image notes or consider Text+Image if visual reinterpretation is needed.")
    return {
        "tool_id": tool["id"],
        "label": tool.get("label", tool["id"]),
        "type": output_type,
        "readiness": recommendation.get("readiness", "medium"),
        "reason": recommendation.get("reason") or f"{tool.get('label', tool['id'])} should begin with {output_type} output for review.",
        "warnings": warnings,
    }


def aggregate_recommendation_type(items: list[dict]) -> str:
    types = {item.get("type", "text") for item in items}
    if "multimodal" in types or len(types.intersection({"image", "text"})) > 1:
        return "multimodal"
    if "image" in types:
        return "image"
    return "text"


def node_type_for_output(output_type: str) -> str:
    if output_type == "image":
        return "image"
    if output_type == "multimodal":
        return "multimodal"
    return "text"


def title_for_output(output_type: str) -> str:
    return {
        "text": "Text Output",
        "image": "Image Output",
        "multimodal": "Text+Image Output",
    }.get(output_type, "Modify Output")


def placeholder_for_output(output_type: str) -> str:
    return {
        "text": "Placeholder text output. Later this will use concrete tool constraints and the OpenAI Model Service.",
        "image": "Placeholder image output. Later this will call image generation and store semantic metadata.",
        "multimodal": "Placeholder text+image output. Later this will produce a written brief, image prompt, generated asset, and semantic summary.",
    }.get(output_type, "Placeholder output.")
