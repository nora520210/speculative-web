from server.graph_store import default_canvas, normalize_node
from server.interaction_runtime import (
    RevisionConflict,
    append_message,
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


def test_default_demo_thread_uses_the_same_start_stage_as_the_conversation_guide():
    canvas = default_canvas("guide-entry-test")
    session = canvas["conversation_sessions"][0]

    assert session["guide"]["kind"] == "four_futures"
    assert session["guide"]["stage_id"] == "start"
    assert session["active_scope_id"] == "scope-global"
    assert session["progress"] == [
        {
            "id": "step-start",
            "label": "Start inquiry",
            "scope_id": "scope-global",
            "status": "active",
            "workflow_stage_id": "start",
        }
    ]
    assert session["messages"][1]["kind"] == "guide"
    assert "Research Brief" in session["messages"][1]["body"]


def test_system_and_assistant_feedback_is_capped_without_truncating_user_research_input():
    canvas = default_canvas("feedback-cap-test")
    session_id = canvas["conversation_sessions"][0]["id"]
    long_feedback = "f" * 240
    long_input = "u" * 240

    feedback = append_message(canvas, session_id, {"role": "assistant", "body": long_feedback})
    user_input = append_message(canvas, session_id, {"role": "user", "body": long_input})

    assert len(feedback["body"]) == 200
    assert feedback["body"].endswith("…")
    assert user_input["body"] == long_input


def test_interaction_payload_compacts_legacy_system_feedback():
    canvas = default_canvas("legacy-feedback-cap-test")
    canvas["conversation_sessions"][0]["messages"][1]["body"] = "s" * 240

    interaction = interaction_payload(canvas)
    message = interaction["conversation_sessions"][0]["messages"][1]

    assert len(message["body"]) == 200
    assert message["body"].endswith("…")


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
