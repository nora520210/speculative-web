import os

from server.model_service import require_openai_key


def test_request_key_is_accepted_without_environment_fallback():
    original = os.environ.pop("OPENAI_API_KEY", None)
    try:
        assert require_openai_key("test-user-key-1234567890") == "test-user-key-1234567890"
    finally:
        if original is not None:
            os.environ["OPENAI_API_KEY"] = original


def test_responses_request_includes_real_image_inputs():
    import server.model_service as model_service

    original_request = model_service.openai_json_request
    captured = {}

    def fake_request(url, key, payload=None, **kwargs):
        captured.update(payload or {})
        return {"output_text": "{}"}

    model_service.openai_json_request = fake_request
    try:
        model_service.call_responses_api(
            "test-key",
            "test-model",
            "Inspect the direct inputs.",
            image_inputs=[{"data_url": "data:image/png;base64,AA==", "detail": "high"}],
        )
        content = captured["input"][0]["content"]
        assert content[0]["type"] == "input_text"
        assert content[1]["type"] == "input_image"
        assert content[1]["image_url"].startswith("data:image/png")
    finally:
        model_service.openai_json_request = original_request


def test_model_environment_describes_multimodal_execution():
    import server.model_service as model_service

    original_key = os.environ.get("OPENAI_API_KEY")
    os.environ["OPENAI_API_KEY"] = "test-key"
    try:
        capabilities = {item["name"]: item for item in model_service.model_environment_status()["capabilities"]}
        assert "sent as bounded visual context" in capabilities["multimodal_analysis"]["notes"]
    finally:
        if original_key is None:
            os.environ.pop("OPENAI_API_KEY", None)
        else:
            os.environ["OPENAI_API_KEY"] = original_key
