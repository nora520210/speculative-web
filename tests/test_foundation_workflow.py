from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory

from server.graph_store import (
    default_canvas,
    read_canvas,
    run_operation,
    select_four_futures_branch,
    start_four_futures_workflow,
    update_node,
    write_canvas,
    write_projects,
)
from server.workflow_registry import get_workflow_definition, list_workflow_definitions


def test_four_futures_workflow_definition_is_a_backend_owned_sequence():
    definition = get_workflow_definition("workflow.four-futures-foundation")
    assert definition is not None
    assert definition["package_path"] == "workflow_definitions/four-futures-foundation"
    assert definition["start_input"]["required"] == ["start_mode", "topic"]
    assert [stage["id"] for stage in definition["stages"]] == [
        "input",
        "four_futures",
        "tools",
        "scenario",
    ]
    assert definition["stages"][1]["operation_definition_id"] == "operation.guided-scenario"
    assert definition["runtime"]["branch_selection_mode"] == "exactly_one"
    assert definition["runtime"]["rerun_policy"] == "supersede_previous_active_line"
    assert definition["discussion_tool_policy"]["minimum_selected"] == 1
    assert definition["discussion_tool_policy"]["recommended_by_branch"]["growth"] == ["futures-wheel"]
    assert definition["discussion_tool_policy"]["recommended_by_branch"]["discipline"] == ["future-triangle"]
    assert definition["locales"]["zh"]["stages"]["four_futures"]["label"] == "四个 What-if"
    assert all(item["package_path"].startswith("workflow_definitions/") for item in list_workflow_definitions())


def test_four_futures_foundation_lifecycle_uses_scopes_without_copying_graphs():
    import server.graph_store as graph_store

    original_openai_runs = os.environ.get("SPEC_WEB_ENABLE_OPENAI_RUNS")
    original_data_dir = graph_store.DATA_DIR
    original_projects_file = graph_store.PROJECTS_FILE
    original_canvas_dir = graph_store.CANVAS_DIR
    os.environ["SPEC_WEB_ENABLE_OPENAI_RUNS"] = "0"
    try:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
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

            started = start_four_futures_workflow(
                "project-a",
                {
                    "definition_id": "workflow.four-futures-foundation",
                    "start_mode": "research",
                    "topic": "公共空间中的自动语音识别与拒绝权",
                    "assumptions": ["便利优先"],
                    "stakeholders": ["路人", "管理者"],
                    "tensions": ["安全与沉默"],
                },
            )
            workflow_id = started["workflow"]["id"]
            saved = read_canvas("project-a")
            workflow = next(item for item in saved["workflow_instances"] if item["id"] == workflow_id)
            session = next(item for item in saved["conversation_sessions"] if item["id"] == workflow["session_id"])

            assert workflow["operation_node_id"] == started["nodes"][2]["id"]
            assert workflow["source_node_ids"] == [started["nodes"][0]["id"], started["nodes"][1]["id"]]
            assert workflow["definition_snapshot"]["id"] == "workflow.four-futures-foundation"
            assert [stage["id"] for stage in workflow["definition_snapshot"]["stages"]] == [
                "input",
                "four_futures",
                "tools",
                "scenario",
            ]
            assert workflow["definition_snapshot"]["locales"]["zh"]["stages"]["scenario"]["label"] == "生成情境"
            assert workflow["status"] == "active"
            assert workflow["stage"] == "four_futures"
            assert [step["workflow_stage_id"] for step in session["progress"]] == [
                "input",
                "four_futures",
                "tools",
                "scenario",
            ]
            assert not saved["runs"]

            completed = run_operation("project-a", workflow["operation_node_id"])
            saved = read_canvas("project-a")
            workflow = next(item for item in saved["workflow_instances"] if item["id"] == workflow_id)
            session = next(item for item in saved["conversation_sessions"] if item["id"] == workflow["session_id"])

            assert completed["workflow"]["id"] == workflow_id
            assert workflow["status"] == "awaiting_selection"
            assert workflow["stage"] == "four_futures"
            assert len(workflow["branch_node_ids"]) == 4
            branch_nodes = [node for node in saved["nodes"] if node["id"] in workflow["branch_node_ids"]]
            assert all(node["payload"].get("image_status") == "pending" for node in branch_nodes)
            assert all(not node["payload"].get("image_url") for node in branch_nodes)
            comparison_scope = next(item for item in saved["scopes"] if item["id"] == workflow["comparison_scope_id"])
            assert comparison_scope["mode"] == "snapshot"
            assert set(workflow["branch_node_ids"]).issubset(comparison_scope["snapshot_node_ids"])
            assert session["active_scope_id"] == comparison_scope["id"]
            assert next(step for step in session["progress"] if step["workflow_stage_id"] == "four_futures")["status"] == "active"

            selected_branch_id = workflow["branch_node_ids"][0]
            selected = select_four_futures_branch(
                "project-a",
                workflow_id,
                {"branch_node_id": selected_branch_id},
            )
            saved = read_canvas("project-a")
            workflow = next(item for item in saved["workflow_instances"] if item["id"] == workflow_id)
            session = next(item for item in saved["conversation_sessions"] if item["id"] == workflow["session_id"])

            assert selected["scope_id"] == workflow["branch_scope_ids"][selected_branch_id]
            assert workflow["status"] == "tools"
            assert workflow["selected_branch_node_id"] == selected_branch_id
            assert workflow["discussion_node_id"] == selected["discussion_node"]["id"]
            discussion_node = next(node for node in saved["nodes"] if node["id"] == workflow["discussion_node_id"])
            branch_scope = next(item for item in saved["scopes"] if item["id"] == selected["scope_id"])
            assert discussion_node["id"] in branch_scope["snapshot_node_ids"]
            assert discussion_node["config"]["selection_policy"]["minimum_selected"] == 1
            assert not any(tool["selected"] for tool in discussion_node["config"]["tools"])
            assert session["active_scope_id"] == selected["scope_id"]
            assert next(step for step in session["progress"] if step["workflow_stage_id"] == "tools")["status"] == "active"

            update_node(
                "project-a",
                workflow["source_node_ids"][0],
                {"payload": {"text": "已更新的研究简报"}},
            )
            saved = read_canvas("project-a")
            workflow = next(item for item in saved["workflow_instances"] if item["id"] == workflow_id)
            branch_nodes = [node for node in saved["nodes"] if node["id"] in workflow["branch_node_ids"]]
            source = next(node for node in saved["nodes"] if node["id"] == workflow["source_node_ids"][0])
            keywords = next(node for node in saved["nodes"] if node["id"] == workflow["keyword_node_id"])
            session = next(item for item in saved["conversation_sessions"] if item["id"] == workflow["session_id"])

            assert workflow["status"] == "stale"
            assert workflow["stage"] == "stale"
            assert all(node["status"] == "stale" for node in branch_nodes)
            assert source["payload"]["workflow_brief_status"] == "superseded_by_direct_text"
            assert keywords["payload"]["keywords"] == ["已更新的研究简报"]
            assert session["active_scope_id"] == "scope-global"
            assert session["guide"]["stage_id"] == "stale"
            assert any(
                message.get("state") == "superseded"
                and selected_branch_id in message.get("related_node_ids", [])
                for message in session["messages"]
            )
            try:
                select_four_futures_branch(
                    "project-a",
                    workflow_id,
                    {"branch_node_id": selected_branch_id},
                )
            except ValueError as exc:
                assert "Re-run the four futures" in str(exc)
            else:
                raise AssertionError("Stale workflow branches must not be selectable.")
    finally:
        if original_openai_runs is None:
            os.environ.pop("SPEC_WEB_ENABLE_OPENAI_RUNS", None)
        else:
            os.environ["SPEC_WEB_ENABLE_OPENAI_RUNS"] = original_openai_runs
        graph_store.DATA_DIR = original_data_dir
        graph_store.PROJECTS_FILE = original_projects_file
        graph_store.CANVAS_DIR = original_canvas_dir
