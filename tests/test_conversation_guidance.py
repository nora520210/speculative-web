from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory

from server.graph_store import (
    _activity_session,
    add_edge,
    advance_conversation_guide,
    default_canvas,
    delete_node,
    read_canvas,
    run_operation,
    select_four_futures_branch,
    update_node,
    write_canvas,
    write_projects,
)
from server.interaction_runtime import create_conversation


def _temporary_project():
    import server.graph_store as graph_store

    tmp = TemporaryDirectory()
    tmp_path = Path(tmp.name)
    original = (graph_store.DATA_DIR, graph_store.PROJECTS_FILE, graph_store.CANVAS_DIR)
    graph_store.DATA_DIR = tmp_path
    graph_store.PROJECTS_FILE = tmp_path / "projects.json"
    graph_store.CANVAS_DIR = tmp_path / "canvases"
    graph_store.ensure_store_light()
    write_projects(
        [
            {
                "id": "project-a",
                "title": "A",
                "status": "active",
                "updated_at": "now",
                "node_count": 0,
                "canvas_id": "project-a",
            }
        ]
    )
    write_canvas("project-a", default_canvas("project-a"))
    return tmp, graph_store, original


def _restore_project(tmp, graph_store, original) -> None:
    graph_store.DATA_DIR, graph_store.PROJECTS_FILE, graph_store.CANVAS_DIR = original
    tmp.cleanup()


def _finish_guided_frame(session_id: str) -> dict:
    advance_conversation_guide("project-a", session_id, {"action": "begin", "body": "城市里的自动语音系统"})
    advance_conversation_guide("project-a", session_id, {"action": "answer", "body": "公共空间中的拒绝权"})
    advance_conversation_guide("project-a", session_id, {"action": "answer", "body": "便利优先\n持续监听"})
    advance_conversation_guide("project-a", session_id, {"action": "answer", "body": "路人\n管理者"})
    return advance_conversation_guide("project-a", session_id, {"action": "answer", "body": "安全与沉默"})


def test_conversation_guide_updates_canonical_nodes_without_tool_configuration():
    tmp, graph_store, original = _temporary_project()
    try:
        canvas = read_canvas("project-a")
        session_id = canvas["conversation_sessions"][0]["id"]
        completed = _finish_guided_frame(session_id)
        workflow = completed["workflow"]
        saved = read_canvas("project-a")
        source = next(node for node in saved["nodes"] if node["id"] == workflow["source_node_ids"][0])
        keywords = next(node for node in saved["nodes"] if node["id"] == workflow["keyword_node_id"])
        session = next(item for item in saved["conversation_sessions"] if item["id"] == session_id)

        assert source["payload"]["workflow_brief"]["topic"] == "城市里的自动语音系统"
        assert "公共空间中的拒绝权" in source["payload"]["text"]
        assert "安全与沉默" in keywords["payload"]["text"]
        assert session["guide"]["stage_id"] == "keywords"
        assert "tools" not in session["guide"]
        assert "tool" not in workflow

        advance_conversation_guide("project-a", session_id, {"action": "confirm_keywords"})
        saved = read_canvas("project-a")
        workflow = next(item for item in saved["workflow_instances"] if item["id"] == workflow["id"])
        assert workflow["stage"] == "four_futures"
        assert not saved["runs"]
    finally:
        _restore_project(tmp, graph_store, original)


def test_deleting_a_selected_branch_invalidates_workflow_and_records_activity():
    original_runs = os.environ.get("SPEC_WEB_ENABLE_OPENAI_RUNS")
    os.environ["SPEC_WEB_ENABLE_OPENAI_RUNS"] = "0"
    tmp, graph_store, original = _temporary_project()
    try:
        canvas = read_canvas("project-a")
        session_id = canvas["conversation_sessions"][0]["id"]
        workflow = _finish_guided_frame(session_id)["workflow"]
        advance_conversation_guide("project-a", session_id, {"action": "confirm_keywords"})
        run_operation("project-a", workflow["operation_node_id"])
        saved = read_canvas("project-a")
        workflow = next(item for item in saved["workflow_instances"] if item["id"] == workflow["id"])
        branch_id = workflow["branch_node_ids"][0]
        select_four_futures_branch("project-a", workflow["id"], {"branch_node_id": branch_id})
        delete_node("project-a", branch_id, session_id=session_id)

        saved = read_canvas("project-a")
        workflow = next(item for item in saved["workflow_instances"] if item["id"] == workflow["id"])
        session = next(item for item in saved["conversation_sessions"] if item["id"] == session_id)
        assert workflow["status"] == "stale"
        assert workflow["selected_branch_node_id"] == ""
        assert session["guide"]["stage_id"] == "stale"
        assert any(message["kind"] == "activity" and "Deleted" in message["body"] for message in session["messages"])

        rerun = run_operation("project-a", workflow["operation_node_id"])
        assert rerun["workflow"]["status"] == "awaiting_selection"
        assert len(rerun["output_nodes"]) == 4
    finally:
        if original_runs is None:
            os.environ.pop("SPEC_WEB_ENABLE_OPENAI_RUNS", None)
        else:
            os.environ["SPEC_WEB_ENABLE_OPENAI_RUNS"] = original_runs
        _restore_project(tmp, graph_store, original)


def test_direct_input_edge_change_blocks_mismatched_workflow_run():
    tmp, graph_store, original = _temporary_project()
    try:
        canvas = read_canvas("project-a")
        session_id = canvas["conversation_sessions"][0]["id"]
        workflow = _finish_guided_frame(session_id)["workflow"]
        advance_conversation_guide("project-a", session_id, {"action": "confirm_keywords"})
        extra = canvas["nodes"][0]
        add_edge(
            "project-a",
            {
                "source_node_id": extra["id"],
                "target_node_id": workflow["operation_node_id"],
                "target_port": "research",
                "edge_kind": "data",
            },
            session_id=session_id,
        )
        saved = read_canvas("project-a")
        workflow = next(item for item in saved["workflow_instances"] if item["id"] == workflow["id"])
        assert workflow["status"] == "stale"
        try:
            run_operation("project-a", workflow["operation_node_id"])
        except ValueError as exc:
            assert "no longer match" in str(exc)
        else:
            raise AssertionError("A workflow with changed data edges must not run with a different input set.")
    finally:
        _restore_project(tmp, graph_store, original)


def test_direct_brief_edit_rebuilds_keywords_and_resets_the_session_scope():
    original_runs = os.environ.get("SPEC_WEB_ENABLE_OPENAI_RUNS")
    os.environ["SPEC_WEB_ENABLE_OPENAI_RUNS"] = "0"
    tmp, graph_store, original = _temporary_project()
    try:
        canvas = read_canvas("project-a")
        session_id = canvas["conversation_sessions"][0]["id"]
        workflow = _finish_guided_frame(session_id)["workflow"]
        advance_conversation_guide("project-a", session_id, {"action": "confirm_keywords"})
        run_operation("project-a", workflow["operation_node_id"])
        saved = read_canvas("project-a")
        workflow = next(item for item in saved["workflow_instances"] if item["id"] == workflow["id"])
        select_four_futures_branch(
            "project-a",
            workflow["id"],
            {"branch_node_id": workflow["branch_node_ids"][0]},
        )

        source_id = workflow["source_node_ids"][0]
        update_node(
            "project-a",
            source_id,
            {"payload": {"text": "Topic: 老年照护中的环境感知\nCore tension: 便利与自主"}},
            session_id=session_id,
        )

        saved = read_canvas("project-a")
        workflow = next(item for item in saved["workflow_instances"] if item["id"] == workflow["id"])
        source = next(node for node in saved["nodes"] if node["id"] == source_id)
        keywords = next(node for node in saved["nodes"] if node["id"] == workflow["keyword_node_id"])
        session = next(item for item in saved["conversation_sessions"] if item["id"] == session_id)
        invalidation = next(
            message
            for message in reversed(session["messages"])
            if message["kind"] == "activity" and message.get("activity", {}).get("type") == "workflow.invalidated"
        )

        assert source["payload"].get("workflow_brief") is None
        assert source["payload"]["workflow_brief_status"] == "superseded_by_direct_text"
        assert keywords["payload"]["keywords"] == ["老年照护中的环境感知", "便利与自主"]
        assert workflow["status"] == "stale"
        assert session["active_scope_id"] == "scope-global"
        assert session["guide"]["stage_id"] == "stale"
        assert {source_id, keywords["id"]}.issubset(set(invalidation["related_node_ids"]))

        rerun = run_operation("project-a", workflow["operation_node_id"])
        assert rerun["workflow"]["status"] == "awaiting_selection"
    finally:
        if original_runs is None:
            os.environ.pop("SPEC_WEB_ENABLE_OPENAI_RUNS", None)
        else:
            os.environ["SPEC_WEB_ENABLE_OPENAI_RUNS"] = original_runs
        _restore_project(tmp, graph_store, original)


def test_operation_edges_require_declared_manifest_ports():
    tmp, graph_store, original = _temporary_project()
    try:
        canvas = read_canvas("project-a")
        session_id = canvas["conversation_sessions"][0]["id"]
        workflow = _finish_guided_frame(session_id)["workflow"]
        extra = canvas["nodes"][0]
        try:
            add_edge(
                "project-a",
                {
                    "source_node_id": extra["id"],
                    "target_node_id": workflow["operation_node_id"],
                    "target_port": "in",
                    "edge_kind": "data",
                },
                session_id=session_id,
            )
        except ValueError as exc:
            assert "does not expose" in str(exc)
        else:
            raise AssertionError("An operation must reject a data edge on an undeclared manifest port.")

        saved = read_canvas("project-a")
        assert not any(
            edge["target_node_id"] == workflow["operation_node_id"] and edge["target_port"] == "in"
            for edge in saved["edges"]
        )
    finally:
        _restore_project(tmp, graph_store, original)


def test_unspecified_graph_activity_never_targets_an_arbitrary_active_conversation():
    canvas = default_canvas("ambiguous-activity")
    create_conversation(canvas, {"title": "Second thread"})

    assert _activity_session(canvas) is None
