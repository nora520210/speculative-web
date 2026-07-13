import os

from server.model_service import require_openai_key


def test_request_key_is_accepted_without_environment_fallback():
    original = os.environ.pop("OPENAI_API_KEY", None)
    try:
        assert require_openai_key("test-user-key-1234567890") == "test-user-key-1234567890"
    finally:
        if original is not None:
            os.environ["OPENAI_API_KEY"] = original
