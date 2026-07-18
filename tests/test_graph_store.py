from pathlib import Path
from tempfile import TemporaryDirectory
import os

from server.graph_store import (
    build_modify_prompt,
    build_text_block_repair_prompt,
    delete_project,
    default_canvas,
    delete_edge,
    delete_node,
    input_modalities_for_nodes,
    infer_response_language,
    image_prompt_for_output,
    visual_basis_from_parsed_output,
    ordered_data_input_edges,
    recommend_output_for_modify,
    run_modify,
    normalize_text_blocks,
    normalize_node,
    update_project,
    valid_text_blocks,
    write_canvas,
)
from server.modifier_registry import recommend_output, tool_snapshot


def test_default_canvas_has_modify_and_edges():
    canvas = default_canvas("test-project")
    assert any(node["type"] == "modify" for node in canvas["nodes"])
    assert any(edge["edge_kind"] == "data" for edge in canvas["edges"])


def test_modify_recommendation_prefers_multimodal_for_physical_fiction():
    canvas = default_canvas("test-project")
    modify = next(node for node in canvas["nodes"] if node["type"] == "modify")
    recommendation = recommend_output_for_modify(modify)
    assert recommendation["type"] == "multimodal"


def test_modify_prompt_carries_tool_owned_text_block_forms():
    canvas = default_canvas("test-project")
    prompt = build_modify_prompt(
        canvas,
        ["node-source"],
        tool_snapshot(["what-if", "futures-wheel"]),
        "text",
        recommend_output(["what-if", "futures-wheel"]),
    )
    assert "text_output_forms" in prompt
    assert "condition card, everyday vignette" in prompt
    assert "three-order consequence ledger" in prompt
    assert "Tables must be structured arrays" in prompt
    assert "Do not expect the user to write a design-fiction brief" in prompt
    assert "Keep the response concise" in prompt
    assert "output_budget" in prompt
    assert "visual_basis" in prompt


def test_image_prompt_requires_direct_conclusion_and_evidence():
    prompt, basis = image_prompt_for_output(
        {
            "image_prompt": "A tendon-driven wrist beside an inspectable consent dial.",
            "visual_basis": {
                "conclusion_text": "Contact accountability becomes a first-class hardware constraint.",
                "evidence_node_ids": ["source", "not-direct"],
                "reference_image_node_ids": ["image-source"],
            },
        },
        "",
        "image",
        ["source", "image-source"],
        [{"node_id": "image-source", "image_url": "/uploads/reference.png"}],
    )
    assert "tendon-driven wrist" in prompt
    assert basis["evidence_node_ids"] == ["source"]
    assert basis["reference_image_node_ids"] == ["image-source"]

    missing_prompt, missing_basis = image_prompt_for_output(
        {"image_prompt": "An unsupported object."},
        "",
        "image",
        ["source"],
        [],
    )
    assert missing_prompt == ""
    assert missing_basis["evidence_node_ids"] == []


def test_image_prompt_recovers_flattened_visual_basis_fields():
    prompt, basis = image_prompt_for_output(
        {
            "image_prompt": "An inspectable tendon-driven contact audit wrist cuff.",
            "visual_basis": "{",
            "conclusion_text": "Contact logging changes who can interrupt a household robot.",
            "evidence_node_ids": '["source"]',
            "reference_image_node_ids": '["image-source"]',
        },
        "",
        "multimodal",
        ["source", "image-source"],
        [{"node_id": "image-source", "image_url": "/uploads/reference.png"}],
    )
    assert "contact audit wrist cuff" in prompt
    assert basis["evidence_node_ids"] == ["source"]
    assert basis["reference_image_node_ids"] == ["image-source"]


def test_response_language_is_inferred_from_research_input():
    assert infer_response_language([{"text": "团队研究闭环生命支持和深空航行中的微生物生态。"}]) == "Chinese"
    assert infer_response_language([{"text": "The team studies bioregenerative life support."}]) == "the dominant language of the direct input"


def test_text_block_repair_prompt_uses_tool_forms_and_validates_blocks():
    snapshot = tool_snapshot(["what-if", "futures-wheel"])
    prompt = build_text_block_repair_prompt(snapshot, "A short speculative source output.")
    assert "condition card, everyday vignette" in prompt
    assert "three-order consequence ledger" in prompt
    assert valid_text_blocks(
        [
            {"type": "callout", "title": "Premise", "text": "A changed rule."},
            {"type": "table", "title": "Effects", "columns": ["Order"], "rows": [["First"]]},
            {"type": "questions", "title": "Open questions", "items": ["Who decides?"]},
        ]
    )
    assert not valid_text_blocks("not a block list")


def test_normalize_text_blocks_decodes_model_stringified_block_array():
    blocks = normalize_text_blocks('[{"type": "questions", "title": "Questions", "items": ["Who decides?"]}]')
    assert valid_text_blocks(blocks)


def test_update_project_renames_canvas_record():
    import server.graph_store as graph_store

    original_data_dir = graph_store.DATA_DIR
    original_projects_file = graph_store.PROJECTS_FILE
    original_canvas_dir = graph_store.CANVAS_DIR
    with TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        graph_store.DATA_DIR = tmp_path
        graph_store.PROJECTS_FILE = tmp_path / "projects.json"
        graph_store.CANVAS_DIR = tmp_path / "canvases"
        graph_store.ensure_store_light()
        graph_store.write_projects(
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
        project = update_project("project-a", {"title": "Renamed Canvas"})
        assert project["title"] == "Renamed Canvas"
        assert graph_store.read_projects()[0]["title"] == "Renamed Canvas"
    graph_store.DATA_DIR = original_data_dir
    graph_store.PROJECTS_FILE = original_projects_file
    graph_store.CANVAS_DIR = original_canvas_dir


def test_delete_project_removes_project_and_canvas_file():
    import server.graph_store as graph_store

    original_data_dir = graph_store.DATA_DIR
    original_projects_file = graph_store.PROJECTS_FILE
    original_canvas_dir = graph_store.CANVAS_DIR
    original_generated_image_dir = graph_store.GENERATED_IMAGE_DIR
    with TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        graph_store.DATA_DIR = tmp_path
        graph_store.PROJECTS_FILE = tmp_path / "projects.json"
        graph_store.CANVAS_DIR = tmp_path / "canvases"
        graph_store.GENERATED_IMAGE_DIR = tmp_path / "generated"
        graph_store.ensure_store_light()
        graph_store.write_projects(
            [{"id": "project-a", "title": "A", "status": "active", "updated_at": "now", "node_count": 0, "canvas_id": "project-a"}]
        )
        write_canvas("project-a", default_canvas("project-a"))
        graph_store.GENERATED_IMAGE_DIR.mkdir()
        image_path = graph_store.GENERATED_IMAGE_DIR / "project-a-run-1.png"
        image_path.write_bytes(b"test-image")
        result = delete_project("project-a")
        assert result["project"]["id"] == "project-a"
        assert graph_store.read_projects() == []
        assert not graph_store.canvas_file("project-a").exists()
        assert not image_path.exists()
    graph_store.DATA_DIR = original_data_dir
    graph_store.PROJECTS_FILE = original_projects_file
    graph_store.CANVAS_DIR = original_canvas_dir
    graph_store.GENERATED_IMAGE_DIR = original_generated_image_dir


def test_run_modify_creates_output():
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
            graph_store.write_projects(
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
            result = run_modify("project-a", "node-modify")
            assert result["run"]["status"] == "succeeded"
            assert result["run"]["model_snapshot"]["provider"] == "placeholder"
            assert result["run"]["context_snapshot"]["output_recommendation"]["type"] == "multimodal"
            assert result["output_node"]["produced_by_run_id"] == result["run"]["id"]
    finally:
        if original_openai_runs is None:
            os.environ.pop("SPEC_WEB_ENABLE_OPENAI_RUNS", None)
        else:
            os.environ["SPEC_WEB_ENABLE_OPENAI_RUNS"] = original_openai_runs
        graph_store.DATA_DIR = original_data_dir
        graph_store.PROJECTS_FILE = original_projects_file
        graph_store.CANVAS_DIR = original_canvas_dir


def test_invalid_node_type_is_rejected():
    import server.graph_store as graph_store

    try:
        graph_store.normalize_node({"type": "unknown-tool"})
    except ValueError as exc:
        assert "Unsupported node type" in str(exc)
    else:
        raise AssertionError("Expected invalid node type to be rejected.")


def test_upload_node_is_text_modality_context():
    node = normalize_node({"type": "upload", "payload": {"text": "Extracted uploaded document text."}})
    canvas = {"nodes": [node], "edges": []}
    assert node["title"] == "Upload"
    assert input_modalities_for_nodes(canvas, [node["id"]]) == ["text"]


def test_delete_node_removes_attached_edges():
    import server.graph_store as graph_store

    original_data_dir = graph_store.DATA_DIR
    original_projects_file = graph_store.PROJECTS_FILE
    original_canvas_dir = graph_store.CANVAS_DIR
    with TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        graph_store.DATA_DIR = tmp_path
        graph_store.PROJECTS_FILE = tmp_path / "projects.json"
        graph_store.CANVAS_DIR = tmp_path / "canvases"
        graph_store.ensure_store_light()
        graph_store.write_projects(
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
        result = delete_node("project-a", "node-modify")
        canvas = graph_store.read_canvas("project-a")
        assert result["node"]["id"] == "node-modify"
        assert "edge-source-modify" in result["removed_edges"]
        assert all(edge["source_node_id"] != "node-modify" for edge in canvas["edges"])
        assert all(edge["target_node_id"] != "node-modify" for edge in canvas["edges"])
    graph_store.DATA_DIR = original_data_dir
    graph_store.PROJECTS_FILE = original_projects_file
    graph_store.CANVAS_DIR = original_canvas_dir


def test_delete_edge_removes_only_that_edge():
    import server.graph_store as graph_store

    original_data_dir = graph_store.DATA_DIR
    original_projects_file = graph_store.PROJECTS_FILE
    original_canvas_dir = graph_store.CANVAS_DIR
    with TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        graph_store.DATA_DIR = tmp_path
        graph_store.PROJECTS_FILE = tmp_path / "projects.json"
        graph_store.CANVAS_DIR = tmp_path / "canvases"
        graph_store.ensure_store_light()
        graph_store.write_projects(
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
        result = delete_edge("project-a", "edge-source-modify")
        canvas = graph_store.read_canvas("project-a")
        assert result["edge"]["id"] == "edge-source-modify"
        assert all(edge["id"] != "edge-source-modify" for edge in canvas["edges"])
        assert any(edge["id"] == "edge-conversation-modify" for edge in canvas["edges"])
    graph_store.DATA_DIR = original_data_dir
    graph_store.PROJECTS_FILE = original_projects_file
    graph_store.CANVAS_DIR = original_canvas_dir


def test_ordered_data_input_edges_follow_connection_creation_order():
    canvas = default_canvas("test-project")
    for edge in canvas["edges"]:
        if edge["id"] == "edge-source-modify":
            edge["created_at"] = "2026-07-09T00:00:01+00:00"
    canvas["edges"].extend(
        [
            {
                "id": "edge-late",
                "source_node_id": "node-image",
                "target_node_id": "node-modify",
                "source_port": "out",
                "target_port": "in",
                "edge_kind": "data",
                "created_at": "2026-07-09T00:00:03+00:00",
            },
            {
                "id": "edge-early",
                "source_node_id": "node-conversation",
                "target_node_id": "node-modify",
                "source_port": "out",
                "target_port": "in",
                "edge_kind": "data",
                "created_at": "2026-07-09T00:00:02+00:00",
            },
        ]
    )
    edge_ids = [edge["id"] for edge in ordered_data_input_edges(canvas, "node-modify")]
    assert edge_ids == ["edge-source-modify", "edge-early", "edge-late"]


def test_invalid_edge_target_is_rejected():
    import server.graph_store as graph_store

    original_data_dir = graph_store.DATA_DIR
    original_projects_file = graph_store.PROJECTS_FILE
    original_canvas_dir = graph_store.CANVAS_DIR
    with TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        graph_store.DATA_DIR = tmp_path
        graph_store.PROJECTS_FILE = tmp_path / "projects.json"
        graph_store.CANVAS_DIR = tmp_path / "canvases"
        graph_store.ensure_store_light()
        graph_store.write_projects(
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
        try:
            graph_store.add_edge(
                "project-a",
                {
                    "source_node_id": "node-source",
                    "target_node_id": "missing-node",
                    "edge_kind": "data",
                },
            )
        except KeyError as exc:
            assert "Target node not found" in str(exc)
        else:
            raise AssertionError("Expected missing edge target to be rejected.")
    graph_store.DATA_DIR = original_data_dir
    graph_store.PROJECTS_FILE = original_projects_file
    graph_store.CANVAS_DIR = original_canvas_dir
