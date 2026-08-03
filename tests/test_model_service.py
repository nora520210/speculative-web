import os
from http.client import RemoteDisconnected

from server.model_service import ModelServiceError, openai_json_request, require_openai_key


def test_request_key_is_accepted_without_environment_fallback():
    original = os.environ.pop("OPENAI_API_KEY", None)
    try:
        assert require_openai_key("test-user-key-1234567890") == "test-user-key-1234567890"
    finally:
        if original is not None:
            os.environ["OPENAI_API_KEY"] = original


def test_request_key_rejects_non_ascii_characters():
    from server.model_service import ModelServiceNotConfigured

    try:
        require_openai_key("sk-测试")
    except ModelServiceNotConfigured as exc:
        assert "ASCII" in str(exc)
    else:
        raise AssertionError("Expected non-ASCII API key to be rejected.")


def test_openai_connection_drop_becomes_model_service_error():
    import server.model_service as model_service

    original_urlopen = model_service.urlopen

    def dropped_connection(*args, **kwargs):
        raise RemoteDisconnected("connection closed")

    model_service.urlopen = dropped_connection
    try:
        try:
            openai_json_request("https://example.test", "test-key", {"model": "test"})
        except ModelServiceError as exc:
            assert "connection closed" in str(exc)
        else:
            raise AssertionError("Expected a disconnected request to become ModelServiceError.")
    finally:
        model_service.urlopen = original_urlopen


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


def test_image_generation_falls_back_to_gpt_image_one():
    import server.model_service as model_service

    original_request = model_service.openai_json_request
    original_model = os.environ.get("OPENAI_IMAGE_MODEL")
    calls = []

    def fake_request(url, key, payload=None, **kwargs):
        calls.append(payload)
        if payload["model"] == "bad-image-model":
            raise ModelServiceError("model is not supported")
        return {"data": [{"b64_json": "AA=="}]}

    os.environ["OPENAI_IMAGE_MODEL"] = "bad-image-model"
    model_service.openai_json_request = fake_request
    try:
        result = model_service.generate_image_response("Draw a test image.", api_key="test-key")
        assert result["model"] == "gpt-image-1"
        assert any(call["model"] == "bad-image-model" for call in calls)
        assert any(call["model"] == "gpt-image-1" for call in calls)
    finally:
        model_service.openai_json_request = original_request
        if original_model is None:
            os.environ.pop("OPENAI_IMAGE_MODEL", None)
        else:
            os.environ["OPENAI_IMAGE_MODEL"] = original_model


def test_image2_alias_prefers_gpt_image_two_before_fallback():
    import server.model_service as model_service

    attempts = model_service.image_generation_attempts("image2", "1536x1024")
    assert attempts[0] == ("gpt-image-2", "1536x1024")
    assert ("gpt-image-1", "1024x1024") in attempts
