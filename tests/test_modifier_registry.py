from pathlib import Path
from tempfile import TemporaryDirectory


def test_custom_tool_registry_preserves_contract_fields():
    import server.modifier_registry as registry

    original_file = registry.TOOL_REGISTRY_FILE
    original_package_dir = registry.TOOL_PACKAGE_DIR
    with TemporaryDirectory() as tmp:
        registry.TOOL_REGISTRY_FILE = Path(tmp) / "tool_registry.json"
        registry.TOOL_PACKAGE_DIR = Path(tmp) / "missing-packages"
        registry.TOOL_REGISTRY_FILE.write_text(
            """
            {
              "modifier_tools": [
                {
                  "id": "method-map",
                  "label": "Method Map",
                  "version": "1.2.0",
                  "accepted_modalities": ["text"],
                  "supported_outputs": ["text"],
                  "input_contract": {"required": ["research_note"]},
                  "output_contract": {"text": ["mapped_constraints"]},
                  "theory_mapping": {"family": "speculative design"},
                  "model_constraints": ["Return structured constraints."],
                  "text_output_forms": {"block_sequence": ["callout", "questions"]},
                  "executor": {"kind": "placeholder"},
                  "selected": true
                }
              ]
            }
            """,
            encoding="utf-8",
        )
        tools = registry.list_modifier_tools()
        method_map = next(tool for tool in tools if tool["id"] == "method-map")
        assert method_map["input_contract"]["required"] == ["research_note"]
        snapshot = registry.tool_snapshot(["method-map"])
        assert snapshot[0]["output_contract"]["text"] == ["mapped_constraints"]
        assert snapshot[0]["model_constraints"] == ["Return structured constraints."]
        assert snapshot[0]["text_output_forms"]["block_sequence"] == ["callout", "questions"]
    registry.TOOL_REGISTRY_FILE = original_file
    registry.TOOL_PACKAGE_DIR = original_package_dir


def test_tool_package_manifest_is_discoverable():
    import server.modifier_registry as registry

    tools = registry.list_modifier_tools()
    reductio = next(tool for tool in tools if tool["id"] == "reductio-ad-absurdum")
    assert reductio["label"] == "Reductio ad Absurdum"
    assert reductio["input_contract"]["required"] == ["accepted_claim_or_logic"]
    snapshot = registry.tool_snapshot(["cautionary-tales"])
    assert snapshot[0]["output_contract"]["text"][0] == "trend"
    assert "package_path" in snapshot[0]


def test_future_tool_packages_are_discoverable_with_recommendations():
    import server.modifier_registry as registry

    tools = {tool["id"]: tool for tool in registry.list_modifier_tools()}
    for tool_id in [
        "future-triangle",
        "futures-wheel",
        "dators-four-futures",
        "causal-layered-analysis",
        "experiential-futures-ladder",
        "envisioning-cards",
        "three-horizons",
    ]:
        assert tool_id in tools
        assert tools[tool_id]["package_path"].startswith("tool_packages/")

    ladder_recommendation = registry.recommend_output(["experiential-futures-ladder"])
    assert ladder_recommendation["type"] == "multimodal"
    mapping_recommendation = registry.recommend_output(["future-triangle"])
    assert mapping_recommendation["type"] == "text"


def test_text_recommended_packages_expose_independent_structured_forms():
    import server.modifier_registry as registry

    tools = {tool["id"]: tool for tool in registry.list_modifier_tools()}
    expected_forms = {
        "what-if": ["callout", "paragraph", "table", "questions"],
        "counterfactual": ["table", "table", "paragraph", "questions"],
        "futures-wheel": ["callout", "table", "bar_chart", "questions"],
        "dators-four-futures": ["table", "table", "questions"],
        "causal-layered-analysis": ["table", "callout", "table", "questions"],
        "future-triangle": ["table", "bar_chart", "table", "questions"],
        "envisioning-cards": ["questions", "questions", "questions", "questions", "callout"],
        "three-horizons": ["table", "table", "questions"],
    }
    for tool_id, block_sequence in expected_forms.items():
        tool = tools[tool_id]
        assert tool["recommendation"]["type"] == "text"
        assert tool["text_output_forms"]["block_sequence"] == block_sequence
        assert "text_blocks" in tool["output_contract"]["text"]
        package_dir = Path(__file__).resolve().parents[1] / tool["package_path"]
        assert (package_dir / "text-output-forms.md").exists()


def test_modifier_tools_expose_short_descriptions():
    import server.modifier_registry as registry

    required_ids = {
        "what-if",
        "futures-wheel",
        "counterfactual",
        "physical-fiction",
        "causal-layered-analysis",
        "cautionary-tales",
        "dators-four-futures",
        "envisioning-cards",
        "experiential-futures-ladder",
        "future-triangle",
        "reductio-ad-absurdum",
        "three-horizons",
    }
    tools = {tool["id"]: tool for tool in registry.list_modifier_tools()}
    assert required_ids.issubset(tools)
    for tool_id in required_ids:
        words = tools[tool_id]["description"].split()
        assert 20 <= len(words) <= 30
        assert tools[tool_id]["package_path"].startswith("tool_packages/")


def test_env_file_loader_sets_missing_values():
    import os

    from server.config import load_env_file

    with TemporaryDirectory() as tmp:
        env_file = Path(tmp) / ".env"
        env_file.write_text("SPEC_WEB_TEST_ENV=value-from-file\n", encoding="utf-8")
        os.environ.pop("SPEC_WEB_TEST_ENV", None)
        load_env_file(env_file)
        assert os.environ["SPEC_WEB_TEST_ENV"] == "value-from-file"
        os.environ.pop("SPEC_WEB_TEST_ENV", None)
