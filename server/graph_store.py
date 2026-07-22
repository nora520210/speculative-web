from __future__ import annotations

import base64
import json
import uuid
from pathlib import Path

from server.config import DATA_DIR, GENERATED_IMAGE_DIR, ensure_dirs
from server.model_service import (
    ModelServiceError,
    ModelServiceNotConfigured,
    generate_image_response,
    generate_modify_response,
    openai_runs_enabled,
)
from server.modifier_registry import (
    default_modifier_tools,
    normalize_modifier_tools,
    normalize_output_type,
    node_type_for_output,
    placeholder_for_output,
    public_recommendation,
    recommend_output,
    title_for_output,
    tool_snapshot,
)
from server.interaction_runtime import (
    RevisionConflict,
    append_message as append_conversation_message,
    assert_expected_revision,
    create_command_proposal as create_command_proposal_record,
    create_conversation as create_conversation_record,
    create_scope as create_scope_record,
    ensure_interaction_data,
    get_scope,
    interaction_payload,
    record_execution_from_run,
    record_graph_event,
    resolve_command_proposal as resolve_command_proposal_record,
    scope_node_ids,
    scope_projection,
)
from server.operation_registry import normalize_operation_config
from server.visual_context import visual_context_for_nodes


PROJECTS_FILE = DATA_DIR / "projects.json"
CANVAS_DIR = DATA_DIR / "canvases"
NODE_TYPES = {"text", "conversation", "upload", "image", "multimodal", "modify", "operation"}
EDGE_KINDS = {"data", "reference", "control", "configuration-reference"}


def utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ensure_store() -> None:
    ensure_dirs()
    CANVAS_DIR.mkdir(exist_ok=True)
    if not PROJECTS_FILE.exists():
        demo = create_project_record("Speculative Canvas", project_id="demo-canvas")
        PROJECTS_FILE.write_text(json.dumps([demo], ensure_ascii=False, indent=2), encoding="utf-8")
        write_canvas("demo-canvas", default_canvas("demo-canvas"))
    else:
        for project in read_projects():
            canvas_path = canvas_file(project["id"])
            if not canvas_path.exists():
                write_canvas(project["id"], default_canvas(project["id"]))


def create_project_record(title: str, project_id: str | None = None) -> dict:
    now = utc_now()
    return {
        "id": project_id or uuid.uuid4().hex[:12],
        "title": title[:96] or "Untitled Canvas",
        "status": "active",
        "updated_at": now,
        "node_count": 4 if project_id == "demo-canvas" else 0,
        "canvas_id": project_id or "",
    }


def read_projects() -> list[dict]:
    ensure_store_light()
    return json.loads(PROJECTS_FILE.read_text(encoding="utf-8"))


def write_projects(projects: list[dict]) -> None:
    ensure_dirs()
    write_json_atomically(PROJECTS_FILE, projects)


def create_project(title: str) -> dict:
    ensure_store()
    project = create_project_record(title)
    project["canvas_id"] = project["id"]
    projects = read_projects()
    projects.insert(0, project)
    write_projects(projects)
    write_canvas(project["id"], empty_canvas(project["id"]))
    return project


def update_project(project_id: str, patch: dict) -> dict:
    projects = read_projects()
    title = str(patch.get("title") or "").strip()
    if not title:
        raise ValueError("Project title cannot be empty.")
    for project in projects:
        if project["id"] == project_id:
            project["title"] = title[:96]
            project["updated_at"] = utc_now()
            write_projects(projects)
            return project
    raise KeyError(f"Project not found: {project_id}")


def delete_project(project_id: str) -> dict:
    projects = read_projects()
    project = next((item for item in projects if item["id"] == project_id), None)
    if not project:
        raise KeyError(f"Project not found: {project_id}")
    write_projects([item for item in projects if item["id"] != project_id])
    path = canvas_file(project_id)
    if path.exists():
        path.unlink()
    safe_project_id = "".join(char for char in project_id if char.isalnum() or char in {"-", "_"})[:48]
    if GENERATED_IMAGE_DIR.exists():
        for image_path in GENERATED_IMAGE_DIR.glob(f"{safe_project_id}-*.png"):
            image_path.unlink()
    return {"project": project}


def get_project(project_id: str) -> dict | None:
    for project in read_projects():
        if project["id"] == project_id:
            return project
    return None


def touch_project(project_id: str, node_count: int | None = None) -> None:
    projects = read_projects()
    for project in projects:
        if project["id"] == project_id:
            project["updated_at"] = utc_now()
            if node_count is not None:
                project["node_count"] = node_count
            break
    write_projects(projects)


def canvas_file(project_id: str) -> Path:
    return CANVAS_DIR / f"{project_id}.json"


def read_canvas(project_id: str) -> dict:
    ensure_store()
    path = canvas_file(project_id)
    if not path.exists():
        canvas = empty_canvas(project_id)
        write_canvas(project_id, canvas)
        return canvas
    canvas = json.loads(path.read_text(encoding="utf-8"))
    ensure_interaction_data(canvas)
    refresh_runtime_config(canvas)
    return canvas


def write_canvas(project_id: str, canvas: dict) -> None:
    ensure_dirs()
    CANVAS_DIR.mkdir(exist_ok=True)
    ensure_interaction_data(canvas)
    canvas["updated_at"] = utc_now()
    write_json_atomically(canvas_file(project_id), canvas)
    touch_project(project_id, node_count=len(canvas.get("nodes", [])))


def write_json_atomically(path: Path, payload) -> None:
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex[:8]}.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def get_interaction(project_id: str) -> dict:
    return interaction_payload(read_canvas(project_id))


def get_scope_projection(project_id: str, scope_id: str) -> dict:
    return scope_projection(read_canvas(project_id), scope_id)


def add_scope(project_id: str, payload: dict, expected_revision=None) -> dict:
    canvas = read_canvas(project_id)
    assert_expected_revision(canvas, expected_revision)
    scope = create_scope_record(canvas, payload)
    record_graph_event(canvas, "scope.created", {"scope_id": scope["id"]})
    write_canvas(project_id, canvas)
    return scope


def add_conversation(project_id: str, payload: dict, expected_revision=None) -> dict:
    canvas = read_canvas(project_id)
    assert_expected_revision(canvas, expected_revision)
    session = create_conversation_record(canvas, payload)
    record_graph_event(canvas, "conversation.created", {"session_id": session["id"]})
    write_canvas(project_id, canvas)
    return session


def add_conversation_message(project_id: str, session_id: str, payload: dict, expected_revision=None) -> dict:
    canvas = read_canvas(project_id)
    assert_expected_revision(canvas, expected_revision)
    message = append_conversation_message(canvas, session_id, payload)
    record_graph_event(canvas, "conversation.message_added", {"session_id": session_id, "message_id": message["id"]})
    write_canvas(project_id, canvas)
    return message


def add_command_proposal(project_id: str, payload: dict, expected_revision=None) -> dict:
    canvas = read_canvas(project_id)
    assert_expected_revision(canvas, expected_revision)
    proposal = create_command_proposal_record(canvas, payload)
    record_graph_event(canvas, "command.proposed", {"command_id": proposal["id"], "action": proposal["action"]})
    write_canvas(project_id, canvas)
    return proposal


def resolve_command_proposal(project_id: str, command_id: str, resolution: str, expected_revision=None) -> dict:
    canvas = read_canvas(project_id)
    assert_expected_revision(canvas, expected_revision)
    proposal = resolve_command_proposal_record(canvas, command_id, resolution)
    record_graph_event(canvas, "command.resolved", {"command_id": command_id, "status": resolution})
    write_canvas(project_id, canvas)
    return proposal


def add_node(project_id: str, payload: dict, expected_revision=None) -> dict:
    canvas = read_canvas(project_id)
    assert_expected_revision(canvas, expected_revision)
    node = normalize_node(payload)
    canvas["nodes"].append(node)
    refresh_runtime_config(canvas)
    record_graph_event(canvas, "node.created", {"node_id": node["id"], "node_type": node["type"]})
    write_canvas(project_id, canvas)
    return node


def update_node(project_id: str, node_id: str, patch: dict, expected_revision=None) -> dict:
    canvas = read_canvas(project_id)
    assert_expected_revision(canvas, expected_revision)
    for node in canvas["nodes"]:
        if node["id"] == node_id:
            node.update({key: value for key, value in patch.items() if key in {"position", "size", "status"}})
            if "config" in patch and isinstance(patch["config"], dict):
                node.setdefault("config", {}).update(patch["config"])
            if "payload" in patch and isinstance(patch["payload"], dict):
                node.setdefault("payload", {}).update(patch["payload"])
            refresh_runtime_config(canvas)
            record_graph_event(canvas, "node.updated", {"node_id": node_id, "fields": sorted(patch.keys())})
            write_canvas(project_id, canvas)
            return node
    raise KeyError(f"Node not found: {node_id}")


def delete_node(project_id: str, node_id: str, expected_revision=None) -> dict:
    canvas = read_canvas(project_id)
    assert_expected_revision(canvas, expected_revision)
    node = next((item for item in canvas.get("nodes", []) if item.get("id") == node_id), None)
    if not node:
        raise KeyError(f"Node not found: {node_id}")

    removed_edge_ids = [
        edge["id"]
        for edge in canvas.get("edges", [])
        if edge.get("source_node_id") == node_id or edge.get("target_node_id") == node_id
    ]
    removed_run_ids = [
        run["id"]
        for run in canvas.get("runs", [])
        if run.get("node_id") == node_id or node_id in run.get("input_node_ids", [])
    ]
    canvas["nodes"] = [item for item in canvas.get("nodes", []) if item.get("id") != node_id]
    canvas["edges"] = [
        edge
        for edge in canvas.get("edges", [])
        if edge.get("source_node_id") != node_id and edge.get("target_node_id") != node_id
    ]
    for run in canvas.get("runs", []):
        if run.get("id") not in removed_run_ids:
            continue
        orphaned = run.setdefault("orphaned_node_ids", [])
        if node_id not in orphaned:
            orphaned.append(node_id)
        run["status"] = "orphaned"
    for item in canvas.get("nodes", []):
        if item.get("active_run_id") in removed_run_ids:
            item["active_run_id"] = None
        if item.get("produced_by_run_id") in removed_run_ids:
            item["status"] = "stale"
    refresh_runtime_config(canvas)
    record_graph_event(canvas, "node.deleted", {"node_id": node_id, "preserved_run_ids": removed_run_ids})
    write_canvas(project_id, canvas)
    return {
        "node": node,
        "removed_edges": removed_edge_ids,
        "removed_runs": removed_run_ids,
    }


def add_edge(project_id: str, payload: dict, expected_revision=None) -> dict:
    canvas = read_canvas(project_id)
    assert_expected_revision(canvas, expected_revision)
    node_ids = {node["id"] for node in canvas.get("nodes", [])}
    source_node_id = payload["source_node_id"]
    target_node_id = payload["target_node_id"]
    if source_node_id not in node_ids:
        raise KeyError(f"Source node not found: {source_node_id}")
    if target_node_id not in node_ids:
        raise KeyError(f"Target node not found: {target_node_id}")
    edge_kind = payload.get("edge_kind", "data")
    if edge_kind not in EDGE_KINDS:
        raise ValueError(f"Unsupported edge kind: {edge_kind}")
    edge = {
        "id": payload.get("id") or f"edge-{uuid.uuid4().hex[:8]}",
        "source_node_id": source_node_id,
        "target_node_id": target_node_id,
        "source_port": payload.get("source_port", "out"),
        "target_port": payload.get("target_port", "in"),
        "edge_kind": edge_kind,
        "created_at": utc_now(),
    }
    canvas["edges"].append(edge)
    refresh_runtime_config(canvas)
    record_graph_event(canvas, "edge.created", {"edge_id": edge["id"], "edge_kind": edge_kind})
    write_canvas(project_id, canvas)
    return edge


def delete_edge(project_id: str, edge_id: str, expected_revision=None) -> dict:
    canvas = read_canvas(project_id)
    assert_expected_revision(canvas, expected_revision)
    edge = next((item for item in canvas.get("edges", []) if item.get("id") == edge_id), None)
    if not edge:
        raise KeyError(f"Edge not found: {edge_id}")
    canvas["edges"] = [item for item in canvas.get("edges", []) if item.get("id") != edge_id]
    refresh_runtime_config(canvas)
    record_graph_event(canvas, "edge.deleted", {"edge_id": edge_id})
    write_canvas(project_id, canvas)
    return {"edge": edge}


def run_modify(project_id: str, node_id: str, api_key: str | None = None, expected_revision=None) -> dict:
    canvas = read_canvas(project_id)
    assert_expected_revision(canvas, expected_revision)
    modify = next((node for node in canvas["nodes"] if node["id"] == node_id), None)
    if not modify:
        raise KeyError(f"Modify node not found: {node_id}")
    if modify.get("type") != "modify":
        raise ValueError("Only modify nodes can be run through this endpoint.")

    upstream_edges = ordered_data_input_edges(canvas, node_id)
    upstream_ids = [edge["source_node_id"] for edge in upstream_edges if edge.get("edge_kind") == "data"]
    selected_tools = [
        tool["id"]
        for tool in modify.get("config", {}).get("tools", [])
        if tool.get("selected")
    ]
    input_modalities = input_modalities_for_nodes(canvas, upstream_ids)
    output_type = normalize_output_type(modify.get("config", {}).get("output_type"))
    recommendation = recommend_output(selected_tools, input_modalities)
    snapshot = tool_snapshot(selected_tools)
    run_id = f"run-{uuid.uuid4().hex[:10]}"
    model_payload = generate_or_placeholder_output(
        project_id,
        run_id,
        canvas,
        upstream_ids,
        snapshot,
        output_type,
        recommendation,
        api_key,
    )
    run = {
        "id": run_id,
        "node_id": node_id,
        "status": model_payload["run_status"],
        "input_node_ids": upstream_ids,
        "context_snapshot": {
            "direct_input_node_ids": upstream_ids,
            "edge_policy": "data edges only; sibling branches excluded",
            "selected_tools": selected_tools,
            "tool_snapshot": snapshot,
            "input_modalities": input_modalities,
            "requested_output_type": output_type,
            "output_recommendation": recommendation,
        },
        "model_snapshot": model_payload["model_snapshot"],
        "created_at": utc_now(),
    }
    output_node = normalize_node(
        {
            "type": node_type_for_output(output_type),
            "title": title_for_output(output_type),
            "position": {
                "x": modify.get("position", {}).get("x", 0) + 330,
                "y": modify.get("position", {}).get("y", 0) + 28,
            },
            "payload": {
                "text": model_payload["text"],
                "requested_output_type": output_type,
                "recommendation": recommendation,
                "model_output": model_payload.get("model_output"),
                "image_prompt": model_payload.get("image_prompt"),
                "image_url": model_payload.get("image_url"),
                "image_file": model_payload.get("image_file"),
                "image_error": model_payload.get("image_error"),
                "semantic_summary": model_payload.get("semantic_summary"),
                "visual_basis": model_payload.get("visual_basis", {}),
                "input_image_node_ids": model_payload.get("input_image_node_ids", []),
                "provenance": [{"produced_by_run_id": run["id"]}],
            },
            "status": "success" if model_payload["run_status"] == "succeeded" else "failed",
        }
    )
    output_node["produced_by_run_id"] = run["id"]
    edge = {
        "id": f"edge-{uuid.uuid4().hex[:8]}",
        "source_node_id": node_id,
        "target_node_id": output_node["id"],
        "source_port": "out",
        "target_port": "in",
        "edge_kind": "data",
        "created_at": utc_now(),
    }
    canvas["runs"].append(run)
    canvas["nodes"].append(output_node)
    canvas["edges"].append(edge)
    modify["active_run_id"] = run["id"]
    modify["status"] = "success" if run["status"] == "succeeded" else "failed"
    scope_id = next(
        (
            scope["id"]
            for scope in canvas.get("scopes", [])
            if scope.get("id") != "scope-global" and node_id in scope_node_ids(canvas, scope)
        ),
        "scope-global",
    )
    execution = record_execution_from_run(canvas, run, scope_id)
    record_graph_event(canvas, "execution.completed", {"execution_id": execution["id"], "run_id": run["id"], "status": run["status"]})
    write_canvas(project_id, canvas)
    return {"run": run, "execution": execution, "output_node": output_node, "edge": edge}


def generate_or_placeholder_output(
    project_id: str,
    run_id: str,
    canvas: dict,
    upstream_ids: list[str],
    snapshot: list[dict],
    output_type: str,
    recommendation: dict,
    api_key: str | None = None,
) -> dict:
    if not openai_runs_enabled():
        return placeholder_model_payload(output_type, recommendation)
    visual_context = visual_context_for_nodes(canvas, upstream_ids)
    try:
        model_result = generate_modify_response(
            build_modify_prompt(
                canvas,
                upstream_ids,
                snapshot,
                output_type,
                recommendation,
                visual_references=visual_context["references"],
            ),
            api_key=api_key,
            image_inputs=visual_context["inputs"],
        )
    except (ModelServiceError, ModelServiceNotConfigured) as exc:
        return {
            "run_status": "failed",
            "text": f"OpenAI generation failed: {exc}",
            "model_output": {"error": str(exc)},
            "image_prompt": "",
            "semantic_summary": "",
            "visual_basis": {},
            "input_image_node_ids": [item["node_id"] for item in visual_context["inputs"]],
            "model_snapshot": {
                "provider": "openai",
                "capability": "structured_text",
                "api_ready": True,
                "generated": False,
                "error": str(exc),
            },
        }

    parsed = parse_model_json(model_result["text"])
    text = output_text_from_model(parsed, model_result["text"], output_type)
    parsed = ensure_text_blocks(parsed, text, snapshot, output_type, api_key=api_key)
    image_prompt, visual_basis = image_prompt_for_output(
        parsed,
        text,
        output_type,
        upstream_ids,
        visual_context["references"],
    )
    image_result = image_payload_for_output(project_id, run_id, image_prompt, output_type, api_key=api_key)
    return {
        "run_status": "failed" if image_result.get("image_error") and output_type in {"image", "multimodal"} else "succeeded",
        "text": text,
        "model_output": parsed or {"raw_text": model_result["text"]},
        "image_prompt": image_prompt,
        "semantic_summary": (parsed or {}).get("semantic_summary", ""),
        "visual_basis": visual_basis,
        "input_image_node_ids": [item["node_id"] for item in visual_context["inputs"]],
        "image_url": image_result.get("image_url", ""),
        "image_file": image_result.get("image_file", ""),
        "image_error": image_result.get("image_error", ""),
        "model_snapshot": {
            "provider": model_result["provider"],
            "api": model_result["api"],
            "model": model_result["model"],
            "image_api": image_result.get("image_api", ""),
            "image_model": image_result.get("image_model", ""),
            "capability": "structured_text",
            "api_ready": True,
            "generated": True,
            "fallback_reason": model_result.get("fallback_reason", ""),
            "input_image_count": len(visual_context["inputs"]),
            "input_image_node_ids": [item["node_id"] for item in visual_context["inputs"]],
        },
    }


def image_prompt_for_output(
    parsed: dict | None,
    text: str,
    output_type: str,
    upstream_ids: list[str],
    visual_references: list[dict],
) -> tuple[str, dict]:
    if output_type not in {"image", "multimodal"}:
        return "", {}
    visual_basis = visual_basis_from_parsed_output(parsed)
    conclusion = render_model_value(visual_basis.get("conclusion_text", ""))
    referenced_ids = [
        node_id
        for node_id in normalize_node_id_list(visual_basis.get("evidence_node_ids", []))
        if isinstance(node_id, str) and node_id in upstream_ids
    ]
    reference_image_ids = [
        node_id
        for node_id in normalize_node_id_list(visual_basis.get("reference_image_node_ids", []))
        if isinstance(node_id, str) and any(item.get("node_id") == node_id for item in visual_references)
    ]
    evidence = {
        "conclusion_text": conclusion,
        "evidence_node_ids": referenced_ids,
        "reference_image_node_ids": reference_image_ids,
    }
    if not conclusion or not referenced_ids:
        return "", evidence
    image_prompt = render_model_value((parsed or {}).get("image_prompt", ""))
    if not image_prompt:
        return "", evidence
    return constrained_image_prompt(image_prompt, conclusion), evidence


def visual_basis_from_parsed_output(parsed: dict | None) -> dict:
    if not isinstance(parsed, dict):
        return {}
    visual_basis = parsed.get("visual_basis")
    if isinstance(visual_basis, dict):
        return visual_basis
    # A malformed nested text_blocks value can flatten these fields during JSON repair.
    return {
        "conclusion_text": parsed.get("conclusion_text", ""),
        "evidence_node_ids": parsed.get("evidence_node_ids", []),
        "reference_image_node_ids": parsed.get("reference_image_node_ids", []),
    }


def normalize_node_id_list(value) -> list[str]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return []
    return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []


TEXT_BLOCK_TYPES = {"callout", "paragraph", "table", "bar_chart", "list", "questions"}


def normalize_text_blocks(value):
    if isinstance(value, list):
        return value
    if not isinstance(value, str):
        return value
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError:
        return value
    return decoded if isinstance(decoded, list) else value


def ensure_text_blocks(
    parsed: dict | None,
    text: str,
    snapshot: list[dict],
    output_type: str,
    api_key: str | None = None,
) -> dict | None:
    if output_type != "text" or not text_forms_for_snapshot(snapshot):
        return parsed
    if isinstance(parsed, dict):
        normalized_blocks = normalize_text_blocks(parsed.get("text_blocks"))
        if valid_text_blocks(normalized_blocks):
            normalized = dict(parsed)
            normalized["text_blocks"] = normalized_blocks
            return normalized
    try:
        repair = generate_modify_response(build_text_block_repair_prompt(snapshot, text), api_key=api_key)
    except (ModelServiceError, ModelServiceNotConfigured):
        return parsed
    repaired = parse_model_json(repair.get("text", ""))
    repaired_blocks = normalize_text_blocks((repaired or {}).get("text_blocks"))
    if not valid_text_blocks(repaired_blocks):
        return parsed
    enriched = dict(parsed or {})
    enriched["text_blocks"] = repaired_blocks
    return enriched


def text_forms_for_snapshot(snapshot: list[dict]) -> list[dict]:
    return [
        {
            "id": tool.get("id", ""),
            "label": tool.get("label", tool.get("id", "")),
            "text_output_forms": tool.get("text_output_forms", {}),
        }
        for tool in snapshot
        if isinstance(tool, dict) and isinstance(tool.get("text_output_forms"), dict)
    ]


def valid_text_blocks(value) -> bool:
    if not isinstance(value, list) or not value:
        return False
    for block in value:
        if not isinstance(block, dict) or block.get("type") not in TEXT_BLOCK_TYPES:
            return False
        block_type = block["type"]
        if block_type in {"callout", "paragraph"} and not isinstance(block.get("text"), str):
            return False
        if block_type == "table":
            if not isinstance(block.get("columns"), list) or not isinstance(block.get("rows"), list):
                return False
        if block_type in {"bar_chart", "list", "questions"} and not isinstance(block.get("items"), list):
            return False
    return True


def build_text_block_repair_prompt(snapshot: list[dict], written_output: str) -> str:
    payload = {
        "task": "Convert a completed speculative-design text into structured reader blocks.",
        "rules": [
            "Return valid JSON only. Do not return generated_text, summary, Markdown, or explanatory prose outside JSON.",
            "Preserve the written output's language, uncertainty, and distinction between evidence and speculation.",
            "Follow each selected tool's required block sequence in selected-tool order. Keep block groups distinct.",
            "Use only callout {title, text}, paragraph {title, text}, table {title, columns, rows}, bar_chart {title, items}, list {title, items}, and questions {title, items}.",
            "Tables use arrays, never Markdown pipe syntax. Bar-chart values are integers from 1 to 5 and mean discussion priority, not probability.",
            "Be concise: do not repeat the entire source text. Prefer 3-8 rows per table and 3-5 items per question or chart block.",
        ],
        "selected_tools": text_forms_for_snapshot(snapshot),
        "written_output": written_output[:9000],
        "required_response_shape": {
            "text_blocks": [
                {
                    "type": "callout | paragraph | table | bar_chart | list | questions",
                    "title": "Localized title",
                    "text": "For callout and paragraph",
                    "columns": ["For table"],
                    "rows": [["For table"]],
                    "items": ["For bar_chart, list, or questions"],
                }
            ]
        },
    }
    return "Return valid JSON only.\n\n" + json.dumps(payload, ensure_ascii=False, indent=2)


def constrained_image_prompt(scene_prompt: str, semantic_basis: str) -> str:
    return (
        "Global visual style: wide cinematic documentary photograph, expanded field of view, pure white or near-white studio/lab/gallery background "
        "unless the semantic basis explicitly requires a real environment. Use realistic optical perspective, soft neutral lighting, high material detail, "
        "clean spatial composition, and a slightly surreal speculative-design core expressed through concrete objects, machines, product-like artifacts, "
        "non-human-centered systems, labels, instruments, or embodied props. Prefer a full object or scene view over tight close-up. "
        "Avoid generic sci-fi, neon, fantasy, dark mood lighting, glossy advertising, abstract graphics, pure flowcharts, text-heavy infographics, "
        "illustration, UI mockups, decorative symbolism, and freestanding presentation boards, posters, whiteboards, or scenario matrices as the main subject. "
        "When documents are relevant, show one as a subordinate physical prop beside an inspectable device, specimen, tool, or material system. "
        "Any people should be secondary to the object or system. Any visible labels or institutional cues must be justified by the semantic basis. "
        f"Scene prompt: {scene_prompt} "
        f"Semantic basis: {semantic_basis}"
    )


def image_payload_for_output(
    project_id: str,
    run_id: str,
    image_prompt: str,
    output_type: str,
    api_key: str | None = None,
) -> dict:
    if output_type not in {"image", "multimodal"}:
        return {}
    if not image_prompt:
        return {
            "image_error": (
                "Image generation requires a concrete prompt tied to a visual_basis conclusion and direct evidence-node IDs."
            )
        }
    try:
        result = generate_image_response(image_prompt, api_key=api_key)
    except (ModelServiceError, ModelServiceNotConfigured) as exc:
        return {"image_error": str(exc)}
    if result.get("b64_json"):
        image_file = save_generated_image(project_id, run_id, result["b64_json"])
        return {
            "image_url": f"/generated/{image_file.name}",
            "image_file": str(image_file.relative_to(DATA_DIR.parent)),
            "image_api": result["api"],
            "image_model": result["model"],
        }
    return {
        "image_url": result.get("url", ""),
        "image_file": "",
        "image_api": result["api"],
        "image_model": result["model"],
    }


def save_generated_image(project_id: str, run_id: str, b64_json: str) -> Path:
    ensure_dirs()
    safe_project_id = "".join(char for char in project_id if char.isalnum() or char in {"-", "_"})[:48]
    path = GENERATED_IMAGE_DIR / f"{safe_project_id}-{run_id}.png"
    path.write_bytes(base64.b64decode(b64_json))
    return path


def placeholder_model_payload(output_type: str, recommendation: dict) -> dict:
    return {
        "run_status": "succeeded",
        "text": placeholder_for_output(output_type),
        "model_output": {
            "summary": "Placeholder output because OpenAI runs are disabled.",
            "recommendation": recommendation,
        },
        "image_prompt": "",
        "image_url": "",
        "image_file": "",
        "image_error": "",
        "semantic_summary": "",
        "model_snapshot": {
            "provider": "placeholder",
            "capability": "structured_text",
            "api_ready": False,
            "generated": False,
        },
    }


def build_modify_prompt(
    canvas: dict,
    upstream_ids: list[str],
    snapshot: list[dict],
    output_type: str,
    recommendation: dict,
    visual_references: list[dict] | None = None,
) -> str:
    context = upstream_context(canvas, upstream_ids)
    response_language = infer_response_language(context)
    text_blocks_rule = (
        "For text outputs, inspect each selected tool's text_output_forms. When a definition is present, "
        "return text_blocks that follow its required block sequence and table columns. When several selected tools define forms, keep each "
        "tool's block group separate and preserve selected-tool order rather than merging them into one generic summary. Use only these block types: "
        "callout {title, text}, paragraph {title, text}, table {title, columns, rows}, bar_chart {title, items}, "
        "list {title, items}, and questions {title, items}. Tables must be structured arrays, never Markdown pipe tables. "
        "Bar-chart values are discussion weights only, never probabilities or evidence scores. Keep generated_text as a compact plain-text "
        "fallback under 60 words; do not duplicate table rows, charts, lists, or questions that belong in text_blocks."
        if output_type == "text"
        else "For image and text+image outputs, omit text_blocks entirely. Keep generated_text concise so visual_basis and image_prompt remain complete."
    )
    text_blocks_shape = (
        [
            {
                "type": "table | callout | paragraph | bar_chart | list | questions",
                "title": "Localized short block title",
                "text": "Required by callout and paragraph blocks",
                "columns": ["Required by table blocks"],
                "rows": [["Required by table blocks"]],
                "items": ["Required by bar_chart, list, and questions blocks"],
            }
        ]
        if output_type == "text"
        else "Omit this field."
    )
    payload = {
        "task": "Run a Modify node in a speculative design node canvas.",
        "runtime_rule": "Use only direct data-edge inputs as source material. Do not claim certainty for speculative outcomes.",
        "system_method_rule": (
            "Direct input nodes are expected to contain research directions, datasets, hypotheses, engineering constraints, observations, or project plans. "
            "Do not expect the user to write a design-fiction brief, select a speculative method in prose, request an output language, or state image-style rules. "
            "The selected tool packages supply the method logic. Translate research inputs into speculative design outputs by applying "
            "the selected tools' theory mappings, input/output contracts, and constraints. For scientific inputs, preserve plausible "
            "research limits, separate evidence from speculation, and avoid magical or product-marketing claims."
        ),
        "language_rule": (
            "Use the detected dominant language of the direct research input for every human-readable JSON string field, "
            "including summary, generated_text, image_prompt, semantic_summary, discussion_questions, and source_trace. "
            "Only keep proper nouns, visible labels, or technical acronyms in another language when necessary. Do not require a language instruction in the input."
        ),
        "response_language": response_language,
        "length_rule": (
            "Keep the response concise. Summary: at most 25 words. generated_text: at most 60 words. "
            "image_prompt: at most 80 words. A callout or paragraph: at most 40 words. "
            "Use at most 3 rows per table, 3 bars per chart, and 3 items per list or question block. "
            "Keep the tool's information architecture but remove repetition, preambles, and duplicated evidence."
        ),
        "text_output_rule": text_blocks_rule,
        "visual_input_rule": (
            "The direct inputs may include real reference images. Treat them as evidence, not decoration: inspect their material, scale, "
            "embodiment, use context, and omissions alongside the text. Do not claim you saw an image when no reference image is supplied."
        ),
        "image_style_rule": (
            "For image or text+image outputs, write image_prompt as a wide cinematic documentary photograph on a pure white or near-white background "
            "unless the generated scenario explicitly requires a real environment. The image should show a concrete inspectable artifact, machine, interface, "
            "product-like object, non-human-centered system, or embodied prop with realistic material detail and a subtly surreal speculative-design premise. "
            "Avoid generic sci-fi, neon, fantasy, dark mood lighting, glossy advertising, abstract illustration, pure flowcharts, text-heavy infographics, "
            "freestanding presentation boards, posters, whiteboards, scenario matrices, and tight close-up framing. If a document is needed, it must be a subordinate prop beside a concrete device or material system."
        ),
        "image_evidence_rule": (
            "For image or text+image outputs, generate an image only from a concrete conclusion grounded in direct input nodes. "
            "Return visual_basis with a concise conclusion_text, evidence_node_ids chosen only from direct input IDs, and reference_image_node_ids "
            "chosen only from real supplied image nodes. The image_prompt must be a visual synthesis of that conclusion and, when supplied, the "
            "reference images. Do not create an image prompt from generic atmosphere, an unsupported claim, or a freestanding scenario matrix."
        ),
        "requested_output_type": output_type,
        "output_recommendation": recommendation,
        "direct_inputs": context,
        "real_reference_images": visual_references or [],
        "selected_tools": snapshot,
        "required_response_shape": {
            "summary": "One sentence describing the generated transformation.",
            "generated_text": "A compact plain-text fallback under 60 words. Required for text and text+image outputs. For text outputs, do not duplicate text_blocks or nest an object in this field.",
            "text_blocks": text_blocks_shape,
            "image_prompt": "A concrete visual generation prompt. Required for image and text+image outputs; otherwise empty string.",
            "visual_basis": {
                "conclusion_text": "A concise conclusion from direct evidence that the image will materialize.",
                "evidence_node_ids": ["Direct input node IDs only"],
                "reference_image_node_ids": ["Direct real image node IDs only, if any"],
            },
            "semantic_summary": "A compact semantic description of any proposed image or artifact.",
            "discussion_questions": ["Two or three questions for critique or continuation."],
            "source_trace": ["Short notes mapping output decisions back to input nodes and selected tools."],
        },
    }
    return (
        "Return valid JSON only. No markdown fences. Respect each selected tool's theory mapping, "
        "input/output contract, and model constraints.\n\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )


def infer_response_language(context: list[dict]) -> str:
    import re

    text = "\n".join(str(item.get("text", "")) for item in context)
    if len(re.findall(r"[\u4e00-\u9fff]", text)) >= 4:
        return "Chinese"
    if len(re.findall(r"[\u3040-\u30ff]", text)) >= 4:
        return "Japanese"
    if len(re.findall(r"[\uac00-\ud7af]", text)) >= 4:
        return "Korean"
    return "the dominant language of the direct input"


def upstream_context(canvas: dict, upstream_ids: list[str]) -> list[dict]:
    by_id = {node["id"]: node for node in canvas.get("nodes", [])}
    context = []
    for node_id in upstream_ids:
        node = by_id.get(node_id)
        if not node:
            continue
        payload = node.get("payload", {})
        context.append(
            {
                "id": node["id"],
                "type": node.get("type"),
                "title": node.get("title"),
                "text": payload.get("text", ""),
                "semantic_status": payload.get("semantic_status", ""),
            }
        )
    return context


def ordered_data_input_edges(canvas: dict, node_id: str) -> list[dict]:
    indexed_edges = [
        (index, edge)
        for index, edge in enumerate(canvas.get("edges", []))
        if edge.get("target_node_id") == node_id and edge.get("edge_kind") == "data"
    ]
    indexed_edges.sort(key=lambda item: (item[1].get("created_at") or "", item[0]))
    return [edge for _, edge in indexed_edges]


def parse_model_json(text: str) -> dict | None:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start < 0:
            return None
        if end <= start:
            return parse_jsonish_object(cleaned[start:])
        try:
            parsed = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError:
            parsed = parse_repaired_json_object(cleaned[start : end + 1])
            if parsed is None:
                return parse_jsonish_object(cleaned[start : end + 1])
            return parsed
    return parsed if isinstance(parsed, dict) else None


def parse_repaired_json_object(text: str) -> dict | None:
    repaired = []
    in_string = False
    escaped = False
    for char in text:
        if in_string:
            if escaped:
                repaired.append(char)
                escaped = False
                continue
            if char == "\\":
                repaired.append(char)
                escaped = True
                continue
            if char == '"':
                repaired.append(char)
                in_string = False
                continue
            if char == "\n":
                repaired.append("\\n")
                continue
            if char == "\r":
                repaired.append("\\r")
                continue
            if char == "\t":
                repaired.append("\\t")
                continue
        else:
            if char == '"':
                in_string = True
        repaired.append(char)
    try:
        parsed = json.loads("".join(repaired))
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def parse_jsonish_object(text: str) -> dict | None:
    import re

    matches = list(re.finditer(r'(?m)^\s*"([A-Za-z0-9_]+)"\s*:\s*', text))
    if not matches:
        return None
    parsed: dict[str, str] = {}
    for index, match in enumerate(matches):
        key = match.group(1)
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        value = text[start:end].strip()
        value = value.rstrip().removesuffix(",").rstrip()
        value = value.removesuffix("}").rstrip()
        if value.startswith('"'):
            value = value[1:]
        if value.endswith('"'):
            value = value[:-1]
        value = value.replace("\\n", "\n").replace('\\"', '"').strip()
        if value:
            parsed[key] = value
    return parsed or None


def output_text_from_model(parsed: dict | None, raw_text: str, output_type: str) -> str:
    if not parsed:
        return raw_text.strip()
    if output_type == "image":
        return render_model_value(
            parsed.get("semantic_summary") or parsed.get("image_prompt") or parsed.get("summary") or raw_text
        )
    parts = [
        render_model_value(parsed.get("summary", "")),
        render_model_value(parsed.get("generated_text", "")),
    ]
    if output_type == "multimodal" and parsed.get("image_prompt"):
        parts.append(f"Image prompt: {render_model_value(parsed['image_prompt'])}")
    return "\n\n".join(part for part in parts if part).strip() or raw_text.strip()


def render_model_value(value) -> str:
    if isinstance(value, str):
        return value.strip()
    if value in (None, ""):
        return ""
    return json.dumps(value, ensure_ascii=False, indent=2)


def recommend_output_for_modify(modify: dict) -> dict:
    if modify.get("config", {}).get("output_recommendation"):
        return public_recommendation(modify["config"]["output_recommendation"])
    selected = [
        tool["id"]
        for tool in modify.get("config", {}).get("tools", [])
        if tool.get("selected")
    ]
    return public_recommendation(recommend_output(selected))


def refresh_runtime_config(canvas: dict) -> None:
    for node in canvas.get("nodes", []):
        if node.get("type") == "modify":
            node["config"] = normalize_modify_config(
                node.get("config", {}),
                input_modalities_for_modify(canvas, node["id"]),
            )
        if node.get("type") == "operation":
            node["config"] = normalize_operation_config(node.get("config", {}))


def input_modalities_for_modify(canvas: dict, node_id: str) -> list[str]:
    upstream_ids = [
        edge["source_node_id"]
        for edge in canvas.get("edges", [])
        if edge.get("target_node_id") == node_id and edge.get("edge_kind") == "data"
    ]
    return input_modalities_for_nodes(canvas, upstream_ids)


def normalize_modify_config(config: dict, input_modalities: list[str] | None = None) -> dict:
    tools = normalize_modifier_tools(config.get("tools") if isinstance(config, dict) else None)
    output_type = normalize_output_type(config.get("output_type") if isinstance(config, dict) else None)
    selected_tools = [tool["id"] for tool in tools if tool.get("selected")]
    return {
        **(config if isinstance(config, dict) else {}),
        "composition": (config.get("composition") if isinstance(config, dict) else None) or "parallel",
        "output_type": output_type,
        "tools": tools,
        "output_recommendation": public_recommendation(recommend_output(selected_tools, input_modalities)),
    }


def input_modalities_for_nodes(canvas: dict, node_ids: list[str]) -> list[str]:
    by_id = {node["id"]: node for node in canvas.get("nodes", [])}
    modalities = []
    for node_id in node_ids:
        node_type = by_id.get(node_id, {}).get("type", "text")
        if node_type in {"image", "multimodal"}:
            modalities.append(node_type)
        else:
            modalities.append("text")
    return sorted(set(modalities or ["text"]))


def normalize_node(payload: dict) -> dict:
    node_type = payload.get("type", "text")
    if node_type not in NODE_TYPES:
        raise ValueError(f"Unsupported node type: {node_type}")
    node = {
        "id": payload.get("id") or f"node-{uuid.uuid4().hex[:8]}",
        "type": node_type,
        "title": payload.get("title") or default_title(node_type),
        "position": payload.get("position") or {"x": 96, "y": 96},
        "size": payload.get("size") or {"width": 240, "height": 150},
        "status": payload.get("status", "draft"),
        "payload": payload.get("payload") or {},
        "config": payload.get("config") or default_config(node_type),
        "created_at": payload.get("created_at") or utc_now(),
        "active_run_id": payload.get("active_run_id"),
    }
    if node_type == "modify":
        node["config"] = normalize_modify_config(node.get("config", {}))
    if node_type == "operation":
        node["config"] = normalize_operation_config(node.get("config", {}))
    return node


def default_config(node_type: str) -> dict:
    if node_type == "modify":
        return {
            "composition": "parallel",
            "output_type": "text",
            "tools": default_modifier_tools(),
        }
    if node_type == "operation":
        return normalize_operation_config({})
    return {}


def default_title(node_type: str) -> str:
    return {
        "text": "Text Node",
        "conversation": "Conversation",
        "upload": "Upload",
        "image": "Image Node",
        "multimodal": "Text+Image Node",
        "modify": "Modify",
        "operation": "Operation",
    }.get(node_type, "Node")


def empty_canvas(project_id: str) -> dict:
    canvas = {
        "id": project_id,
        "project_id": project_id,
        "version": 2,
        "schema_version": 2,
        "revision": 0,
        "viewport": {"x": 0, "y": 0, "zoom": 1},
        "nodes": [],
        "edges": [],
        "runs": [],
        "pinned_context": [],
        "events": [],
        "scopes": [],
        "conversation_sessions": [],
        "command_proposals": [],
        "executions": [],
        "updated_at": utc_now(),
    }
    ensure_interaction_data(canvas)
    return canvas


def default_canvas(project_id: str) -> dict:
    canvas = empty_canvas(project_id)
    canvas["nodes"] = [
        normalize_node(
            {
                "id": "node-source",
                "type": "text",
                "title": "Research Material",
                "position": {"x": 52, "y": 92},
                "payload": {"text": "Research material about DNA catalysts and hydrogen energy systems."},
                "status": "ready",
            }
        ),
        normalize_node(
            {
                "id": "node-conversation",
                "type": "conversation",
                "title": "Conversation",
                "position": {"x": 52, "y": 292},
                "payload": {"text": "Translate the research question into node content that can be extended."},
                "status": "ready",
            }
        ),
        normalize_node(
            {
                "id": "node-modify",
                "type": "modify",
                "title": "Modify",
                "position": {"x": 510, "y": 194},
                "status": "ready",
            }
        ),
        normalize_node(
            {
                "id": "node-image",
                "type": "image",
                "title": "Semantic Image",
                "position": {"x": 948, "y": 112},
                "payload": {
                    "text": "Image summary awaits user confirmation.",
                    "semantic_status": "generated",
                },
                "status": "generated",
            }
        ),
    ]
    canvas["edges"] = [
        {
            "id": "edge-source-modify",
            "source_node_id": "node-source",
            "target_node_id": "node-modify",
            "source_port": "out",
            "target_port": "in",
            "edge_kind": "data",
            "created_at": utc_now(),
        },
        {
            "id": "edge-conversation-modify",
            "source_node_id": "node-conversation",
            "target_node_id": "node-modify",
            "source_port": "out",
            "target_port": "in",
            "edge_kind": "reference",
            "created_at": utc_now(),
        },
        {
            "id": "edge-modify-image",
            "source_node_id": "node-modify",
            "target_node_id": "node-image",
            "source_port": "out",
            "target_port": "in",
            "edge_kind": "data",
            "created_at": utc_now(),
        },
    ]
    ensure_interaction_data(canvas, seed_demo=True)
    return canvas


def ensure_store_light() -> None:
    ensure_dirs()
    CANVAS_DIR.mkdir(exist_ok=True)
    if not PROJECTS_FILE.exists():
        demo = create_project_record("Speculative Canvas", project_id="demo-canvas")
        PROJECTS_FILE.write_text(json.dumps([demo], ensure_ascii=False, indent=2), encoding="utf-8")
