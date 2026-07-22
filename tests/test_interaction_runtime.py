from server.graph_store import default_canvas, normalize_node
from server.interaction_runtime import (
    RevisionConflict,
    assert_expected_revision,
    create_command_proposal,
    interaction_payload,
    record_graph_event,
    resolve_command_proposal,
    scope_projection,
)
from server.operation_registry import list_operation_definitions


def test_default_canvas_exposes_global_and_focused_scope_without_copying_nodes():
    canvas = default_canvas("interaction-test")
    interaction = interaction_payload(canvas)
    scope_ids = {scope["id"] for scope in interaction["scopes"]}
    assert {"scope-global", "scope-current-inquiry"}.issubset(scope_ids)

    global_projection = scope_projection(canvas, "scope-global")
    focused_projection = scope_projection(canvas, "scope-current-inquiry")
    assert len(global_projection["nodes"]) == len(canvas["nodes"])
    assert 0 < len(focused_projection["nodes"]) < len(global_projection["nodes"])
    assert all(node in canvas["nodes"] for node in focused_projection["nodes"])


def test_command_proposal_requires_resolution_before_future_application():
    canvas = default_canvas("command-test")
    node_ids_before = [node["id"] for node in canvas["nodes"]]
    proposal = create_command_proposal(
        canvas,
        {
            "title": "Rename a research note",
            "action": "patch_node",
            "scope_id": "scope-current-inquiry",
            "target_node_ids": ["node-source"],
            "arguments": {"title": "Updated note"},
        },
    )
    assert proposal["status"] == "proposed"
    resolved = resolve_command_proposal(canvas, proposal["id"], "approved")
    assert resolved["status"] == "approved"
    assert [node["id"] for node in canvas["nodes"]] == node_ids_before


def test_revision_preconditions_detect_concurrent_graph_edits():
    canvas = default_canvas("revision-test")
    assert_expected_revision(canvas, 0)
    record_graph_event(canvas, "node.created", {"node_id": "future-node"})
    try:
        assert_expected_revision(canvas, 0)
    except RevisionConflict as exc:
        assert "current revision is 1" in str(exc)
    else:
        raise AssertionError("Expected an out-of-date graph revision to be rejected.")


def test_operation_node_uses_manifest_driven_definition():
    definitions = list_operation_definitions()
    assert any(item["id"] == "operation.transform" for item in definitions)
    node = normalize_node({"type": "operation"})
    assert node["config"]["definition_ref"]["id"] == "operation.transform"
    assert node["config"]["definition"]["tool_selector"]["selection_mode"] == "many"
