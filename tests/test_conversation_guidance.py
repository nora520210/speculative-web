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
    run_modify,
    run_operation,
    select_four_futures_branch,
    set_conversation_scope,
    start_four_futures_workflow,
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


def _finish_scenario_probe(session_id: str) -> dict:
    advance_conversation_guide("project-a", session_id, {"action": "begin_scenario"})
    advance_conversation_guide(
        "project-a",
        session_id,
        {"action": "scenario_answer", "body": "从一次人工复核中止开始"},
    )
    return advance_conversation_guide(
        "project-a",
        session_id,
        {"action": "scenario_answer", "body": "保留拒绝权与解释权冲突"},
    )


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
        assert session["guide"]["stage_id"] == "four_futures"
        assert "tools" not in session["guide"]
        assert "tool" not in workflow

        saved = read_canvas("project-a")
        workflow = next(item for item in saved["workflow_instances"] if item["id"] == workflow["id"])
        assert workflow["stage"] == "four_futures"
        assert not saved["runs"]
    finally:
        _restore_project(tmp, graph_store, original)


def test_guided_conversation_preserves_input_perspective_in_messages_and_brief():
    tmp, graph_store, original = _temporary_project()
    try:
        canvas = read_canvas("project-a")
        session_id = canvas["conversation_sessions"][0]["id"]
        advance_conversation_guide(
            "project-a",
            session_id,
            {"action": "begin", "body": "可穿戴材料进入护理场景", "input_perspective": "design"},
        )
        result = advance_conversation_guide(
            "project-a",
            session_id,
            {"action": "answer", "body": "材料行为与护理判断之间的边界", "input_perspective": "research"},
        )
        workflow = result["workflow"]
        saved = read_canvas("project-a")
        source = next(node for node in saved["nodes"] if node["id"] == workflow["source_node_ids"][0])
        brief = source["payload"]["workflow_brief"]
        session = next(item for item in saved["conversation_sessions"] if item["id"] == session_id)

        assert brief["input_sources"]["topic"] == "design"
        assert brief["input_sources"]["research_focus"] == "research"
        assert "研究议题 (设计师输入): 可穿戴材料进入护理场景" in source["payload"]["text"]
        assert "研究关注点 (科学家输入): 材料行为与护理判断之间的边界" in source["payload"]["text"]
        user_messages = [message for message in session["messages"] if message["role"] == "user"]
        assert [message["input_perspective"] for message in user_messages[-2:]] == ["design", "research"]
    finally:
        _restore_project(tmp, graph_store, original)


def test_preview_navigation_persists_guide_stage_with_scope():
    tmp, graph_store, original = _temporary_project()
    try:
        canvas = read_canvas("project-a")
        session_id = canvas["conversation_sessions"][0]["id"]
        workflow = _finish_guided_frame(session_id)["workflow"]

        updated = set_conversation_scope(
            "project-a",
            session_id,
            workflow["foundation_scope_id"],
            guide_stage_id="frame_focus",
        )
        saved = read_canvas("project-a")
        session = next(item for item in saved["conversation_sessions"] if item["id"] == session_id)

        assert updated["active_scope_id"] == workflow["foundation_scope_id"]
        assert updated["guide"]["stage_id"] == "frame_focus"
        assert updated["guide"]["pending_field"] == "research_focus"
        assert session["guide"]["stage_id"] == "frame_focus"
        assert session["guide"]["pending_field"] == "research_focus"
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
        removed_branch_messages = [
            message
            for message in session["messages"]
            if branch_id in message.get("related_node_ids", []) and message.get("state") == "removed"
        ]
        assert removed_branch_messages
        assert any(
            any(reference.get("id") == branch_id and reference.get("title") for reference in message.get("related_node_refs", []))
            for message in removed_branch_messages
        )

        rerun = run_operation("project-a", workflow["operation_node_id"])
        assert rerun["workflow"]["status"] == "awaiting_selection"
        assert len(rerun["output_nodes"]) == 4
    finally:
        if original_runs is None:
            os.environ.pop("SPEC_WEB_ENABLE_OPENAI_RUNS", None)
        else:
            os.environ["SPEC_WEB_ENABLE_OPENAI_RUNS"] = original_runs
        _restore_project(tmp, graph_store, original)


def test_selected_branch_adds_required_discussion_tool_node_without_preselecting_a_tool():
    original_runs = os.environ.get("SPEC_WEB_ENABLE_OPENAI_RUNS")
    os.environ["SPEC_WEB_ENABLE_OPENAI_RUNS"] = "0"
    tmp, graph_store, original = _temporary_project()
    try:
        canvas = read_canvas("project-a")
        session_id = canvas["conversation_sessions"][0]["id"]
        workflow = _finish_guided_frame(session_id)["workflow"]
        run_operation("project-a", workflow["operation_node_id"])
        saved = read_canvas("project-a")
        workflow = next(item for item in saved["workflow_instances"] if item["id"] == workflow["id"])
        branch_id = workflow["branch_node_ids"][0]

        selected = select_four_futures_branch("project-a", workflow["id"], {"branch_node_id": branch_id})
        saved = read_canvas("project-a")
        workflow = next(item for item in saved["workflow_instances"] if item["id"] == workflow["id"])
        discussion = next(node for node in saved["nodes"] if node["id"] == workflow["discussion_node_id"])
        branch_scope = next(item for item in saved["scopes"] if item["id"] == selected["scope_id"])

        assert selected["discussion_node"]["id"] == discussion["id"]
        assert discussion["type"] == "modify"
        assert discussion["config"]["selection_policy"]["minimum_selected"] == 1
        assert discussion["config"]["selection_policy"]["required_for"] == "workflow.tools"
        assert not any(tool["selected"] for tool in discussion["config"]["tools"])
        assert discussion["id"] in branch_scope["snapshot_node_ids"]
        assert any(
            edge["source_node_id"] == branch_id
            and edge["target_node_id"] == discussion["id"]
            and edge["edge_kind"] == "data"
            for edge in saved["edges"]
        )

        try:
            run_modify("project-a", discussion["id"])
        except ValueError as exc:
            assert "Select at least 1 discussion tool" in str(exc)
        else:
            raise AssertionError("Discussion should require an explicit tool choice.")

        selected_tools = [dict(tool) for tool in discussion["config"]["tools"]]
        selected_tools[0]["selected"] = True
        update_node(
            "project-a",
            discussion["id"],
            {"config": {"tools": selected_tools}},
            session_id=session_id,
        )
        updated = read_canvas("project-a")
        session = next(item for item in updated["conversation_sessions"] if item["id"] == session_id)
        assert any(
            message.get("activity", {}).get("type") == "workflow.discussion_tools_changed"
            for message in session["messages"]
        )

        try:
            run_modify("project-a", discussion["id"], session_id=session_id)
        except ValueError as exc:
            assert "scenario probing questions" in str(exc)
        else:
            raise AssertionError("Final scenario generation should wait for scenario probing answers.")

        started_probe = advance_conversation_guide("project-a", session_id, {"action": "begin_scenario"})
        assert started_probe["conversation"]["guide"]["stage_id"] == "scenario_probe"

        refined = advance_conversation_guide(
            "project-a",
            session_id,
            {"action": "scenario_answer", "body": "从一次人工复核中止开始"},
        )
        assert refined["conversation"]["guide"]["stage_id"] == "scenario_refine"

        ready = advance_conversation_guide(
            "project-a",
            session_id,
            {"action": "scenario_answer", "body": "保留拒绝权与解释权冲突"},
        )
        assert ready["conversation"]["guide"]["stage_id"] == "scenario_ready"
    finally:
        if original_runs is None:
            os.environ.pop("SPEC_WEB_ENABLE_OPENAI_RUNS", None)
        else:
            os.environ["SPEC_WEB_ENABLE_OPENAI_RUNS"] = original_runs
        _restore_project(tmp, graph_store, original)


def test_branch_reselection_and_tool_reruns_keep_one_current_scenario_line():
    original_runs = os.environ.get("SPEC_WEB_ENABLE_OPENAI_RUNS")
    os.environ["SPEC_WEB_ENABLE_OPENAI_RUNS"] = "0"
    tmp, graph_store, original = _temporary_project()
    try:
        started = start_four_futures_workflow(
            "project-a",
            {"start_mode": "research", "topic": "城市公共数据的退出权"},
        )
        workflow_id = started["workflow"]["id"]
        session_id = started["workflow"]["session_id"]
        run_operation("project-a", started["workflow"]["operation_node_id"])
        saved = read_canvas("project-a")
        workflow = next(item for item in saved["workflow_instances"] if item["id"] == workflow_id)
        first_branch, second_branch = workflow["branch_node_ids"][:2]
        selected = select_four_futures_branch("project-a", workflow_id, {"branch_node_id": first_branch})
        discussion = selected["discussion_node"]
        tools = [dict(tool) for tool in discussion["config"]["tools"]]
        tools[0]["selected"] = True
        update_node("project-a", discussion["id"], {"config": {"tools": tools}})
        _finish_scenario_probe(session_id)
        first_result = run_modify("project-a", discussion["id"], session_id=session_id)

        select_four_futures_branch("project-a", workflow_id, {"branch_node_id": second_branch})
        saved = read_canvas("project-a")
        workflow = next(item for item in saved["workflow_instances"] if item["id"] == workflow_id)
        old_output = next(node for node in saved["nodes"] if node["id"] == first_result["output_node"]["id"])
        assert workflow["status"] == "tools"
        assert workflow["selected_branch_node_id"] == second_branch
        assert workflow["active_scenario_node_id"] == ""
        assert old_output["status"] == "stale"
        assert not any(
            edge["source_node_id"] == first_branch and edge["target_node_id"] == discussion["id"] and edge["edge_kind"] == "data"
            for edge in saved["edges"]
        )
        assert any(
            edge["source_node_id"] == second_branch and edge["target_node_id"] == discussion["id"] and edge["edge_kind"] == "data"
            for edge in saved["edges"]
        )

        _finish_scenario_probe(session_id)
        second_result = run_modify("project-a", discussion["id"], session_id=session_id)
        saved = read_canvas("project-a")
        workflow = next(item for item in saved["workflow_instances"] if item["id"] == workflow_id)
        assert workflow["status"] == "complete"
        assert workflow["stage"] == "scenario"
        assert workflow["active_scenario_node_id"] == second_result["output_node"]["id"]
        assert sum(
            node["status"] != "stale"
            for node in saved["nodes"]
            if node.get("produced_by_run_id") in {first_result["run"]["id"], second_result["run"]["id"]}
        ) == 1
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
