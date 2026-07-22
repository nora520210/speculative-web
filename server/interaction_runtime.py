from __future__ import annotations

"""Conversation, scope, command, and execution primitives for a graph workspace.

This module deliberately works on a canvas dictionary.  The file-backed graph store
uses it today; a database repository can use the same contracts later without the
conversation surface becoming a second, copied graph.
"""

from copy import deepcopy
from datetime import datetime, timezone
import uuid


CONTROL_POLICIES = {"manual", "propose", "confirm", "auto"}
SCOPE_MODES = {"live", "snapshot"}
SCOPE_SELECTOR_KINDS = {"all", "explicit", "neighborhood"}
COMMAND_ACTIONS = {"create_node", "patch_node", "connect_nodes", "create_scope"}
COMMAND_STATUSES = {"proposed", "approved", "rejected", "applied", "superseded"}
EXECUTION_STATUSES = {"queued", "running", "awaiting_input", "succeeded", "failed", "cancelled"}


class RevisionConflict(ValueError):
    """Raised when a command was prepared from an out-of-date graph revision."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


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

    canvas["scopes"] = [normalize_scope(scope, canvas) for scope in canvas["scopes"] if isinstance(scope, dict)]
    if not any(scope.get("id") == "scope-global" for scope in canvas["scopes"]):
        canvas["scopes"].insert(0, global_scope())

    if not canvas["conversation_sessions"]:
        canvas["conversation_sessions"].append(default_session(canvas, seed_demo=seed_demo))
    else:
        canvas["conversation_sessions"] = [
            normalize_session(session, canvas) for session in canvas["conversation_sessions"] if isinstance(session, dict)
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
    if seed_demo and canvas.get("nodes"):
        return {
            "id": "session-workbench",
            "title": "Research thread",
            "status": "active",
            "control_policy": "confirm",
            "active_scope_id": "scope-current-inquiry",
            "progress": [
                {"id": "step-material", "label": "Frame material", "scope_id": "scope-research-material", "status": "succeeded"},
                {"id": "step-inquiry", "label": "Develop premise", "scope_id": "scope-current-inquiry", "status": "active"},
                {"id": "step-artifact", "label": "Materialise branch", "scope_id": "scope-artifact-branch", "status": "pending"},
            ],
            "messages": [
                {
                    "id": "message-system-scope",
                    "role": "system",
                    "body": "This conversation is attached to a graph scope, not a copied canvas.",
                    "scope_id": "scope-current-inquiry",
                    "related_node_ids": [],
                    "created_at": utc_now(),
                },
                {
                    "id": "message-assistant-focus",
                    "role": "assistant",
                    "body": "当前正在形成研究前提。中间只显示这一步关联的节点；全局关系保留在右侧导航中。",
                    "scope_id": "scope-current-inquiry",
                    "related_node_ids": scope_node_ids(canvas, get_scope(canvas, "scope-current-inquiry") or global_scope()),
                    "created_at": utc_now(),
                },
            ],
            "created_at": utc_now(),
            "updated_at": utc_now(),
        }
    return {
        "id": new_id("session"),
        "title": "Working thread",
        "status": "active",
        "control_policy": "confirm",
        "active_scope_id": "scope-global",
        "progress": [{"id": new_id("step"), "label": "Start", "scope_id": "scope-global", "status": "active"}],
        "messages": [],
        "created_at": utc_now(),
        "updated_at": utc_now(),
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
                "status": item.get("status") if item.get("status") in {"pending", "active", "succeeded", "failed"} else "pending",
                "execution_id": str(item.get("execution_id") or ""),
            }
        )
    if not progress:
        progress = [{"id": new_id("step"), "label": "Start", "scope_id": active_scope_id, "status": "active", "execution_id": ""}]
    messages = []
    for message in session.get("messages", []):
        if not isinstance(message, dict):
            continue
        messages.append(
            {
                "id": str(message.get("id") or new_id("message")),
                "role": message.get("role") if message.get("role") in {"system", "user", "assistant"} else "system",
                "body": str(message.get("body") or "")[:12000],
                "scope_id": message.get("scope_id") if message.get("scope_id") in scope_ids else active_scope_id,
                "related_node_ids": normalize_node_ids(message.get("related_node_ids"), canvas),
                "execution_id": str(message.get("execution_id") or ""),
                "created_at": message.get("created_at") or utc_now(),
            }
        )
    return {
        "id": str(session.get("id") or new_id("session")),
        "title": str(session.get("title") or "Working thread")[:96],
        "status": session.get("status") if session.get("status") in {"active", "paused", "closed"} else "active",
        "control_policy": session.get("control_policy") if session.get("control_policy") in CONTROL_POLICIES else "confirm",
        "active_scope_id": active_scope_id,
        "progress": progress,
        "messages": messages,
        "created_at": session.get("created_at") or utc_now(),
        "updated_at": session.get("updated_at") or utc_now(),
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
        "conversation_sessions": deepcopy(canvas.get("conversation_sessions", [])),
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
            "active_scope_id": payload.get("active_scope_id") or "scope-global",
            "messages": [],
            "progress": payload.get("progress") or [],
        },
        canvas,
    )
    canvas["conversation_sessions"].append(session)
    return deepcopy(session)


def append_message(canvas: dict, session_id: str, payload: dict) -> dict:
    session = next((item for item in canvas.get("conversation_sessions", []) if item.get("id") == session_id), None)
    if not session:
        raise KeyError(f"Conversation session not found: {session_id}")
    role = payload.get("role") if payload.get("role") in {"user", "assistant", "system"} else "user"
    body = str(payload.get("body") or "").strip()
    if not body:
        raise ValueError("Message body cannot be empty.")
    message = {
        "id": new_id("message"),
        "role": role,
        "body": body[:12000],
        "scope_id": payload.get("scope_id") or session.get("active_scope_id") or "scope-global",
        "related_node_ids": normalize_node_ids(payload.get("related_node_ids"), canvas),
        "execution_id": str(payload.get("execution_id") or ""),
        "created_at": utc_now(),
    }
    session.setdefault("messages", []).append(message)
    session["updated_at"] = utc_now()
    return deepcopy(message)


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
