from __future__ import annotations

"""Conversation, scope, command, and execution primitives for a graph workspace.

This module deliberately works on a canvas dictionary.  The file-backed graph store
uses it today; a database repository can use the same contracts later without the
conversation surface becoming a second, copied graph.
"""

from copy import deepcopy
from datetime import datetime, timezone
import uuid

from server.workflow_registry import workflow_runtime_contract


CONTROL_POLICIES = {"manual", "propose", "confirm", "auto"}
SCOPE_MODES = {"live", "snapshot"}
SCOPE_SELECTOR_KINDS = {"all", "explicit", "neighborhood"}
COMMAND_ACTIONS = {"create_node", "patch_node", "connect_nodes", "create_scope"}
COMMAND_STATUSES = {"proposed", "approved", "rejected", "applied", "superseded"}
EXECUTION_STATUSES = {"queued", "running", "awaiting_input", "succeeded", "failed", "cancelled"}
PROGRESS_STATUSES = {"pending", "active", "succeeded", "failed", "stale"}
WORKFLOW_STATUSES = {"active", "awaiting_selection", "tools", "scenario", "discussion", "stale", "complete"}
MESSAGE_KINDS = {"message", "guide", "activity"}
MESSAGE_STATES = {"active", "superseded", "removed"}
MAX_CONVERSATION_FEEDBACK_CHARS = 200
GUIDE_STAGE_IDS = {
    "start",
    "frame_focus",
    "frame_assumptions",
    "frame_stakeholders",
    "frame_tensions",
    "input",
    "keywords",
    "four_futures",
    "choose_future",
    "tools",
    "scenario_probe",
    "scenario_refine",
    "scenario_ready",
    "scenario",
    "discussion",
    "stale",
}


class RevisionConflict(ValueError):
    """Raised when a command was prepared from an out-of-date graph revision."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def compact_conversation_feedback(value: object) -> str:
    """Keep system feedback scannable without limiting a user's research input."""

    body = str(value or "").strip()
    if len(body) <= MAX_CONVERSATION_FEEDBACK_CHARS:
        return body
    return f"{body[: MAX_CONVERSATION_FEEDBACK_CHARS - 1].rstrip()}…"


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


def ensure_interaction_data(canvas: dict, *, seed_demo: bool = False) -> None:
    """Migrate a V1 canvas in memory to the additive V2 interaction shape."""

    canvas["schema_version"] = max(int(canvas.get("schema_version") or canvas.get("version") or 1), 2)
    canvas.setdefault("revision", 0)
    canvas.setdefault("events", [])
    canvas.setdefault("scopes", [])
    canvas.setdefault("conversation_sessions", [])
    canvas.setdefault("command_proposals", [])
    canvas.setdefault("executions", [])
    canvas.setdefault("workflow_instances", [])

    canvas["scopes"] = [normalize_scope(scope, canvas) for scope in canvas["scopes"] if isinstance(scope, dict)]
    if not any(scope.get("id") == "scope-global" for scope in canvas["scopes"]):
        canvas["scopes"].insert(0, global_scope())

    if not canvas["conversation_sessions"]:
        canvas["conversation_sessions"].append(default_session(canvas, seed_demo=seed_demo))
    else:
        canvas["conversation_sessions"] = [
            normalize_session(session, canvas) for session in canvas["conversation_sessions"] if isinstance(session, dict)
        ]
        canvas["conversation_sessions"] = [
            default_session(canvas, seed_demo=True) if is_legacy_demo_entry_session(session) else session
            for session in canvas["conversation_sessions"]
        ]

    canvas["workflow_instances"] = [
        normalize_workflow(workflow, canvas) for workflow in canvas["workflow_instances"] if isinstance(workflow, dict)
    ]

    canvas["command_proposals"] = [
        normalize_command(proposal, canvas) for proposal in canvas["command_proposals"] if isinstance(proposal, dict)
    ]
    canvas["executions"] = [
        normalize_execution(execution) for execution in canvas["executions"] if isinstance(execution, dict)
    ]

    if seed_demo and len(canvas["scopes"]) == 1 and canvas.get("nodes"):
        canvas["scopes"].extend(demo_scopes(canvas))
        canvas["conversation_sessions"] = [default_session(canvas, seed_demo=True)]
        operation = next((node for node in canvas.get("nodes", []) if node.get("type") in {"modify", "operation"}), None)
        canvas["command_proposals"].append(
            normalize_command(
                {
                    "id": "command-confirm-premise",
                    "title": "Confirm the current premise before creating a branch",
                    "action": "patch_node",
                    "status": "proposed",
                    "scope_id": "scope-current-inquiry",
                    "session_id": "session-workbench",
                    "target_node_ids": [operation.get("id")] if operation else [],
                    "arguments": {"note": "A future executor may apply this only after confirmation."},
                },
                canvas,
            )
        )


def global_scope() -> dict:
    return {
        "id": "scope-global",
        "label": "Global graph",
        "mode": "live",
        "selector": {"kind": "all"},
        "viewport": {"x": 0, "y": 0, "zoom": 0.45},
        "created_at": utc_now(),
    }


def demo_scopes(canvas: dict) -> list[dict]:
    nodes = canvas.get("nodes", [])
    ids = [node.get("id") for node in nodes if node.get("id")]
    operation = next((node for node in nodes if node.get("type") in {"modify", "operation"}), None)
    source_ids = [node_id for node_id in ids if node_id != (operation or {}).get("id")]
    if operation:
        focus_ids = source_ids[:2] + [operation["id"]]
        artifact_ids = [operation["id"]] + [node_id for node_id in ids if node_id not in source_ids[:2] and node_id != operation["id"]]
    else:
        focus_ids = ids[:3]
        artifact_ids = ids[-2:]
    return [
        normalize_scope(
            {
                "id": "scope-research-material",
                "label": "Research material",
                "mode": "live",
                "selector": {"kind": "explicit", "node_ids": source_ids[:2]},
            },
            canvas,
        ),
        normalize_scope(
            {
                "id": "scope-current-inquiry",
                "label": "Current inquiry",
                "mode": "live",
                "selector": {"kind": "explicit", "node_ids": focus_ids},
            },
            canvas,
        ),
        normalize_scope(
            {
                "id": "scope-artifact-branch",
                "label": "Artifact branch",
                "mode": "live",
                "selector": {"kind": "explicit", "node_ids": artifact_ids},
            },
            canvas,
        ),
    ]


def default_session(canvas: dict, *, seed_demo: bool = False) -> dict:
    # Start the guided thread inside the local inquiry when that Scope exists.
    # The global graph remains available as a navigator, but it should not be the
    # default amount of information a new participant has to parse.
    scope_ids = {scope.get("id") for scope in canvas.get("scopes", []) if isinstance(scope, dict)}
    default_scope_id = "scope-current-inquiry" if "scope-current-inquiry" in scope_ids else "scope-global"
    if seed_demo and canvas.get("nodes"):
        return {
            "id": "session-workbench",
            "title": "Research thread",
            "status": "active",
            "control_policy": "confirm",
            "guide": default_guide(),
            "active_scope_id": default_scope_id,
            "progress": [
                {
                    "id": "step-start",
                    "label": "Start inquiry",
                    "scope_id": default_scope_id,
                    "status": "active",
                    "workflow_stage_id": "start",
                },
            ],
            "messages": [],
            "created_at": utc_now(),
            "updated_at": utc_now(),
        }
    return {
        "id": new_id("session"),
        "title": "Working thread",
        "status": "active",
        "control_policy": "confirm",
        "guide": default_guide(),
        "active_scope_id": default_scope_id,
        "progress": [
            {
                "id": new_id("step"),
                "label": "Start inquiry",
                "scope_id": default_scope_id,
                "status": "active",
                "workflow_stage_id": "start",
            }
        ],
        "messages": [],
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }


def is_legacy_demo_entry_session(session: dict) -> bool:
    """Recognize untouched demo entry records before applying the current clean seed.

    Both historical demo forms are safe to replace: the original three-step narrative
    and the brief intermediate one-step, global-Scope seed. Neither has user messages
    or a workflow instance, so this migration cannot overwrite authored work.
    """

    if session.get("id") != "session-workbench":
        return False
    guide = session.get("guide") if isinstance(session.get("guide"), dict) else {}
    if guide.get("workflow_instance_id") or guide.get("stage_id") != "start":
        return False
    progress = [item for item in session.get("progress", []) if isinstance(item, dict)]
    progress_ids = {item.get("id") for item in progress}
    message_ids = {item.get("id") for item in session.get("messages", []) if isinstance(item, dict)}
    original_three_step_seed = progress_ids == {"step-material", "step-inquiry", "step-artifact"} and message_ids == {
        "message-system-scope",
        "message-assistant-focus",
    }
    intermediate_global_seed = (
        session.get("active_scope_id") == "scope-global"
        and not message_ids
        and len(progress) == 1
        and progress[0].get("id") == "step-start"
        and progress[0].get("scope_id") == "scope-global"
        and progress[0].get("workflow_stage_id") == "start"
    )
    return original_three_step_seed or intermediate_global_seed


def default_guide() -> dict:
    """State for the deterministic, conversation-first entry flow.

    This deliberately holds only workflow navigation and never copies a brief, a
    tool choice, or an executor configuration.  The graph remains canonical.
    """

    return {
        "kind": "four_futures",
        "status": "active",
        "stage_id": "start",
        "workflow_definition_id": "workflow.four-futures-foundation",
        "workflow_instance_id": "",
        "start_mode": "research",
        "pending_field": "topic",
    }


def normalize_guide(value, *, workflow_instance_id: str = "") -> dict:
    raw = value if isinstance(value, dict) else {}
    stage_id = str(raw.get("stage_id") or ("discussion" if workflow_instance_id else "start"))
    if stage_id not in GUIDE_STAGE_IDS:
        stage_id = "start"
    status = str(raw.get("status") or "active")
    if status not in {"active", "idle"}:
        status = "active"
    start_mode = str(raw.get("start_mode") or "research")
    if start_mode not in {"research", "design"}:
        start_mode = "research"
    pending_field = str(raw.get("pending_field") or "")
    if pending_field not in {"topic", "research_focus", "assumptions", "stakeholders", "tensions", ""}:
        pending_field = ""
    return {
        "kind": "four_futures",
        "status": status,
        "stage_id": stage_id,
        "workflow_definition_id": "workflow.four-futures-foundation",
        "workflow_instance_id": str(raw.get("workflow_instance_id") or workflow_instance_id or ""),
        "start_mode": start_mode,
        "pending_field": pending_field,
    }


def normalize_scope(scope: dict, canvas: dict) -> dict:
    selector = scope.get("selector") if isinstance(scope.get("selector"), dict) else {}
    kind = selector.get("kind") if selector.get("kind") in SCOPE_SELECTOR_KINDS else "explicit"
    node_ids = normalize_node_ids(selector.get("node_ids"), canvas)
    root_ids = normalize_node_ids(selector.get("root_node_ids"), canvas)
    normalized_selector = {
        "kind": kind,
        "node_ids": node_ids,
        "root_node_ids": root_ids,
        "max_depth": min(8, max(0, int(selector.get("max_depth", 1) or 1))),
        "edge_kinds": [str(item) for item in selector.get("edge_kinds", []) if str(item)],
    }
    mode = scope.get("mode") if scope.get("mode") in SCOPE_MODES else "live"
    return {
        "id": str(scope.get("id") or new_id("scope")),
        "label": str(scope.get("label") or "Untitled scope")[:96],
        "mode": mode,
        "selector": normalized_selector,
        "snapshot_node_ids": normalize_node_ids(scope.get("snapshot_node_ids"), canvas),
        "source_revision": int(scope.get("source_revision") or canvas.get("revision") or 0),
        "viewport": normalize_viewport(scope.get("viewport")),
        "created_at": scope.get("created_at") or utc_now(),
        "updated_at": scope.get("updated_at") or utc_now(),
    }


def normalize_session(session: dict, canvas: dict) -> dict:
    scope_ids = {scope["id"] for scope in canvas.get("scopes", [])}
    active_scope_id = session.get("active_scope_id") if session.get("active_scope_id") in scope_ids else "scope-global"
    progress = []
    for item in session.get("progress", []):
        if not isinstance(item, dict):
            continue
        progress.append(
            {
                "id": str(item.get("id") or new_id("step")),
                "label": str(item.get("label") or "Untitled step")[:96],
                "scope_id": item.get("scope_id") if item.get("scope_id") in scope_ids else active_scope_id,
                "status": item.get("status") if item.get("status") in PROGRESS_STATUSES else "pending",
                "workflow_stage_id": str(item.get("workflow_stage_id") or "")[:64],
                "execution_id": str(item.get("execution_id") or ""),
            }
        )
    if not progress:
        progress = [
            {
                "id": new_id("step"),
                "label": "Start",
                "scope_id": active_scope_id,
                "status": "active",
                "workflow_stage_id": "",
                "execution_id": "",
            }
        ]
    messages = []
    for message in session.get("messages", []):
        if not isinstance(message, dict):
            continue
        role = message.get("role") if message.get("role") in {"system", "user", "assistant"} else "system"
        body = str(message.get("body") or "")
        messages.append(
            {
                "id": str(message.get("id") or new_id("message")),
                "role": role,
                "kind": message.get("kind") if message.get("kind") in MESSAGE_KINDS else "message",
                "body": (
                    body[:12000]
                    if role == "user"
                    else compact_conversation_feedback(body)
                ),
                "scope_id": message.get("scope_id") if message.get("scope_id") in scope_ids else active_scope_id,
                # Conversation history is an audit surface. Keep references to a
                # removed node instead of silently erasing the historical link on
                # the next read/migration pass.
                "related_node_ids": normalize_reference_ids(message.get("related_node_ids")),
                "related_node_refs": normalize_message_node_refs(
                    message.get("related_node_refs"),
                    canvas,
                    message.get("related_node_ids"),
                ),
                "execution_id": str(message.get("execution_id") or ""),
                "input_perspective": normalize_input_perspective(message.get("input_perspective")),
                "activity": normalize_activity(message.get("activity")),
                "state": normalize_message_state(message.get("state")),
                "inactive_reason": compact_conversation_feedback(message.get("inactive_reason") or ""),
                "inactive_at": str(message.get("inactive_at") or ""),
                "created_at": message.get("created_at") or utc_now(),
            }
        )
    return {
        "id": str(session.get("id") or new_id("session")),
        "title": str(session.get("title") or "Working thread")[:96],
        "status": session.get("status") if session.get("status") in {"active", "paused", "closed"} else "active",
        "control_policy": session.get("control_policy") if session.get("control_policy") in CONTROL_POLICIES else "confirm",
        "workflow_instance_id": str(session.get("workflow_instance_id") or ""),
        "guide": normalize_guide(
            session.get("guide"),
            workflow_instance_id=str(session.get("workflow_instance_id") or ""),
        ),
        "active_scope_id": active_scope_id,
        "progress": progress,
        "messages": messages,
        "created_at": session.get("created_at") or utc_now(),
        "updated_at": session.get("updated_at") or utc_now(),
    }


def normalize_activity(value) -> dict:
    value = value if isinstance(value, dict) else {}
    return {
        "type": str(value.get("type") or "")[:96],
        "workflow_id": str(value.get("workflow_id") or "")[:128],
        "stage_id": str(value.get("stage_id") or "")[:64],
        "action_id": str(value.get("action_id") or "")[:96],
    }


def normalize_message_state(value: object) -> str:
    return str(value or "active") if str(value or "active") in MESSAGE_STATES else "active"


def normalize_input_perspective(value: object) -> str:
    perspective = str(value or "").strip().lower()
    return perspective if perspective in {"research", "design"} else ""


def normalize_message_node_refs(value, canvas: dict, related_node_ids) -> list[dict]:
    """Keep a readable node label even after a direct graph deletion.

    Node IDs remain canonical references; the small title snapshot is presentation
    provenance for the conversation history and never recreates node content.
    """

    node_titles = {
        str(node.get("id")): str(node.get("title") or node.get("type") or "Node")[:96]
        for node in canvas.get("nodes", [])
        if node.get("id")
    }
    refs = []
    seen = set()
    for item in value if isinstance(value, list) else []:
        if not isinstance(item, dict):
            continue
        node_id = str(item.get("id") or "").strip()
        if not node_id or node_id in seen:
            continue
        refs.append({"id": node_id, "title": str(item.get("title") or node_titles.get(node_id) or node_id)[:96]})
        seen.add(node_id)
    for node_id in normalize_reference_ids(related_node_ids):
        if node_id in seen:
            continue
        refs.append({"id": node_id, "title": node_titles.get(node_id, node_id)})
        seen.add(node_id)
    return refs


def normalize_workflow(workflow: dict, canvas: dict) -> dict:
    """Normalize a workflow instance without copying graph nodes into workflow state."""

    known_node_ids = {node["id"] for node in canvas.get("nodes", [])}
    # Workflow references deliberately remain visible even when a direct node or
    # edge was deleted. Silently dropping them would make an incomplete workflow
    # appear runnable after a reload. Runtime invalidation owns recovery instead.
    node_ids = normalize_reference_ids(workflow.get("source_node_ids"))
    branch_node_ids = normalize_reference_ids(workflow.get("branch_node_ids"))
    scope_ids = {scope["id"] for scope in canvas.get("scopes", [])}
    sessions = {session["id"] for session in canvas.get("conversation_sessions", [])}
    branch_scope_ids = {}
    raw_branch_scopes = workflow.get("branch_scope_ids") if isinstance(workflow.get("branch_scope_ids"), dict) else {}
    for branch_id in branch_node_ids:
        scope_id = raw_branch_scopes.get(branch_id)
        if scope_id in scope_ids:
            branch_scope_ids[branch_id] = scope_id
    selected_branch_node_id = workflow.get("selected_branch_node_id")
    if selected_branch_node_id not in branch_node_ids or selected_branch_node_id not in known_node_ids:
        selected_branch_node_id = ""
    discussion_node_id = str(workflow.get("discussion_node_id") or "")
    if discussion_node_id not in known_node_ids:
        discussion_node_id = ""
    active_scenario_node_id = str(workflow.get("active_scenario_node_id") or "")
    if active_scenario_node_id not in known_node_ids:
        active_scenario_node_id = ""
    input_edge_ids = normalize_reference_ids(workflow.get("input_edge_ids"))
    if not input_edge_ids:
        # Additive migration for foundation instances created before explicit input
        # edge provenance existed. Only the existing direct workflow sources qualify.
        operation_node_id = str(workflow.get("operation_node_id") or "")
        input_edge_ids = [
            str(edge.get("id"))
            for edge in canvas.get("edges", [])
            if edge.get("edge_kind") == "data"
            and edge.get("target_node_id") == operation_node_id
            and edge.get("source_node_id") in node_ids
            and edge.get("id")
        ]

    raw_snapshot = workflow.get("definition_snapshot") if isinstance(workflow.get("definition_snapshot"), dict) else {}
    snapshot_stages = []
    for stage in raw_snapshot.get("stages", []):
        if not isinstance(stage, dict) or not stage.get("id"):
            continue
        snapshot_stages.append(
            {
                "id": str(stage["id"])[:64],
                "label": str(stage.get("label") or stage["id"])[:96],
                "kind": str(stage.get("kind") or "input")[:32],
            }
        )
    snapshot_locales = raw_snapshot.get("locales") if isinstance(raw_snapshot.get("locales"), dict) else {}
    definition_snapshot = {
        "id": str(raw_snapshot.get("id") or (workflow.get("definition_ref") or {}).get("id") or "")[:128],
        "version": str(raw_snapshot.get("version") or (workflow.get("definition_ref") or {}).get("version") or "")[:64],
        "label": str(raw_snapshot.get("label") or workflow.get("label") or "Guided workflow")[:96],
        "stages": snapshot_stages,
        "locales": deepcopy(snapshot_locales),
        "runtime": workflow_runtime_contract(raw_snapshot),
        "discussion_tool_policy": deepcopy(
            raw_snapshot.get("discussion_tool_policy")
            if isinstance(raw_snapshot.get("discussion_tool_policy"), dict)
            else {}
        ),
    }

    return {
        "id": str(workflow.get("id") or new_id("workflow")),
        "definition_ref": {
            "id": str((workflow.get("definition_ref") or {}).get("id") or ""),
            "version": str((workflow.get("definition_ref") or {}).get("version") or ""),
        },
        "definition_snapshot": definition_snapshot,
        "label": str(workflow.get("label") or "Guided workflow")[:96],
        "status": workflow.get("status") if workflow.get("status") in WORKFLOW_STATUSES else "active",
        "stage": str(workflow.get("stage") or "frame")[:64],
        "session_id": workflow.get("session_id") if workflow.get("session_id") in sessions else "",
        "foundation_scope_id": workflow.get("foundation_scope_id") if workflow.get("foundation_scope_id") in scope_ids else "",
        "comparison_scope_id": workflow.get("comparison_scope_id") if workflow.get("comparison_scope_id") in scope_ids else "",
        "source_node_ids": node_ids,
        "keyword_node_id": str(workflow.get("keyword_node_id") or ""),
        "operation_node_id": str(workflow.get("operation_node_id") or ""),
        "input_edge_ids": input_edge_ids,
        "branch_node_ids": branch_node_ids,
        "branch_scope_ids": branch_scope_ids,
        "selected_branch_node_id": selected_branch_node_id,
        "discussion_node_id": discussion_node_id,
        "active_scenario_node_id": active_scenario_node_id,
        "input_revision": int(workflow.get("input_revision") or canvas.get("revision") or 0),
        "created_at": workflow.get("created_at") or utc_now(),
        "updated_at": workflow.get("updated_at") or utc_now(),
    }


def normalize_command(proposal: dict, canvas: dict) -> dict:
    scope_ids = {scope["id"] for scope in canvas.get("scopes", [])}
    return {
        "id": str(proposal.get("id") or new_id("command")),
        "title": str(proposal.get("title") or "Graph proposal")[:120],
        "action": proposal.get("action") if proposal.get("action") in COMMAND_ACTIONS else "patch_node",
        "status": proposal.get("status") if proposal.get("status") in COMMAND_STATUSES else "proposed",
        "scope_id": proposal.get("scope_id") if proposal.get("scope_id") in scope_ids else "scope-global",
        "session_id": str(proposal.get("session_id") or ""),
        "message_id": str(proposal.get("message_id") or ""),
        "target_node_ids": normalize_node_ids(proposal.get("target_node_ids"), canvas),
        "arguments": deepcopy(proposal.get("arguments") if isinstance(proposal.get("arguments"), dict) else {}),
        "expected_revision": int(proposal.get("expected_revision") or canvas.get("revision") or 0),
        "created_at": proposal.get("created_at") or utc_now(),
        "resolved_at": proposal.get("resolved_at") or "",
    }


def normalize_execution(execution: dict) -> dict:
    return {
        "id": str(execution.get("id") or new_id("execution")),
        "run_id": str(execution.get("run_id") or ""),
        "node_id": str(execution.get("node_id") or ""),
        "scope_id": str(execution.get("scope_id") or "scope-global"),
        "status": execution.get("status") if execution.get("status") in EXECUTION_STATUSES else "queued",
        "steps": deepcopy(execution.get("steps") if isinstance(execution.get("steps"), list) else []),
        "created_at": execution.get("created_at") or utc_now(),
        "updated_at": execution.get("updated_at") or utc_now(),
    }


def normalize_node_ids(value, canvas: dict) -> list[str]:
    node_ids = {node.get("id") for node in canvas.get("nodes", [])}
    result = []
    for node_id in value if isinstance(value, list) else []:
        if isinstance(node_id, str) and node_id in node_ids and node_id not in result:
            result.append(node_id)
    return result


def normalize_reference_ids(value) -> list[str]:
    """Keep stable workflow references without treating missing graph items as data."""

    result = []
    for item in value if isinstance(value, list) else []:
        if isinstance(item, str) and item and item not in result:
            result.append(item)
    return result


def normalize_viewport(value) -> dict:
    value = value if isinstance(value, dict) else {}
    return {
        "x": float(value.get("x") or 0),
        "y": float(value.get("y") or 0),
        "zoom": min(1.0, max(0.2, float(value.get("zoom") or 1))),
    }


def get_scope(canvas: dict, scope_id: str) -> dict | None:
    return next((scope for scope in canvas.get("scopes", []) if scope.get("id") == scope_id), None)


def scope_node_ids(canvas: dict, scope: dict) -> list[str]:
    node_ids = [node.get("id") for node in canvas.get("nodes", []) if node.get("id")]
    if scope.get("mode") == "snapshot":
        snapshot = [node_id for node_id in scope.get("snapshot_node_ids", []) if node_id in node_ids]
        return snapshot
    selector = scope.get("selector") or {}
    kind = selector.get("kind")
    if kind == "all":
        return node_ids
    if kind == "explicit":
        return [node_id for node_id in selector.get("node_ids", []) if node_id in node_ids]
    if kind == "neighborhood":
        return neighborhood_node_ids(canvas, selector)
    return []


def neighborhood_node_ids(canvas: dict, selector: dict) -> list[str]:
    roots = [node_id for node_id in selector.get("root_node_ids", []) if node_id]
    depth = int(selector.get("max_depth") or 1)
    edge_kinds = set(selector.get("edge_kinds") or [])
    seen = list(roots)
    frontier = list(roots)
    for _ in range(depth):
        following = []
        for edge in canvas.get("edges", []):
            if edge_kinds and edge.get("edge_kind") not in edge_kinds:
                continue
            source = edge.get("source_node_id")
            target = edge.get("target_node_id")
            if source in frontier and target not in seen:
                following.append(target)
            if target in frontier and source not in seen:
                following.append(source)
        seen.extend(node_id for node_id in following if node_id not in seen)
        frontier = following
    known = {node.get("id") for node in canvas.get("nodes", [])}
    return [node_id for node_id in seen if node_id in known]


def scope_projection(canvas: dict, scope_id: str) -> dict:
    scope = get_scope(canvas, scope_id)
    if not scope:
        raise KeyError(f"Scope not found: {scope_id}")
    member_ids = scope_node_ids(canvas, scope)
    member_set = set(member_ids)
    nodes_by_id = {node.get("id"): node for node in canvas.get("nodes", [])}
    return {
        "scope": with_scope_count(scope, canvas),
        "revision": canvas.get("revision", 0),
        "nodes": [deepcopy(nodes_by_id[node_id]) for node_id in member_ids if node_id in nodes_by_id],
        "edges": [
            deepcopy(edge)
            for edge in canvas.get("edges", [])
            if edge.get("source_node_id") in member_set and edge.get("target_node_id") in member_set
        ],
    }


def with_scope_count(scope: dict, canvas: dict) -> dict:
    result = deepcopy(scope)
    result["node_count"] = len(scope_node_ids(canvas, scope))
    return result


def interaction_payload(canvas: dict) -> dict:
    return {
        "schema_version": canvas.get("schema_version", 2),
        "revision": canvas.get("revision", 0),
        "scopes": [with_scope_count(scope, canvas) for scope in canvas.get("scopes", [])],
        "conversation_sessions": [
            normalize_session(deepcopy(session), canvas)
            for session in canvas.get("conversation_sessions", [])
            if isinstance(session, dict)
        ],
        "workflow_instances": deepcopy(canvas.get("workflow_instances", [])),
        "command_proposals": deepcopy(canvas.get("command_proposals", [])),
        "executions": deepcopy(canvas.get("executions", [])),
    }


def create_scope(canvas: dict, payload: dict) -> dict:
    scope = normalize_scope(payload, canvas)
    if any(item.get("id") == scope["id"] for item in canvas.get("scopes", [])):
        raise ValueError("Scope id already exists.")
    if scope["mode"] == "snapshot" and not scope["snapshot_node_ids"]:
        # Snapshot membership is derived from its selector once, before the scope
        # becomes snapshot-only. Asking scope_node_ids on the snapshot itself would
        # otherwise read the still-empty snapshot_node_ids array.
        selector_scope = {**scope, "mode": "live"}
        scope["snapshot_node_ids"] = scope_node_ids(canvas, selector_scope)
    canvas["scopes"].append(scope)
    return with_scope_count(scope, canvas)


def create_conversation(canvas: dict, payload: dict) -> dict:
    session = normalize_session(
        {
            "id": payload.get("id") or new_id("session"),
            "title": payload.get("title") or "Working thread",
            "control_policy": payload.get("control_policy") or "confirm",
            "workflow_instance_id": payload.get("workflow_instance_id") or "",
            "guide": payload.get("guide") if isinstance(payload.get("guide"), dict) else default_guide(),
            "active_scope_id": payload.get("active_scope_id") or "scope-global",
            "messages": [],
            "progress": payload.get("progress") or [],
        },
        canvas,
    )
    canvas["conversation_sessions"].append(session)
    return deepcopy(session)


def set_conversation_scope(canvas: dict, session_id: str, scope_id: str) -> dict:
    """Move one conversation and its graph projection to the same canonical Scope."""

    session = next((item for item in canvas.get("conversation_sessions", []) if item.get("id") == session_id), None)
    if not session:
        raise KeyError(f"Conversation session not found: {session_id}")
    if not get_scope(canvas, scope_id):
        raise ValueError("Conversation scope does not exist.")
    session["active_scope_id"] = scope_id
    session["updated_at"] = utc_now()
    return deepcopy(session)


def append_message(canvas: dict, session_id: str, payload: dict) -> dict:
    session = next((item for item in canvas.get("conversation_sessions", []) if item.get("id") == session_id), None)
    if not session:
        raise KeyError(f"Conversation session not found: {session_id}")
    role = payload.get("role") if payload.get("role") in {"user", "assistant", "system"} else "user"
    body = str(payload.get("body") or "").strip()
    if not body:
        raise ValueError("Message body cannot be empty.")
    related_node_ids = normalize_node_ids(payload.get("related_node_ids"), canvas)
    message = {
        "id": new_id("message"),
        "role": role,
        "kind": payload.get("kind") if payload.get("kind") in MESSAGE_KINDS else "message",
        "body": body[:12000] if role == "user" else compact_conversation_feedback(body),
        "scope_id": payload.get("scope_id") or session.get("active_scope_id") or "scope-global",
        "related_node_ids": related_node_ids,
        "related_node_refs": normalize_message_node_refs(
            payload.get("related_node_refs"),
            canvas,
            related_node_ids,
        ),
        "execution_id": str(payload.get("execution_id") or ""),
        "input_perspective": normalize_input_perspective(payload.get("input_perspective")),
        "activity": normalize_activity(payload.get("activity")),
        "state": normalize_message_state(payload.get("state")),
        "inactive_reason": compact_conversation_feedback(payload.get("inactive_reason") or ""),
        "inactive_at": str(payload.get("inactive_at") or ""),
        "created_at": utc_now(),
    }
    session.setdefault("messages", []).append(message)
    session["updated_at"] = utc_now()
    return deepcopy(message)


def mark_messages_inactive(
    canvas: dict,
    *,
    related_node_ids: list[str],
    state: str,
    reason: str,
    workflow_id: str = "",
) -> list[str]:
    """Mark historical branch talk as no longer live without deleting it.

    A direct graph change must not rewrite a researcher's conversation. The timeline
    therefore keeps the original messages, marks only messages tied to affected nodes
    as superseded/removed, and leaves an explicit activity record to explain why.
    """

    next_state = normalize_message_state(state)
    if next_state == "active":
        raise ValueError("Inactive conversation messages require a non-active state.")
    affected_ids = set(normalize_reference_ids(related_node_ids))
    if not affected_ids and not workflow_id:
        return []
    changed = []
    for session in canvas.get("conversation_sessions", []):
        for message in session.get("messages", []):
            message_ids = set(normalize_reference_ids(message.get("related_node_ids")))
            message_workflow_id = str((message.get("activity") or {}).get("workflow_id") or "")
            if not (message_ids & affected_ids) and not (workflow_id and message_workflow_id == workflow_id):
                continue
            previous_state = normalize_message_state(message.get("state"))
            # Removal is stronger than supersession and must remain visible if a
            # source edit later invalidates the enclosing workflow as well.
            if previous_state == "removed" and next_state != "removed":
                continue
            message["state"] = next_state
            message["inactive_reason"] = compact_conversation_feedback(reason)
            message["inactive_at"] = utc_now()
            message["related_node_refs"] = normalize_message_node_refs(
                message.get("related_node_refs"),
                canvas,
                message.get("related_node_ids"),
            )
            changed.append(str(message.get("id") or ""))
    return [message_id for message_id in changed if message_id]


def append_activity_message(
    canvas: dict,
    session_id: str,
    body: str,
    *,
    scope_id: str = "",
    related_node_ids: list[str] | None = None,
    activity_type: str = "graph.changed",
    workflow_id: str = "",
    stage_id: str = "",
    action_id: str = "",
) -> dict:
    """Record one canonical graph action in the conversation timeline."""

    return append_message(
        canvas,
        session_id,
        {
            "role": "system",
            "kind": "activity",
            "body": body,
            "scope_id": scope_id,
            "related_node_ids": related_node_ids or [],
            "activity": {
                "type": activity_type,
                "workflow_id": workflow_id,
                "stage_id": stage_id,
                "action_id": action_id,
            },
        },
    )


def set_session_guide(
    session: dict,
    stage_id: str,
    *,
    workflow_instance_id: str = "",
    pending_field: str = "",
    status: str = "active",
) -> None:
    guide = normalize_guide(session.get("guide"), workflow_instance_id=workflow_instance_id or session.get("workflow_instance_id", ""))
    guide["stage_id"] = stage_id if stage_id in GUIDE_STAGE_IDS else guide["stage_id"]
    guide["status"] = status if status in {"active", "idle"} else guide["status"]
    if workflow_instance_id:
        guide["workflow_instance_id"] = workflow_instance_id
    guide["pending_field"] = pending_field
    session["guide"] = guide
    session["updated_at"] = utc_now()


def get_workflow(canvas: dict, workflow_id: str) -> dict | None:
    return next((item for item in canvas.get("workflow_instances", []) if item.get("id") == workflow_id), None)


def workflow_for_operation(canvas: dict, operation_node_id: str) -> dict | None:
    return next(
        (item for item in canvas.get("workflow_instances", []) if item.get("operation_node_id") == operation_node_id),
        None,
    )


def _progress_step(session: dict, stage_id: str) -> dict | None:
    return next(
        (step for step in session.get("progress", []) if step.get("workflow_stage_id") == stage_id),
        None,
    )


def _set_progress(session: dict, stage_id: str, status: str, *, scope_id: str | None = None, execution_id: str = "") -> None:
    step = _progress_step(session, stage_id)
    if not step:
        return
    step["status"] = status if status in PROGRESS_STATUSES else "pending"
    if scope_id:
        step["scope_id"] = scope_id
    if execution_id:
        step["execution_id"] = execution_id


def record_workflow_futures(
    canvas: dict,
    operation_node_id: str,
    run: dict,
    output_nodes: list[dict],
    branch_scopes: list[dict],
) -> dict | None:
    """Attach a Guided Scenario run to a workflow instance, if it owns this operation."""

    workflow = workflow_for_operation(canvas, operation_node_id)
    if not workflow:
        return None
    runtime = workflow_runtime_contract(workflow.get("definition_snapshot"))

    previous_branch_ids = list(workflow.get("branch_node_ids", []))
    branch_node_ids = [node["id"] for node in output_nodes]
    branch_scope_ids = {
        node["id"]: scope["id"]
        for node, scope in zip(output_nodes, branch_scopes)
        if node.get("id") and scope.get("id")
    }
    comparison_scope = create_scope(
        canvas,
        {
            "id": f"scope-{run['id']}-four-futures",
            "label": "Compare four What-if futures",
            "mode": "snapshot",
            "selector": {
                "kind": "explicit",
                "node_ids": [*workflow.get("source_node_ids", []), *branch_node_ids],
            },
        },
    )
    workflow.update(
        {
            "status": "awaiting_selection",
            "stage": runtime["future_stage_id"],
            "comparison_scope_id": comparison_scope["id"],
            "branch_node_ids": branch_node_ids,
            "branch_scope_ids": branch_scope_ids,
            "selected_branch_node_id": "",
            "input_revision": int(canvas.get("revision") or 0),
            "updated_at": utc_now(),
        }
    )

    session = next((item for item in canvas.get("conversation_sessions", []) if item.get("id") == workflow.get("session_id")), None)
    if session:
        session["active_scope_id"] = comparison_scope["id"]
        _set_progress(session, runtime["input_stage_id"], "succeeded", scope_id=comparison_scope["id"])
        _set_progress(session, runtime["future_stage_id"], "active", scope_id=comparison_scope["id"])
        _set_progress(session, runtime["tools_stage_id"], "pending", scope_id=comparison_scope["id"])
        _set_progress(session, runtime["scenario_stage_id"], "pending", scope_id=comparison_scope["id"])
        set_session_guide(
            session,
            "four_futures",
            workflow_instance_id=workflow["id"],
            pending_field="",
        )
        append_message(
            canvas,
            session["id"],
            {
                "role": "assistant",
                "scope_id": comparison_scope["id"],
                "related_node_ids": branch_node_ids,
                "execution_id": run.get("id", ""),
                "body": "Four What-if futures are ready. Compare their assumptions and tensions, then choose one branch before beginning discussion.",
            },
        )
        session["updated_at"] = utc_now()

    return {
        "workflow": deepcopy(workflow),
        "comparison_scope": comparison_scope,
        "stale_branch_node_ids": [node_id for node_id in previous_branch_ids if node_id not in branch_node_ids],
    }


def select_workflow_branch(canvas: dict, workflow_id: str, branch_node_id: str) -> dict:
    workflow = get_workflow(canvas, workflow_id)
    if not workflow:
        raise KeyError(f"Workflow not found: {workflow_id}")
    if workflow.get("status") == "stale":
        raise ValueError("The research brief changed. Re-run the four futures before selecting a branch.")
    if branch_node_id not in workflow.get("branch_node_ids", []):
        raise ValueError("Choose one of this workflow's current four futures.")
    scope_id = workflow.get("branch_scope_ids", {}).get(branch_node_id)
    if not scope_id or not get_scope(canvas, scope_id):
        raise ValueError("The selected future no longer has an isolated Scope.")

    branch = next((node for node in canvas.get("nodes", []) if node.get("id") == branch_node_id), None)
    scenario = (branch or {}).get("payload", {}).get("scenario_branch", {})
    opening_question = str((scenario.get("facilitation") or {}).get("opening_question") or "")
    branch_title = str((branch or {}).get("title") or "selected future")
    runtime = workflow_runtime_contract(workflow.get("definition_snapshot"))
    previous_branch_id = str(workflow.get("selected_branch_node_id") or "")
    previous_discussion_id = str(workflow.get("discussion_node_id") or "")
    if previous_branch_id and previous_branch_id != branch_node_id:
        stale_run_ids = {
            str(run.get("id"))
            for run in canvas.get("runs", [])
            if run.get("node_id") == previous_discussion_id
        }
        superseded_ids = [
            previous_branch_id,
            *[
                node.get("id")
                for node in canvas.get("nodes", [])
                if node.get("produced_by_run_id") in stale_run_ids
            ],
        ]
        for node in canvas.get("nodes", []):
            if node.get("id") in superseded_ids:
                node["status"] = "stale"
        mark_messages_inactive(
            canvas,
            related_node_ids=superseded_ids,
            state="superseded",
            reason="A different What-if branch is now the only active line of this workflow.",
            workflow_id=str(workflow.get("id") or ""),
        )
    workflow.update(
        {
            "status": "tools",
            "stage": runtime["tools_stage_id"],
            "selected_branch_node_id": branch_node_id,
            "active_scenario_node_id": "",
            "updated_at": utc_now(),
        }
    )

    session = next((item for item in canvas.get("conversation_sessions", []) if item.get("id") == workflow.get("session_id")), None)
    if session:
        session["active_scope_id"] = scope_id
        _set_progress(session, runtime["future_stage_id"], "succeeded", scope_id=scope_id)
        _set_progress(session, runtime["tools_stage_id"], "active", scope_id=scope_id)
        _set_progress(session, runtime["scenario_stage_id"], "pending", scope_id=scope_id)
        set_session_guide(
            session,
            "tools",
            workflow_instance_id=workflow["id"],
            pending_field="",
        )
        append_message(
            canvas,
            session["id"],
            {
                "role": "assistant",
                "scope_id": scope_id,
                "related_node_ids": [*workflow.get("source_node_ids", []), branch_node_id],
                "body": opening_question or f"You selected {branch_title}. What assumption in this future should the discussion challenge first?",
            },
        )
        session["updated_at"] = utc_now()

    return {
        "workflow": deepcopy(workflow),
        "session": deepcopy(session) if session else None,
        "scope_id": scope_id,
    }


def mark_workflows_stale_for_source_node(canvas: dict, node_id: str) -> list[dict]:
    """Mark derived futures stale when their explicit research input changes."""

    changed = []
    for workflow in canvas.get("workflow_instances", []):
        if node_id not in workflow.get("source_node_ids", []) or not workflow.get("branch_node_ids"):
            continue
        workflow["status"] = "stale"
        workflow["stage"] = "stale"
        workflow["updated_at"] = utc_now()
        session = next((item for item in canvas.get("conversation_sessions", []) if item.get("id") == workflow.get("session_id")), None)
        if session:
            _set_progress(session, "four_futures", "stale")
            _set_progress(session, "choose_future", "pending")
            _set_progress(session, "discussion", "pending")
            set_session_guide(
                session,
                "stale",
                workflow_instance_id=workflow["id"],
                pending_field="",
            )
            session["updated_at"] = utc_now()
        changed.append(deepcopy(workflow))
    return changed


def create_command_proposal(canvas: dict, payload: dict) -> dict:
    action = payload.get("action")
    if action not in COMMAND_ACTIONS:
        raise ValueError("Unsupported graph command action.")
    proposal = normalize_command({**payload, "id": new_id("command"), "status": "proposed"}, canvas)
    canvas["command_proposals"].append(proposal)
    return deepcopy(proposal)


def resolve_command_proposal(canvas: dict, command_id: str, resolution: str) -> dict:
    if resolution not in {"approved", "rejected"}:
        raise ValueError("Commands can only be approved or rejected at this stage.")
    proposal = next((item for item in canvas.get("command_proposals", []) if item.get("id") == command_id), None)
    if not proposal:
        raise KeyError(f"Command proposal not found: {command_id}")
    if proposal.get("status") != "proposed":
        raise ValueError("Only proposed commands can be resolved.")
    proposal["status"] = resolution
    proposal["resolved_at"] = utc_now()
    return deepcopy(proposal)


def record_execution_from_run(canvas: dict, run: dict, scope_id: str = "scope-global") -> dict:
    status = "succeeded" if run.get("status") == "succeeded" else "failed"
    execution = {
        "id": new_id("execution"),
        "run_id": run.get("id", ""),
        "node_id": run.get("node_id", ""),
        "scope_id": scope_id if get_scope(canvas, scope_id) else "scope-global",
        "status": status,
        "steps": [
            {"id": "context", "label": "Resolve context", "status": "succeeded"},
            {"id": "model", "label": "Run operation", "status": status},
            {"id": "materialize", "label": "Materialise output", "status": status},
        ],
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }
    canvas.setdefault("executions", []).append(execution)
    return execution


def assert_expected_revision(canvas: dict, expected_revision) -> None:
    if expected_revision is None or expected_revision == "":
        return
    try:
        expected = int(expected_revision)
    except (TypeError, ValueError) as exc:
        raise ValueError("expected_revision must be an integer.") from exc
    current = int(canvas.get("revision") or 0)
    if expected != current:
        raise RevisionConflict(f"Graph revision conflict: expected {expected}, current revision is {current}.")


def record_graph_event(canvas: dict, event_type: str, payload: dict | None = None) -> dict:
    canvas["revision"] = int(canvas.get("revision") or 0) + 1
    event = {
        "id": new_id("event"),
        "revision": canvas["revision"],
        "type": event_type,
        "payload": deepcopy(payload or {}),
        "created_at": utc_now(),
    }
    events = canvas.setdefault("events", [])
    events.append(event)
    if len(events) > 500:
        del events[:-500]
    return event
