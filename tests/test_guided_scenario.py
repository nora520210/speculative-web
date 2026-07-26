from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory

from server.guided_scenario import generate_guided_scenarios
from server.graph_store import default_canvas, normalize_node, read_canvas, run_operation, write_canvas, write_projects
from server.operation_registry import get_operation_definition, list_operation_definitions


def test_guided_scenario_definition_declares_backend_executor_and_contracts():
    definition = get_operation_definition("operation.guided-scenario")
    assert definition is not None
    assert definition["execution"]["executor"] == "guided_scenario"
    assert definition["execution"]["tool_package_ids"] == ["dators-four-futures", "what-if"]
    assert definition["output_profiles"][0]["id"] == "branch-set"


def test_guided_scenario_definition_exposes_package_owned_chinese_display_copy():
    definition = get_operation_definition("operation.guided-scenario")
    assert definition is not None
    chinese = definition.get("locales", {}).get("zh", {})
    assert chinese["label"] == "引导情境"
    assert chinese["description"]
    assert chinese["ui"]["run_label"] == "生成四条情境"


def test_operation_definitions_expose_package_owned_chinese_display_copy():
    definitions = list_operation_definitions()
    assert definitions
    for definition in definitions:
        chinese = definition.get("locales", {}).get("zh", {})
        assert chinese.get("label")
        assert chinese.get("description")


def test_guided_scenario_fallback_keeps_four_future_contract_visible():
    original = os.environ.get("SPEC_WEB_ENABLE_OPENAI_RUNS")
    os.environ["SPEC_WEB_ENABLE_OPENAI_RUNS"] = "0"
    try:
        result = generate_guided_scenarios(
            [{"id": "source", "title": "Research", "text": "研究公共空间中的多人语音识别与拒绝权。"}],
            [],
        )
    finally:
        if original is None:
            os.environ.pop("SPEC_WEB_ENABLE_OPENAI_RUNS", None)
        else:
            os.environ["SPEC_WEB_ENABLE_OPENAI_RUNS"] = original

    assert result["model_snapshot"]["fallback_used"] is True
    assert [branch["strategy"] for branch in result["branches"]] == [
        "growth",
        "collapse",
        "discipline",
        "transformation",
    ]
    for branch in result["branches"]:
        assert branch["what_if"]
        assert len(branch["key_actors"]) >= 2
        assert len(branch["facilitation"]["role_prompts"]) >= 2
        assert len(branch["facilitation"]["summary_lenses"]) >= 3


def test_guided_scenario_run_materializes_isolated_branch_scopes():
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
                [{"id": "project-a", "title": "A", "status": "active", "updated_at": "now", "node_count": 0, "canvas_id": "project-a"}]
            )
            canvas = default_canvas("project-a")
            operation = normalize_node(
                {
                    "id": "node-guided-scenario",
                    "type": "operation",
                    "config": {"definition_ref": {"id": "operation.guided-scenario"}},
                }
            )
            canvas["nodes"].append(operation)
            canvas["edges"].append(
                {
                    "id": "edge-source-guided",
                    "source_node_id": "node-source",
                    "target_node_id": operation["id"],
                    "source_port": "out",
                    "target_port": "research",
                    "edge_kind": "data",
                    "created_at": "now",
                }
            )
            write_canvas("project-a", canvas)

            result = run_operation("project-a", operation["id"])
            saved = read_canvas("project-a")

            assert result["run"]["status"] == "succeeded"
            assert result["run"]["context_snapshot"]["operation_definition"]["id"] == "operation.guided-scenario"
            assert [tool["id"] for tool in result["run"]["context_snapshot"]["tool_snapshot"]] == [
                "dators-four-futures",
                "what-if",
            ]
            assert len(result["output_nodes"]) == 4
            assert len(result["scopes"]) == 4
            assert len(result["edges"]) == 4
            assert all(node["produced_by_run_id"] == result["run"]["id"] for node in result["output_nodes"])
            assert all(scope["mode"] == "snapshot" for scope in result["scopes"])
            assert all("node-source" in scope["snapshot_node_ids"] for scope in result["scopes"])
            assert any(event["type"] == "operation.guided_scenario.completed" for event in saved["events"])
    finally:
        if original_openai_runs is None:
            os.environ.pop("SPEC_WEB_ENABLE_OPENAI_RUNS", None)
        else:
            os.environ["SPEC_WEB_ENABLE_OPENAI_RUNS"] = original_openai_runs
        graph_store.DATA_DIR = original_data_dir
        graph_store.PROJECTS_FILE = original_projects_file
        graph_store.CANVAS_DIR = original_canvas_dir
