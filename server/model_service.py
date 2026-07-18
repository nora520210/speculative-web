from __future__ import annotations

import json
import os
from http.client import RemoteDisconnected
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from dataclasses import dataclass

from server.config import MAX_USER_API_KEY_CHARS, load_env_file, user_api_key_required


load_env_file()

OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_MODELS_URL = "https://api.openai.com/v1/models"
OPENAI_IMAGE_GENERATIONS_URL = "https://api.openai.com/v1/images/generations"
DEFAULT_MODEL_CANDIDATES = (
    "gpt-5.2",
    "gpt-5.1",
    "gpt-5",
    "gpt-4.1-mini",
    "gpt-4o-mini",
    "gpt-4",
    "gpt-3.5-turbo",
)


@dataclass(frozen=True)
class ModelCapability:
    name: str
    configured: bool
    notes: str


def model_environment_status() -> dict:
    has_key = bool(os.environ.get("OPENAI_API_KEY"))
    runs_enabled = openai_runs_enabled()
    capabilities = [
        ModelCapability("structured_text", has_key and runs_enabled, "OpenAI text generation for Modify runs."),
        ModelCapability("multimodal_analysis", has_key and runs_enabled, "Direct Image and Text+Image inputs are sent as bounded visual context during the active Modify request."),
        ModelCapability("image_generation", has_key and runs_enabled, "Text-to-image generation is enabled for image and text+image Modify outputs."),
    ]
    return {
        "openai_api_key_configured": has_key,
        "openai_runs_enabled": runs_enabled,
        "user_api_key_required": user_api_key_required(),
        "model": configured_model(),
        "capabilities": [capability.__dict__ for capability in capabilities],
    }


class ModelServiceError(RuntimeError):
    pass


class ModelServiceNotConfigured(RuntimeError):
    pass


def openai_runs_enabled() -> bool:
    return os.environ.get("SPEC_WEB_ENABLE_OPENAI_RUNS", "1").lower() not in {"0", "false", "no"}


def configured_model() -> str:
    return os.environ.get("OPENAI_MODEL", "").strip() or "auto"


def configured_image_model() -> str:
    return os.environ.get("OPENAI_IMAGE_MODEL", "").strip() or "gpt-image-1"


def require_openai_key(api_key: str | None = None) -> str:
    key = (api_key or os.environ.get("OPENAI_API_KEY") or "").strip()
    if len(key) > MAX_USER_API_KEY_CHARS:
        raise ModelServiceNotConfigured("The API key is too long.")
    if not key:
        raise ModelServiceNotConfigured(
            "No API key is available for this run."
        )
    try:
        key.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ModelServiceNotConfigured("The API key must contain ASCII characters only.") from exc
    return key


def generate_modify_response(prompt: str, api_key: str | None = None, image_inputs: list[dict] | None = None) -> dict:
    if not openai_runs_enabled():
        raise ModelServiceNotConfigured("OpenAI runs are disabled for this process.")
    key = require_openai_key(api_key)
    model = resolve_model(key)
    try:
        return call_responses_api(key, model, prompt, image_inputs=image_inputs)
    except ModelServiceError as responses_error:
        try:
            result = call_chat_completions_api(key, model, prompt, image_inputs=image_inputs)
            result["fallback_reason"] = str(responses_error)
            return result
        except ModelServiceError:
            raise responses_error


def generate_image_response(prompt: str, api_key: str | None = None) -> dict:
    if not openai_runs_enabled():
        raise ModelServiceNotConfigured("OpenAI runs are disabled for this process.")
    key = require_openai_key(api_key)
    model = configured_image_model()
    response = openai_json_request(
        OPENAI_IMAGE_GENERATIONS_URL,
        key,
        {
            "model": model,
            "prompt": prompt,
            "size": os.environ.get("OPENAI_IMAGE_SIZE", "1536x1024"),
        },
        timeout=120,
    )
    images = response.get("data") or []
    if not images:
        raise ModelServiceError("OpenAI image generation returned no image data.")
    image = images[0]
    b64_json = image.get("b64_json", "")
    url = image.get("url", "")
    if not b64_json and not url:
        raise ModelServiceError("OpenAI image generation returned no b64_json or url.")
    return {
        "provider": "openai",
        "api": "images_generations",
        "model": model,
        "b64_json": b64_json,
        "url": url,
    }


def resolve_model(key: str) -> str:
    explicit_model = os.environ.get("OPENAI_MODEL", "").strip()
    if explicit_model:
        return explicit_model
    try:
        response = openai_json_request(
            OPENAI_MODELS_URL,
            key,
            method="GET",
            timeout=12,
        )
    except ModelServiceError:
        return "gpt-4.1-mini"
    ids = {item.get("id") for item in response.get("data", []) if isinstance(item, dict)}
    for candidate in DEFAULT_MODEL_CANDIDATES:
        if candidate in ids:
            return candidate
    return "gpt-4.1-mini"


def call_responses_api(key: str, model: str, prompt: str, image_inputs: list[dict] | None = None) -> dict:
    content = [{"type": "input_text", "text": prompt}]
    content.extend(
        {
            "type": "input_image",
            "image_url": image["data_url"],
            "detail": image.get("detail", "high"),
        }
        for image in image_inputs or []
        if image.get("data_url")
    )
    response = openai_json_request(
        OPENAI_RESPONSES_URL,
        key,
        {
            "model": model,
            "input": [{"role": "user", "content": content}],
            "max_output_tokens": 1200,
        },
        timeout=60,
    )
    text = extract_responses_text(response)
    if not text:
        raise ModelServiceError("OpenAI Responses API returned no text.")
    return {
        "provider": "openai",
        "api": "responses",
        "model": model,
        "text": text,
    }


def call_chat_completions_api(key: str, model: str, prompt: str, image_inputs: list[dict] | None = None) -> dict:
    content: str | list[dict] = prompt
    if image_inputs:
        content = [{"type": "text", "text": prompt}]
        content.extend(
            {
                "type": "image_url",
                "image_url": {"url": image["data_url"], "detail": image.get("detail", "high")},
            }
            for image in image_inputs
            if image.get("data_url")
        )
    response = openai_json_request(
        OPENAI_CHAT_COMPLETIONS_URL,
        key,
        {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You generate constrained speculative design outputs. Return JSON only.",
                },
                {"role": "user", "content": content},
            ],
            "max_tokens": 1200,
        },
        timeout=60,
    )
    choices = response.get("choices") or []
    text = ""
    if choices:
        message = choices[0].get("message") or {}
        text = message.get("content") or ""
    if not text:
        raise ModelServiceError("OpenAI Chat Completions API returned no text.")
    return {
        "provider": "openai",
        "api": "chat_completions",
        "model": model,
        "text": text,
    }


def openai_json_request(
    url: str,
    key: str,
    payload: dict | None = None,
    method: str = "POST",
    timeout: int = 60,
) -> dict:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(
        url,
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw or "{}")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise ModelServiceError(f"OpenAI request failed with HTTP {exc.code}: {detail}") from exc
    except (URLError, RemoteDisconnected, ConnectionError, OSError) as exc:
        reason = getattr(exc, "reason", None) or str(exc) or exc.__class__.__name__
        raise ModelServiceError(f"OpenAI request failed: {reason}") from exc
    except TimeoutError as exc:
        raise ModelServiceError("OpenAI request timed out.") from exc
    except json.JSONDecodeError as exc:
        raise ModelServiceError("OpenAI returned invalid JSON.") from exc


def extract_responses_text(response: dict) -> str:
    output_text = response.get("output_text")
    if output_text:
        return str(output_text)
    parts = []
    for item in response.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                parts.append(str(content["text"]))
    return "\n".join(parts).strip()
