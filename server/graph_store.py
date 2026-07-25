from __future__ import annotations

import base64
import json
import re
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
    append_activity_message,
    append_message as append_conversation_message,
    assert_expected_revision,
    create_command_proposal as create_command_proposal_record,
    create_conversation as create_conversation_record,
    create_scope as create_scope_record,
    ensure_interaction_data,
    get_scope,
    interaction_payload,
    mark_messages_inactive,
    mark_workflows_stale_for_source_node,
    record_execution_from_run,
    record_graph_event,
    record_workflow_futures,
    resolve_command_proposal as resolve_command_proposal_record,
    set_conversation_scope as set_conversation_scope_record,
    select_workflow_branch as select_workflow_branch_record,
    set_session_guide,
    scope_node_ids,
    scope_projection,
    workflow_for_operation,
)
from server.operation_registry import normalize_operation_config
from server.workflow_registry import default_workflow_definition, get_workflow_definition
from server.guided_scenario import generate_guided_scenarios, render_branch_text
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


def set_conversation_scope(project_id: str, session_id: str, scope_id: str, expected_revision=None) -> dict:
    """Persist a Scope change so conversation and projection cannot drift apart."""

    canvas = read_canvas(project_id)
    assert_expected_revision(canvas, expected_revision)
    session = set_conversation_scope_record(canvas, session_id, scope_id)
    record_graph_event(
        canvas,
        "conversation.scope_changed",
        {"session_id": session_id, "scope_id": scope_id},
    )
    write_canvas(project_id, canvas)
    return session


def add_conversation_message(project_id: str, session_id: str, payload: dict, expected_revision=None) -> dict:
    canvas = read_canvas(project_id)
    assert_expected_revision(canvas, expected_revision)
    message = append_conversation_message(canvas, session_id, payload)
    record_graph_event(canvas, "conversation.message_added", {"session_id": session_id, "message_id": message["id"]})
    write_canvas(project_id, canvas)
    return message


def start_four_futures_workflow(project_id: str, payload: dict, expected_revision=None) -> dict:
    """Materialise the document's low-friction foundation as graph-owned references.

    This action is deterministic: it creates editable source/keyword nodes and a ready
    Guided Scenario operation, but it does not call a model, select tools, or generate images.
    """

    canvas = read_canvas(project_id)
    assert_expected_revision(canvas, expected_revision)
    guided = bool(payload.get("guided"))
    requested_session_id = str(payload.get("session_id") or "")
    requested_id = str(payload.get("definition_id") or "workflow.four-futures-foundation")
    definition = get_workflow_definition(requested_id) or (
        default_workflow_definition() if not payload.get("definition_id") else None
    )
    if not definition or definition["id"] != "workflow.four-futures-foundation":
        raise ValueError("This endpoint only starts the Four Futures foundation workflow.")

    start_mode = str(payload.get("start_mode") or "research").strip().lower()
    if start_mode not in {"research", "design"}:
        raise ValueError("start_mode must be research or design.")
    topic = str(payload.get("topic") or "").strip()
    if not topic:
        raise ValueError("A research topic is required to start the Four Futures workflow.")

    brief = {
        "start_mode": start_mode,
        "topic": topic[:600],
        "research_focus": str(payload.get("research_focus") or "").strip()[:1200],
        "assumptions": workflow_text_list(payload.get("assumptions")),
        "stakeholders": workflow_text_list(payload.get("stakeholders")),
        "tensions": workflow_text_list(payload.get("tensions")),
    }
    keywords = foundation_keywords(brief)
    offset = len(canvas.get("nodes", [])) * 20
    source_node = normalize_node(
        {
            "type": "text",
            "title": "Research brief",
            "position": {"x": 72 + offset, "y": 96 + offset},
            "payload": {
                "text": render_foundation_brief(brief),
                "workflow_role": "research_brief",
                "workflow_brief": brief,
            },
            "status": "ready",
        }
    )
    keyword_node = normalize_node(
        {
            "type": "text",
            "title": "Keywords to confirm",
            "position": {"x": 388 + offset, "y": 96 + offset},
            "payload": {
                "text": render_keyword_scaffold(keywords),
                "workflow_role": "keyword_scaffold",
                "keywords": keywords,
                "keyword_source": "deterministic scaffold from the research brief; no model call",
            },
            "status": "ready",
        }
    )
    operation_node = normalize_node(
        {
            "type": "operation",
            "title": "",
            "position": {"x": 700 + offset, "y": 96 + offset},
            "config": {"definition_ref": {"id": "operation.guided-scenario"}},
            "payload": {"workflow_role": "four_futures_operation"},
            "status": "ready",
        }
    )
    canvas["nodes"].extend([source_node, keyword_node, operation_node])
    source_keyword_edge = {
        "id": f"edge-{uuid.uuid4().hex[:8]}",
        "source_node_id": source_node["id"],
        "target_node_id": keyword_node["id"],
        "source_port": "out",
        "target_port": "in",
        "edge_kind": "reference",
        "created_at": utc_now(),
    }
    source_operation_edge = {
        "id": f"edge-{uuid.uuid4().hex[:8]}",
        "source_node_id": source_node["id"],
        "target_node_id": operation_node["id"],
        "source_port": "out",
        "target_port": "research",
        "edge_kind": "data",
        "created_at": utc_now(),
    }
    keyword_operation_edge = {
        "id": f"edge-{uuid.uuid4().hex[:8]}",
        "source_node_id": keyword_node["id"],
        "target_node_id": operation_node["id"],
        "source_port": "out",
        "target_port": "research",
        "edge_kind": "data",
        "created_at": utc_now(),
    }
    canvas["edges"].extend([source_keyword_edge, source_operation_edge, keyword_operation_edge])
    workflow_id = f"workflow-{uuid.uuid4().hex[:10]}"
    scope = create_scope_record(
        canvas,
        {
            "id": f"scope-{workflow_id}-foundation",
            "label": "Four Futures foundation",
            "mode": "live",
            "selector": {
                "kind": "explicit",
                "node_ids": [source_node["id"], keyword_node["id"], operation_node["id"]],
            },
        },
    )
    progress = [
        {
            "id": f"step-{workflow_id}-frame",
            "workflow_stage_id": "frame",
            "label": "Frame the inquiry",
            "scope_id": scope["id"],
            "status": "active" if guided else "succeeded",
        },
        {
            "id": f"step-{workflow_id}-keywords",
            "workflow_stage_id": "keywords",
            "label": "Confirm keywords",
            "scope_id": scope["id"],
            "status": "pending" if guided else "succeeded",
        },
        {
            "id": f"step-{workflow_id}-futures",
            "workflow_stage_id": "four_futures",
            "label": "Generate four What-if futures",
            "scope_id": scope["id"],
            "status": "pending" if guided else "active",
        },
        {
            "id": f"step-{workflow_id}-choose",
            "workflow_stage_id": "choose_future",
            "label": "Choose one future",
            "scope_id": scope["id"],
            "status": "pending",
        },
        {
            "id": f"step-{workflow_id}-discussion",
            "workflow_stage_id": "discussion",
            "label": "Discuss the chosen future",
            "scope_id": scope["id"],
            "status": "pending",
        },
    ]
    session = next(
        (item for item in canvas.get("conversation_sessions", []) if item.get("id") == requested_session_id),
        None,
    )
    if requested_session_id and not session:
        raise KeyError(f"Conversation session not found: {requested_session_id}")
    if session:
        session.update(
            {
                "title": "Four Futures research thread",
                "control_policy": "confirm",
                "workflow_instance_id": workflow_id,
                "active_scope_id": scope["id"],
                "progress": progress,
                "updated_at": utc_now(),
            }
        )
    else:
        session = create_conversation_record(
            canvas,
            {
                "title": "Four Futures research thread",
                "control_policy": "confirm",
                "workflow_instance_id": workflow_id,
                "active_scope_id": scope["id"],
                "progress": progress,
            },
        )
    workflow = {
        "id": workflow_id,
        "definition_ref": {"id": definition["id"], "version": definition["version"]},
        "label": definition["label"],
        "status": "active",
        "stage": "frame" if guided else "four_futures",
        "session_id": session["id"],
        "foundation_scope_id": scope["id"],
        "comparison_scope_id": "",
        "source_node_ids": [source_node["id"], keyword_node["id"]],
        "keyword_node_id": keyword_node["id"],
        "operation_node_id": operation_node["id"],
        "input_edge_ids": [source_operation_edge["id"], keyword_operation_edge["id"]],
        "branch_node_ids": [],
        "branch_scope_ids": {},
        "selected_branch_node_id": "",
        "discussion_node_id": "",
        "input_revision": int(canvas.get("revision") or 0) + 1,
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }
    canvas.setdefault("workflow_instances", []).append(workflow)
    set_session_guide(
        session,
        "frame_focus" if guided else "four_futures",
        workflow_instance_id=workflow_id,
        pending_field="research_focus" if guided else "",
    )
    append_conversation_message(
        canvas,
        session["id"],
        {
            "role": "system",
            "kind": "guide",
            "scope_id": scope["id"],
            "related_node_ids": [source_node["id"], keyword_node["id"], operation_node["id"]],
            "body": "This conversation writes to the canonical research nodes. You can also edit those nodes directly; both routes update the same workflow record.",
        },
    )
    append_conversation_message(
        canvas,
        session["id"],
        {
            "role": "assistant",
            "kind": "guide",
            "scope_id": scope["id"],
            "related_node_ids": [source_node["id"], keyword_node["id"], operation_node["id"]],
            "body": (
                "What should this inquiry focus on? You can write a short answer, skip it, or edit the Research brief node directly."
                if guided
                else "The research brief and keyword scaffold are ready. Review either node if needed, then run Guided Scenario to compare four What-if futures."
            ),
        },
    )
    record_graph_event(
        canvas,
        "workflow.four_futures.started",
        {
            "workflow_id": workflow_id,
            "session_id": session["id"],
            "scope_id": scope["id"],
            "source_node_ids": workflow["source_node_ids"],
            "operation_node_id": operation_node["id"],
        },
    )
    write_canvas(project_id, canvas)
    return {"workflow": workflow, "conversation": session, "scope": scope, "nodes": [source_node, keyword_node, operation_node]}


def select_four_futures_branch(project_id: str, workflow_id: str, payload: dict, expected_revision=None) -> dict:
    canvas = read_canvas(project_id)
    assert_expected_revision(canvas, expected_revision)
    branch_node_id = str(payload.get("branch_node_id") or "")
    result = select_workflow_branch_record(canvas, workflow_id, branch_node_id)
    workflow = next((item for item in canvas.get("workflow_instances", []) if item.get("id") == workflow_id), None)
    discussion_node = _ensure_discussion_tool_node(canvas, workflow, branch_node_id)
    _record_graph_activity(
        canvas,
        "Selected a What-if branch and prepared its discussion tools.",
        requested_session_id=str(payload.get("session_id") or ""),
        workflow=workflow,
        related_node_ids=[branch_node_id, discussion_node["id"]],
        activity_type="workflow.branch_selected",
    )
    record_graph_event(
        canvas,
        "workflow.four_futures.branch_selected",
        {
            "workflow_id": workflow_id,
            "branch_node_id": branch_node_id,
            "discussion_node_id": discussion_node["id"],
            "scope_id": result["scope_id"],
        },
    )
    write_canvas(project_id, canvas)
    return {**result, "discussion_node": discussion_node}


def _ensure_discussion_tool_node(canvas: dict, workflow: dict | None, branch_node_id: str) -> dict:
    """Attach one empty, registry-backed tool node to a chosen future Scope.

    The workflow owns only the reference and its selection rule. Tool theory, card
    metadata, constraints, and later executors still come from the package registry.
    """

    if not workflow:
        raise KeyError("Workflow not found while preparing the discussion scope.")
    branch = next((node for node in canvas.get("nodes", []) if node.get("id") == branch_node_id), None)
    if not branch:
        raise KeyError("Selected What-if branch no longer exists.")
    scope_id = str(workflow.get("branch_scope_ids", {}).get(branch_node_id) or "")
    scope = get_scope(canvas, scope_id)
    if not scope:
        raise ValueError("Selected What-if branch has no discussion Scope.")

    definition = get_workflow_definition((workflow.get("definition_ref") or {}).get("id")) or {}
    policy = definition.get("discussion_tool_policy") if isinstance(definition.get("discussion_tool_policy"), dict) else {}
    scenario = branch.get("payload", {}).get("scenario_branch", {})
    strategy_id = str(scenario.get("strategy") or "")
    recommended_tool_ids = list((policy.get("recommended_by_branch") or {}).get(strategy_id, []))
    selection_policy = {
        "minimum_selected": int(policy.get("minimum_selected") or 0),
        "required_for": "workflow.discussion",
        "recommended_tool_ids": recommended_tool_ids,
    }

    existing_id = str(workflow.get("discussion_node_id") or "")
    discussion_node = next((node for node in canvas.get("nodes", []) if node.get("id") == existing_id), None)
    if not discussion_node:
        discussion_node = normalize_node(
            {
                "type": "modify",
                "title": "Discussion tools",
                "position": {
                    "x": int(branch.get("position", {}).get("x") or 0) + 320,
                    "y": int(branch.get("position", {}).get("y") or 0),
                },
                "status": "ready",
                "config": {
                    "output_type": "text",
                    "tools": [
                        {"id": tool["id"], "selected": False}
                        for tool in default_modifier_tools()
                    ],
                    "selection_policy": selection_policy,
                    "workflow_context": {
                        "workflow_id": workflow["id"],
                        "branch_node_id": branch_node_id,
                    },
                },
            }
        )
        canvas["nodes"].append(discussion_node)
        canvas["edges"].append(
            {
                "id": f"edge-{uuid.uuid4().hex[:8]}",
                "source_node_id": branch_node_id,
                "target_node_id": discussion_node["id"],
                "source_port": "out",
                "target_port": "in",
                "edge_kind": "data",
                "created_at": utc_now(),
            }
        )
    else:
        discussion_node.setdefault("config", {})["selection_policy"] = selection_policy
        discussion_node.setdefault("config", {})["workflow_context"] = {
            "workflow_id": workflow["id"],
            "branch_node_id": branch_node_id,
        }

    if not any(
        edge.get("source_node_id") == branch_node_id
        and edge.get("target_node_id") == discussion_node["id"]
        and edge.get("edge_kind") == "data"
        for edge in canvas.get("edges", [])
    ):
        canvas["edges"].append(
            {
                "id": f"edge-{uuid.uuid4().hex[:8]}",
                "source_node_id": branch_node_id,
                "target_node_id": discussion_node["id"],
                "source_port": "out",
                "target_port": "in",
                "edge_kind": "data",
                "created_at": utc_now(),
            }
        )

    if scope.get("mode") == "snapshot":
        member_ids = scope.setdefault("snapshot_node_ids", [])
        if discussion_node["id"] not in member_ids:
            member_ids.append(discussion_node["id"])
    workflow["discussion_node_id"] = discussion_node["id"]
    workflow["updated_at"] = utc_now()
    refresh_runtime_config(canvas)
    return discussion_node


GUIDE_FIELD_SEQUENCE = {
    "research_focus": ("frame_assumptions", "assumptions", "What assumptions currently shape this topic? Add one per line or sentence; you can also skip."),
    "assumptions": ("frame_stakeholders", "stakeholders", "Who is affected, involved, or able to act? Add stakeholders or skip."),
    "stakeholders": ("frame_tensions", "tensions", "What is the central tension or trade-off? Add one or more, or skip."),
}


def advance_conversation_guide(project_id: str, session_id: str, payload: dict, expected_revision=None) -> dict:
    """Advance the conversation-first foundation flow without duplicating graph data.

    The assistant's deterministic questions only change the Research brief and
    Keywords nodes that the workflow owns.  It intentionally knows nothing about
    tool packages, model selection, or image generation.
    """

    action = str(payload.get("action") or "answer")
    if action == "begin":
        canvas = read_canvas(project_id)
        session = next((item for item in canvas.get("conversation_sessions", []) if item.get("id") == session_id), None)
        if not session:
            raise KeyError(f"Conversation session not found: {session_id}")
        guide = session.get("guide") if isinstance(session.get("guide"), dict) else {}
        return start_four_futures_workflow(
            project_id,
            {
                "definition_id": "workflow.four-futures-foundation",
                "guided": True,
                "session_id": session_id,
                "start_mode": guide.get("start_mode") or "research",
                "topic": str(payload.get("body") or "").strip(),
            },
            expected_revision=expected_revision,
        )

    canvas = read_canvas(project_id)
    assert_expected_revision(canvas, expected_revision)
    session = next((item for item in canvas.get("conversation_sessions", []) if item.get("id") == session_id), None)
    if not session:
        raise KeyError(f"Conversation session not found: {session_id}")
    guide = session.get("guide") if isinstance(session.get("guide"), dict) else {}

    if action == "set_start_mode":
        if guide.get("stage_id") != "start":
            raise ValueError("Starting mode can only be changed before the inquiry begins.")
        start_mode = str(payload.get("start_mode") or "").strip().lower()
        if start_mode not in {"research", "design"}:
            raise ValueError("start_mode must be research or design.")
        guide["start_mode"] = start_mode
        session["guide"] = guide
        append_conversation_message(
            canvas,
            session_id,
            {
                "role": "assistant",
                "kind": "guide",
                "scope_id": session.get("active_scope_id", "scope-global"),
                "body": "Start from a real research inquiry." if start_mode == "research" else "Start from a design proposition.",
            },
        )
        record_graph_event(canvas, "conversation.guide.start_mode_set", {"session_id": session_id, "start_mode": start_mode})
        write_canvas(project_id, canvas)
        return {"conversation": session}

    workflow_id = str(guide.get("workflow_instance_id") or session.get("workflow_instance_id") or "")
    workflow = next((item for item in canvas.get("workflow_instances", []) if item.get("id") == workflow_id), None)
    if not workflow:
        raise ValueError("Begin with a topic before answering the guided questions.")
    if action not in {"answer", "skip", "confirm_keywords"}:
        raise ValueError("Unsupported guided conversation action.")
    if workflow.get("status") == "stale":
        raise ValueError("This workflow is stale. Reframe the inquiry before continuing.")

    if action == "confirm_keywords":
        if guide.get("stage_id") != "keywords":
            raise ValueError("Keywords can only be confirmed after the inquiry frame is complete.")
        workflow.update({"status": "active", "stage": "four_futures", "updated_at": utc_now()})
        _set_workflow_progress(session, "keywords", "succeeded")
        _set_workflow_progress(session, "four_futures", "active")
        set_session_guide(session, "four_futures", workflow_instance_id=workflow_id, pending_field="")
        append_conversation_message(
            canvas,
            session_id,
            {
                "role": "assistant",
                "kind": "guide",
                "scope_id": workflow.get("foundation_scope_id") or session.get("active_scope_id", "scope-global"),
                "related_node_ids": [*workflow.get("source_node_ids", []), workflow.get("operation_node_id", "")],
                "body": "Keywords are confirmed. The four What-if stage is ready; run the Guided Scenario node when you want to generate the four directions.",
            },
        )
        record_graph_event(canvas, "conversation.guide.keywords_confirmed", {"session_id": session_id, "workflow_id": workflow_id})
        write_canvas(project_id, canvas)
        return {"workflow": workflow, "conversation": session}

    field = str(guide.get("pending_field") or "")
    if field not in {"research_focus", "assumptions", "stakeholders", "tensions"}:
        raise ValueError("The guided frame is not waiting for an answer.")
    body = str(payload.get("body") or "").strip()
    if action == "answer" and not body:
        raise ValueError("Write an answer or use Skip for this step.")

    source_node = next((item for item in canvas.get("nodes", []) if item.get("id") == workflow.get("source_node_ids", [""])[0]), None)
    keyword_node = next((item for item in canvas.get("nodes", []) if item.get("id") == workflow.get("keyword_node_id")), None)
    if not source_node or not keyword_node:
        raise ValueError("The canonical foundation nodes are missing; this workflow cannot continue.")
    brief = source_node.get("payload", {}).get("workflow_brief")
    if not isinstance(brief, dict):
        raise ValueError("The research brief was changed outside the guided flow. Continue by editing nodes directly and restart this workflow when ready.")
    if action == "answer":
        if field in {"assumptions", "stakeholders", "tensions"}:
            brief[field] = workflow_text_list(body)
        else:
            brief[field] = body[:1200]
        append_conversation_message(
            canvas,
            session_id,
            {
                "role": "user",
                "kind": "guide",
                "scope_id": workflow.get("foundation_scope_id") or session.get("active_scope_id", "scope-global"),
                "related_node_ids": [source_node["id"]],
                "body": body,
            },
        )
    else:
        brief[field] = [] if field in {"assumptions", "stakeholders", "tensions"} else ""
        append_activity_message(
            canvas,
            session_id,
            f"Skipped {field.replace('_', ' ')} in the guided frame.",
            scope_id=workflow.get("foundation_scope_id") or session.get("active_scope_id", "scope-global"),
            related_node_ids=[source_node["id"]],
            activity_type="conversation.guide.skipped",
            workflow_id=workflow_id,
            stage_id=str(guide.get("stage_id") or "frame"),
        )

    source_node.setdefault("payload", {})["workflow_brief"] = brief
    source_node["payload"]["text"] = render_foundation_brief(brief)
    keywords = foundation_keywords(brief)
    keyword_node.setdefault("payload", {})["keywords"] = keywords
    keyword_node["payload"]["text"] = render_keyword_scaffold(keywords)
    next_step = GUIDE_FIELD_SEQUENCE.get(field)
    scope_id = workflow.get("foundation_scope_id") or session.get("active_scope_id", "scope-global")
    if next_step:
        next_stage, next_field, prompt = next_step
        set_session_guide(session, next_stage, workflow_instance_id=workflow_id, pending_field=next_field)
        append_conversation_message(
            canvas,
            session_id,
            {
                "role": "assistant",
                "kind": "guide",
                "scope_id": scope_id,
                "related_node_ids": [source_node["id"], keyword_node["id"]],
                "body": prompt,
            },
        )
    else:
        workflow.update({"stage": "keywords", "status": "active", "updated_at": utc_now()})
        _set_workflow_progress(session, "frame", "succeeded")
        _set_workflow_progress(session, "keywords", "active")
        set_session_guide(session, "keywords", workflow_instance_id=workflow_id, pending_field="")
        append_conversation_message(
            canvas,
            session_id,
            {
                "role": "assistant",
                "kind": "guide",
                "scope_id": scope_id,
                "related_node_ids": [source_node["id"], keyword_node["id"]],
                "body": "The inquiry frame is complete. Review the editable keyword node, then confirm the keywords here to unlock the four What-if stage.",
            },
        )
    record_graph_event(
        canvas,
        "conversation.guide.advanced",
        {"session_id": session_id, "workflow_id": workflow_id, "field": field, "action": action},
    )
    write_canvas(project_id, canvas)
    return {"workflow": workflow, "conversation": session, "source_node": source_node, "keyword_node": keyword_node}


def _set_workflow_progress(session: dict, stage_id: str, status: str) -> None:
    for step in session.get("progress", []):
        if step.get("workflow_stage_id") == stage_id:
            step["status"] = status
            return


def workflow_text_list(value) -> list[str]:
    if isinstance(value, str):
        parts = value.replace("；", ";").replace("，", ",").replace("\n", ",").split(",")
    elif isinstance(value, list):
        parts = value
    else:
        parts = []
    result = []
    for item in parts:
        text = str(item or "").strip()
        if text and text not in result:
            result.append(text[:180])
    return result[:8]


def foundation_keywords(brief: dict) -> list[str]:
    candidates = [brief.get("topic", ""), brief.get("research_focus", ""), *brief.get("assumptions", []), *brief.get("stakeholders", []), *brief.get("tensions", [])]
    keywords = []
    for item in candidates:
        text = str(item or "").strip()
        if text and text not in keywords:
            keywords.append(text[:72])
    return keywords[:8]


def direct_brief_keywords(text: str) -> list[str]:
    """Derive an inspectable keyword scaffold from a directly edited brief.

    A free-form node edit no longer has the guide's structured fields.  Keeping the
    extraction deliberately shallow makes that loss explicit while ensuring the
    Keyword node is still derived from the canonical Brief rather than an older copy.
    """

    candidates = []
    for raw_part in re.split(r"[\n;；]+", str(text or "")):
        part = raw_part.strip().lstrip("-• ").strip()
        if not part:
            continue
        if ":" in part or "：" in part:
            part = re.split(r"[:：]", part, maxsplit=1)[1].strip()
        if part and part not in candidates:
            candidates.append(part[:72])
    return candidates[:8]


def synchronize_keyword_scaffold_from_brief(canvas: dict, workflow: dict, source_node: dict, patch: dict) -> dict | None:
    """Keep the editable keyword node derived from the current canonical Brief."""

    keyword_node = next(
        (item for item in canvas.get("nodes", []) if item.get("id") == workflow.get("keyword_node_id")),
        None,
    )
    payload_patch = patch.get("payload") if isinstance(patch.get("payload"), dict) else {}
    if not keyword_node or not ({"text", "workflow_brief"} & set(payload_patch)):
        return None

    source_payload = source_node.setdefault("payload", {})
    structured_brief = source_payload.get("workflow_brief")
    if "workflow_brief" in payload_patch and isinstance(structured_brief, dict):
        source_payload["text"] = render_foundation_brief(structured_brief)
        source_payload.pop("workflow_brief_status", None)
        keywords = foundation_keywords(structured_brief)
        source_kind = "deterministic scaffold from the structured research brief; no model call"
    else:
        # `payload.text` is now the source of truth.  Do not leave an older guided
        # object beside it where it could later be mistaken for current research.
        source_payload.pop("workflow_brief", None)
        source_payload["workflow_brief_status"] = "superseded_by_direct_text"
        keywords = direct_brief_keywords(source_payload.get("text", ""))
        source_kind = "deterministic scaffold from the directly edited research brief; no model call"

    keyword_payload = keyword_node.setdefault("payload", {})
    keyword_payload["keywords"] = keywords
    keyword_payload["text"] = render_keyword_scaffold(keywords)
    keyword_payload["keyword_source"] = source_kind
    keyword_node["status"] = "ready"
    return keyword_node


def render_foundation_brief(brief: dict) -> str:
    start_mode = str(brief.get("start_mode") or "research")
    lines = [
        f"Starting point: {'Real research / researcher-led' if start_mode == 'research' else 'Design proposition / designer-led'}",
        f"Topic: {str(brief.get('topic') or '').strip()}",
    ]
    if brief.get("research_focus"):
        lines.append(f"Research focus: {brief['research_focus']}")
    for label, values in (("Default assumptions", brief.get("assumptions", [])), ("Stakeholders", brief.get("stakeholders", [])), ("Core tensions", brief.get("tensions", []))):
        if values:
            lines.append(f"{label}: " + "; ".join(values))
    return "\n".join(lines)


def render_keyword_scaffold(keywords: list[str]) -> str:
    if not keywords:
        return "Keywords to confirm\n\nAdd the concepts, trends, and tensions that should seed the four futures."
    return "Keywords to confirm\n\n" + "\n".join(f"- {keyword}" for keyword in keywords)


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


def _workflow_for_node_id(canvas: dict, node_id: str) -> dict | None:
    return next(
        (
            workflow
            for workflow in canvas.get("workflow_instances", [])
            if node_id in {
                *workflow.get("source_node_ids", []),
                workflow.get("operation_node_id", ""),
                workflow.get("discussion_node_id", ""),
                *workflow.get("branch_node_ids", []),
            }
        ),
        None,
    )


def _activity_session(canvas: dict, *, requested_session_id: str = "", workflow: dict | None = None) -> dict | None:
    if requested_session_id:
        requested = next(
            (item for item in canvas.get("conversation_sessions", []) if item.get("id") == requested_session_id),
            None,
        )
        if requested:
            return requested
    if workflow and workflow.get("session_id"):
        linked = next(
            (item for item in canvas.get("conversation_sessions", []) if item.get("id") == workflow.get("session_id")),
            None,
        )
        if linked:
            return linked
    active_sessions = [item for item in canvas.get("conversation_sessions", []) if item.get("status") == "active"]
    # A mutation without an explicit conversation owner must not silently appear in
    # an arbitrary thread once a canvas has multiple active discussions.
    return active_sessions[0] if len(active_sessions) == 1 else None


def _record_graph_activity(
    canvas: dict,
    body: str,
    *,
    requested_session_id: str = "",
    workflow: dict | None = None,
    related_node_ids: list[str] | None = None,
    activity_type: str = "graph.changed",
) -> None:
    session = _activity_session(canvas, requested_session_id=requested_session_id, workflow=workflow)
    if not session:
        return
    session_scope_id = str(session.get("active_scope_id") or "")
    scope_id = session_scope_id if get_scope(canvas, session_scope_id) else (workflow or {}).get("foundation_scope_id") or "scope-global"
    append_activity_message(
        canvas,
        session["id"],
        body,
        scope_id=scope_id,
        related_node_ids=related_node_ids or [],
        activity_type=activity_type,
        workflow_id=(workflow or {}).get("id", ""),
        stage_id=(workflow or {}).get("stage", ""),
    )


def _invalidate_workflow(
    canvas: dict,
    workflow: dict,
    reason: str,
    *,
    related_node_ids: list[str] | None = None,
    requested_session_id: str = "",
) -> None:
    """Make an invalid graph dependency visible instead of retaining a branch silently."""

    branch_ids = set(workflow.get("branch_node_ids", []))
    discussion_node_id = str(workflow.get("discussion_node_id") or "")
    mark_messages_inactive(
        canvas,
        related_node_ids=list(branch_ids),
        state="superseded",
        reason="This speculative branch no longer participates in the current workflow.",
        workflow_id=str(workflow.get("id") or ""),
    )
    workflow.update(
        {
            "status": "stale",
            "stage": "stale",
            "selected_branch_node_id": "",
            "discussion_node_id": "",
            "updated_at": utc_now(),
        }
    )
    for node in canvas.get("nodes", []):
        if node.get("id") in branch_ids or node.get("id") == discussion_node_id:
            node["status"] = "stale"
    session = _activity_session(canvas, requested_session_id=requested_session_id, workflow=workflow)
    if session:
        session["active_scope_id"] = "scope-global"
        _set_workflow_progress(session, "four_futures", "stale")
        _set_workflow_progress(session, "choose_future", "pending")
        _set_workflow_progress(session, "discussion", "pending")
        set_session_guide(session, "stale", workflow_instance_id=workflow["id"], pending_field="")
    _record_graph_activity(
        canvas,
        reason,
        requested_session_id=requested_session_id,
        workflow=workflow,
        related_node_ids=related_node_ids,
        activity_type="workflow.invalidated",
    )


def _invalidate_workflows_for_edge(
    canvas: dict,
    edge: dict,
    *,
    reason: str,
    requested_session_id: str = "",
) -> list[str]:
    if edge.get("edge_kind") != "data":
        return []
    invalidated = []
    for workflow in canvas.get("workflow_instances", []):
        if edge.get("target_node_id") != workflow.get("operation_node_id"):
            continue
        _invalidate_workflow(
            canvas,
            workflow,
            reason,
            related_node_ids=[edge.get("source_node_id", ""), workflow.get("operation_node_id", "")],
            requested_session_id=requested_session_id,
        )
        invalidated.append(workflow["id"])
    return invalidated


def operation_input_port_map(operation: dict) -> dict[str, dict]:
    definition = operation.get("config", {}).get("definition", {})
    return {
        str(port.get("id")): port
        for port in definition.get("input_ports", [])
        if isinstance(port, dict) and port.get("id")
    }


def validate_operation_data_edge(
    canvas: dict,
    source_node_id: str,
    target_node: dict,
    target_port: str,
) -> None:
    """Validate a direct graph edge against the target operation's manifest port."""

    ports = operation_input_port_map(target_node)
    if target_port not in ports:
        raise ValueError(f"{target_node.get('title') or 'Operation'} does not expose a '{target_port}' data input port.")
    port = ports[target_port]
    source_modalities = set(input_modalities_for_nodes(canvas, [source_node_id]))
    accepted_modalities = set(port.get("accepted_modalities") or ["text"])
    if not source_modalities.issubset(accepted_modalities):
        raise ValueError(
            f"The '{target_port}' input accepts {', '.join(sorted(accepted_modalities))}, not {', '.join(sorted(source_modalities))}."
        )
    existing = [
        edge
        for edge in canvas.get("edges", [])
        if edge.get("target_node_id") == target_node.get("id")
        and edge.get("target_port") == target_port
        and edge.get("edge_kind") == "data"
    ]
    if port.get("cardinality") == "one" and existing:
        raise ValueError(f"The '{target_port}' input accepts only one direct data edge.")
    if any(edge.get("source_node_id") == source_node_id for edge in existing):
        raise ValueError("That direct data edge already exists.")


def validated_operation_input_edges(canvas: dict, operation: dict) -> list[dict]:
    """Return input edges only after enforcing the manifest's port contract."""

    ports = operation_input_port_map(operation)
    input_edges = ordered_data_input_edges(canvas, operation.get("id", ""))
    seen_by_port: dict[str, int] = {}
    for edge in input_edges:
        target_port = str(edge.get("target_port") or "")
        if target_port not in ports:
            raise ValueError(f"{operation.get('title') or 'Operation'} has a data edge on an undeclared '{target_port}' port.")
        port = ports[target_port]
        source_modalities = set(input_modalities_for_nodes(canvas, [edge.get("source_node_id", "")]))
        accepted_modalities = set(port.get("accepted_modalities") or ["text"])
        if not source_modalities.issubset(accepted_modalities):
            raise ValueError(f"Input on '{target_port}' has an unsupported modality.")
        seen_by_port[target_port] = seen_by_port.get(target_port, 0) + 1
        if port.get("cardinality") == "one" and seen_by_port[target_port] > 1:
            raise ValueError(f"The '{target_port}' input accepts only one direct data edge.")
    missing_required = [port_id for port_id, port in ports.items() if port.get("required") and not seen_by_port.get(port_id)]
    if missing_required:
        raise ValueError(f"{operation.get('title') or 'Operation'} is missing required input: {', '.join(missing_required)}.")
    return input_edges


def add_node(project_id: str, payload: dict, expected_revision=None, session_id: str = "") -> dict:
    canvas = read_canvas(project_id)
    assert_expected_revision(canvas, expected_revision)
    node = normalize_node(payload)
    canvas["nodes"].append(node)
    refresh_runtime_config(canvas)
    _record_graph_activity(
        canvas,
        f"Added {node.get('title') or node.get('type', 'node')}.",
        requested_session_id=session_id,
        related_node_ids=[node["id"]],
        activity_type="node.created",
    )
    record_graph_event(canvas, "node.created", {"node_id": node["id"], "node_type": node["type"]})
    write_canvas(project_id, canvas)
    return node


def update_node(project_id: str, node_id: str, patch: dict, expected_revision=None, session_id: str = "") -> dict:
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
            workflow = _workflow_for_node_id(canvas, node_id)
            stale_workflows = []
            synchronized_keyword_node = None
            if "payload" in patch and workflow and node_id in workflow.get("source_node_ids", []):
                if node_id != workflow.get("keyword_node_id"):
                    synchronized_keyword_node = synchronize_keyword_scaffold_from_brief(canvas, workflow, node, patch)
                # A direct node edit is a valid route, but it invalidates any
                # downstream comparison rather than leaving it deceptively live.
                _invalidate_workflow(
                    canvas,
                    workflow,
                    (
                        "The canonical Research Brief was edited directly, and its keyword scaffold was synchronized. "
                        "Existing What-if branches are now stale; regenerate before selecting a future."
                        if synchronized_keyword_node
                        else "The canonical workflow input was edited directly. Existing What-if branches are now stale; regenerate before selecting a future."
                    ),
                    related_node_ids=[
                        node_id,
                        *([synchronized_keyword_node["id"]] if synchronized_keyword_node else []),
                        *workflow.get("branch_node_ids", []),
                    ],
                    requested_session_id=session_id,
                )
                stale_workflows = [workflow]
            elif "payload" in patch and workflow and node_id in workflow.get("branch_node_ids", []):
                _invalidate_workflow(
                    canvas,
                    workflow,
                    "A What-if branch was edited directly. Re-run the comparison before using a selected branch.",
                    related_node_ids=[node_id],
                    requested_session_id=session_id,
                )
                stale_workflows = [workflow]
            elif "payload" in patch:
                stale_workflows = mark_workflows_stale_for_source_node(canvas, node_id)
                for stale_workflow in stale_workflows:
                    _record_graph_activity(
                        canvas,
                        "A workflow input changed. Its generated futures are now stale.",
                        requested_session_id=session_id,
                        workflow=stale_workflow,
                        related_node_ids=[node_id, *stale_workflow.get("branch_node_ids", [])],
                        activity_type="workflow.invalidated",
                    )
            # An invalidation already writes the meaningful conversational record for
            # a semantic edit. Avoid following it with a generic duplicate update.
            if set(patch) - {"position", "size"} and not stale_workflows:
                config_patch = patch.get("config") if isinstance(patch.get("config"), dict) else {}
                tools_changed = "tools" in config_patch
                selected_count = len(
                    [tool for tool in node.get("config", {}).get("tools", []) if tool.get("selected")]
                )
                _record_graph_activity(
                    canvas,
                    (
                        f"Updated discussion tools: {selected_count} method(s) selected."
                        if tools_changed
                        else f"Updated {node.get('title') or node.get('type', 'node')}."
                    ),
                    requested_session_id=session_id,
                    workflow=workflow,
                    related_node_ids=[node_id],
                    activity_type="workflow.discussion_tools_changed" if tools_changed else "node.updated",
                )
            record_graph_event(
                canvas,
                "node.updated",
                {
                    "node_id": node_id,
                    "fields": sorted(patch.keys()),
                    "stale_workflow_ids": [workflow["id"] for workflow in stale_workflows],
                },
            )
            write_canvas(project_id, canvas)
            return node
    raise KeyError(f"Node not found: {node_id}")


def delete_node(project_id: str, node_id: str, expected_revision=None, session_id: str = "") -> dict:
    canvas = read_canvas(project_id)
    assert_expected_revision(canvas, expected_revision)
    node = next((item for item in canvas.get("nodes", []) if item.get("id") == node_id), None)
    if not node:
        raise KeyError(f"Node not found: {node_id}")

    # Preserve the conversational trace before the graph item disappears. This is
    # intentionally a status change to history, not a deletion of history.
    mark_messages_inactive(
        canvas,
        related_node_ids=[node_id],
        state="removed",
        reason="This part of the speculation was removed directly from the current workflow.",
    )

    affected_workflows = [
        workflow
        for workflow in canvas.get("workflow_instances", [])
        if node_id in {
            *workflow.get("source_node_ids", []),
            workflow.get("operation_node_id", ""),
            workflow.get("discussion_node_id", ""),
            *workflow.get("branch_node_ids", []),
        }
    ]

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
    for workflow in affected_workflows:
        _invalidate_workflow(
            canvas,
            workflow,
            f"Deleted {node.get('title') or node.get('type', 'node')}. The connected Four Futures workflow is now stale and cannot retain a selected branch.",
            related_node_ids=[*workflow.get("source_node_ids", []), *workflow.get("branch_node_ids", [])],
            requested_session_id=session_id,
        )
    if not affected_workflows:
        _record_graph_activity(
            canvas,
            f"Deleted {node.get('title') or node.get('type', 'node')}.",
            requested_session_id=session_id,
            activity_type="node.deleted",
        )
    record_graph_event(canvas, "node.deleted", {"node_id": node_id, "preserved_run_ids": removed_run_ids})
    write_canvas(project_id, canvas)
    return {
        "node": node,
        "removed_edges": removed_edge_ids,
        "removed_runs": removed_run_ids,
    }


def add_edge(project_id: str, payload: dict, expected_revision=None, session_id: str = "") -> dict:
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
    target_node = next((node for node in canvas.get("nodes", []) if node.get("id") == target_node_id), None)
    target_port = str(payload.get("target_port", "in"))
    if edge_kind == "data" and target_node and target_node.get("type") == "operation":
        validate_operation_data_edge(canvas, source_node_id, target_node, target_port)
    edge = {
        "id": payload.get("id") or f"edge-{uuid.uuid4().hex[:8]}",
        "source_node_id": source_node_id,
        "target_node_id": target_node_id,
        "source_port": payload.get("source_port", "out"),
        "target_port": target_port,
        "edge_kind": edge_kind,
        "created_at": utc_now(),
    }
    canvas["edges"].append(edge)
    refresh_runtime_config(canvas)
    invalidated = _invalidate_workflows_for_edge(
        canvas,
        edge,
        reason="A direct data edge changed the workflow inputs. Reconfirm the canonical inputs before generating futures.",
        requested_session_id=session_id,
    )
    if not invalidated:
        _record_graph_activity(
            canvas,
            "Connected two nodes.",
            requested_session_id=session_id,
            workflow=_workflow_for_node_id(canvas, source_node_id) or _workflow_for_node_id(canvas, target_node_id),
            related_node_ids=[source_node_id, target_node_id],
            activity_type="edge.created",
        )
    record_graph_event(canvas, "edge.created", {"edge_id": edge["id"], "edge_kind": edge_kind})
    write_canvas(project_id, canvas)
    return edge


def delete_edge(project_id: str, edge_id: str, expected_revision=None, session_id: str = "") -> dict:
    canvas = read_canvas(project_id)
    assert_expected_revision(canvas, expected_revision)
    edge = next((item for item in canvas.get("edges", []) if item.get("id") == edge_id), None)
    if not edge:
        raise KeyError(f"Edge not found: {edge_id}")
    canvas["edges"] = [item for item in canvas.get("edges", []) if item.get("id") != edge_id]
    refresh_runtime_config(canvas)
    invalidated = _invalidate_workflows_for_edge(
        canvas,
        edge,
        reason="A workflow input edge was removed. The four-futures comparison is stale until its inputs are restored and regenerated.",
        requested_session_id=session_id,
    )
    if not invalidated:
        _record_graph_activity(
            canvas,
            "Removed a connection between two nodes.",
            requested_session_id=session_id,
            workflow=_workflow_for_node_id(canvas, edge.get("source_node_id", "")) or _workflow_for_node_id(canvas, edge.get("target_node_id", "")),
            related_node_ids=[edge.get("source_node_id", ""), edge.get("target_node_id", "")],
            activity_type="edge.deleted",
        )
    record_graph_event(canvas, "edge.deleted", {"edge_id": edge_id})
    write_canvas(project_id, canvas)
    return {"edge": edge}


def run_modify(project_id: str, node_id: str, api_key: str | None = None, expected_revision=None, session_id: str = "") -> dict:
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
    minimum_selected_tools = int((modify.get("config", {}).get("selection_policy") or {}).get("minimum_selected") or 0)
    if len(selected_tools) < minimum_selected_tools:
        raise ValueError(
            f"Select at least {minimum_selected_tools} discussion tool before running this node."
        )
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
    _record_graph_activity(
        canvas,
        f"Ran {modify.get('title') or 'Modify'} and added a new output node.",
        requested_session_id=session_id,
        related_node_ids=[node_id, output_node["id"]],
        activity_type="execution.completed",
    )
    record_graph_event(canvas, "execution.completed", {"execution_id": execution["id"], "run_id": run["id"], "status": run["status"]})
    write_canvas(project_id, canvas)
    return {"run": run, "execution": execution, "output_node": output_node, "edge": edge}


def run_operation(project_id: str, node_id: str, api_key: str | None = None, expected_revision=None, session_id: str = "") -> dict:
    """Run a manifest-defined operation without reusing Modify's generic executor."""

    canvas = read_canvas(project_id)
    assert_expected_revision(canvas, expected_revision)
    operation = next((node for node in canvas["nodes"] if node["id"] == node_id), None)
    if not operation:
        raise KeyError(f"Operation node not found: {node_id}")
    if operation.get("type") != "operation":
        raise ValueError("Only Operation nodes can be run through this operation executor.")

    definition = operation.get("config", {}).get("definition", {})
    executor = definition.get("execution", {}).get("executor")
    if executor != "guided_scenario":
        raise ValueError("This operation definition does not yet have a runnable executor.")

    input_edges = validated_operation_input_edges(canvas, operation)
    upstream_ids = [edge["source_node_id"] for edge in input_edges]
    workflow = workflow_for_operation(canvas, node_id)
    if workflow:
        if workflow.get("stage") not in {"four_futures", "stale"}:
            raise ValueError("Complete and confirm the inquiry frame before generating the four What-if futures.")
        expected_sources = workflow.get("source_node_ids", [])
        expected_edges = workflow.get("input_edge_ids", [])
        if (
            len(input_edges) != len(expected_edges)
            or len(upstream_ids) != len(set(upstream_ids))
            or set(upstream_ids) != set(expected_sources)
        ):
            raise ValueError("Guided Scenario inputs no longer match this workflow's canonical data edges. Restore or restart the workflow before running it.")
        # Edge IDs are kept for provenance. If a user restores the same semantic
        # direct inputs with a new edge object, a stale workflow may be rerun and
        # records that repaired input identity on the new run.
        workflow["input_edge_ids"] = [edge["id"] for edge in input_edges]
    if not upstream_ids:
        raise ValueError("Guided Scenario requires at least one direct data input node.")
    source_context = upstream_context(canvas, upstream_ids)
    if not any(str(item.get("text") or "").strip() for item in source_context):
        raise ValueError("Guided Scenario requires direct research text or multimodal text context.")

    package_ids = [
        str(item)
        for item in definition.get("execution", {}).get("tool_package_ids", [])
        if isinstance(item, str) and item
    ]
    snapshot = tool_snapshot(package_ids)
    if len(snapshot) != len(package_ids):
        raise ValueError("Guided Scenario references an unavailable tool package.")

    run_id = f"run-{uuid.uuid4().hex[:10]}"
    result = generate_guided_scenarios(source_context, snapshot, api_key=api_key)
    branches = result["branches"]
    run = {
        "id": run_id,
        "node_id": node_id,
        "status": "succeeded",
        "input_node_ids": upstream_ids,
        "output_node_ids": [],
        "context_snapshot": {
            "direct_input_node_ids": upstream_ids,
            "edge_policy": "data edges only; sibling branches excluded",
            "operation_definition": {
                "id": definition.get("id", ""),
                "version": definition.get("version", ""),
            },
            "requested_output_profile": operation.get("config", {}).get("output_profile", "branch-set"),
            "selected_tools": package_ids,
            "tool_snapshot": snapshot,
            "facilitation_contract": {
                "branch_count": 4,
                "requires_human_branch_selection": True,
                "required_summary_lenses": ["shared ground", "disagreement", "unresolved question"],
            },
        },
        "model_snapshot": result["model_snapshot"],
        "created_at": utc_now(),
    }

    output_nodes = []
    edges = []
    scopes = []
    base_position = operation.get("position", {})
    for index, branch in enumerate(branches):
        output_node = normalize_node(
            {
                "type": "text",
                "title": f"{branch['strategy_label']} scenario",
                "position": {
                    "x": base_position.get("x", 0) + 340,
                    "y": base_position.get("y", 0) + index * 180,
                },
                "payload": {
                    "text": render_branch_text(branch),
                    "scenario_branch": branch,
                    "provenance": [{"produced_by_run_id": run_id}],
                },
                "status": "success",
            }
        )
        output_node["produced_by_run_id"] = run_id
        output_nodes.append(output_node)
        run["output_node_ids"].append(output_node["id"])
        edges.append(
            {
                "id": f"edge-{uuid.uuid4().hex[:8]}",
                "source_node_id": node_id,
                "target_node_id": output_node["id"],
                "source_port": "out",
                "target_port": "in",
                "edge_kind": "data",
                "created_at": utc_now(),
            }
        )

    canvas["runs"].append(run)
    canvas["nodes"].extend(output_nodes)
    canvas["edges"].extend(edges)
    for output_node, branch in zip(output_nodes, branches):
        scope = create_scope_record(
            canvas,
            {
                "id": f"scope-{run_id}-{branch['strategy']}",
                "label": f"{branch['strategy_label']}: {branch['what_if'][:72]}",
                "mode": "snapshot",
                "selector": {"kind": "explicit", "node_ids": [*upstream_ids, output_node["id"]]},
            },
        )
        scopes.append(scope)

    operation["active_run_id"] = run_id
    operation["status"] = "success"
    workflow_result = record_workflow_futures(canvas, node_id, run, output_nodes, scopes)
    if workflow_result:
        stale_branch_ids = set(workflow_result.get("stale_branch_node_ids", []))
        for candidate in canvas.get("nodes", []):
            if candidate.get("id") in stale_branch_ids:
                candidate["status"] = "stale"
        _record_graph_activity(
            canvas,
            "Generated four What-if futures from the current canonical inputs.",
            requested_session_id=session_id,
            workflow=workflow_result.get("workflow"),
            related_node_ids=[node_id, *run["output_node_ids"]],
            activity_type="workflow.futures_generated",
        )
    execution = record_execution_from_run(canvas, run, "scope-global")
    if not workflow_result:
        _record_graph_activity(
            canvas,
            f"Ran {operation.get('title') or 'Operation'} and added {len(output_nodes)} output nodes.",
            requested_session_id=session_id,
            related_node_ids=[node_id, *run["output_node_ids"]],
            activity_type="execution.completed",
        )
    record_graph_event(
        canvas,
        "operation.guided_scenario.completed",
        {
            "execution_id": execution["id"],
            "run_id": run_id,
            "branch_node_ids": run["output_node_ids"],
            "scope_ids": [scope["id"] for scope in scopes],
            "workflow_id": (workflow_result or {}).get("workflow", {}).get("id", ""),
            "fallback_used": bool(result["model_snapshot"].get("fallback_used")),
        },
    )
    write_canvas(project_id, canvas)
    return {
        "run": run,
        "execution": execution,
        "output_nodes": output_nodes,
        "edges": edges,
        "scopes": scopes,
        "workflow": (workflow_result or {}).get("workflow"),
        "comparison_scope": (workflow_result or {}).get("comparison_scope"),
    }


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
    raw_policy = config.get("selection_policy") if isinstance(config, dict) and isinstance(config.get("selection_policy"), dict) else {}
    try:
        configured_minimum = int(raw_policy.get("minimum_selected") or 0)
    except (TypeError, ValueError):
        configured_minimum = 0
    minimum_selected = min(24, max(0, configured_minimum))
    recommended_tool_ids = []
    for tool_id in raw_policy.get("recommended_tool_ids", []):
        value = str(tool_id or "").strip()
        if value and value not in recommended_tool_ids:
            recommended_tool_ids.append(value)
    selection_policy = {
        "minimum_selected": minimum_selected,
        "required_for": str(raw_policy.get("required_for") or "")[:96],
        "recommended_tool_ids": recommended_tool_ids,
    }
    return {
        **(config if isinstance(config, dict) else {}),
        "composition": (config.get("composition") if isinstance(config, dict) else None) or "parallel",
        "output_type": output_type,
        "tools": tools,
        "selection_policy": selection_policy,
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
        if not payload.get("title"):
            node["title"] = node["config"]["definition"]["label"]
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
