from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def fetch_json(url: str) -> dict:
    with urlopen(url, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json(url: str, payload: dict) -> dict:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def patch_json(url: str, payload: dict) -> dict:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="PATCH",
    )
    with urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    port = "8765"
    data_dir = TemporaryDirectory(prefix="speculative-web-smoke-")
    process = subprocess.Popen(
        [PYTHON, str(ROOT / "app.py")],
        cwd=ROOT,
        env={
            **os.environ,
            "PORT": port,
            "SPEC_WEB_DATA_DIR": data_dir.name,
            "SPEC_WEB_ENABLE_OPENAI_RUNS": "0",
            "SPEC_WEB_REQUIRE_USER_API_KEY": "0",
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        deadline = time.time() + 8
        health = None
        while time.time() < deadline:
            try:
                health = fetch_json(f"http://127.0.0.1:{port}/api/health")
                break
            except Exception:
                time.sleep(0.25)
        if not health or not health.get("ok"):
            print("health check failed")
            return 1

        projects = fetch_json(f"http://127.0.0.1:{port}/api/projects")
        if "projects" not in projects:
            print("projects endpoint failed")
            return 1
        first_project = projects["projects"][0]
        canvas = fetch_json(f"http://127.0.0.1:{port}/api/projects/{first_project['id']}/canvas")
        if "canvas" not in canvas or "nodes" not in canvas["canvas"]:
            print("canvas endpoint failed")
            return 1
        tools = fetch_json(f"http://127.0.0.1:{port}/api/modifier-tools")
        if "tools" not in tools:
            print("modifier tools endpoint failed")
            return 1
        operations = fetch_json(f"http://127.0.0.1:{port}/api/operation-definitions")
        if not any(item.get("id") == "operation.guided-scenario" for item in operations.get("definitions", [])):
            print("guided scenario operation definition failed")
            return 1
        workflows = fetch_json(f"http://127.0.0.1:{port}/api/workflow-definitions")
        if not any(item.get("id") == "workflow.four-futures-foundation" for item in workflows.get("definitions", [])):
            print("four futures workflow definition failed")
            return 1
        foundation = post_json(
            f"http://127.0.0.1:{port}/api/projects/{first_project['id']}/workflows",
            {
                "definition_id": "workflow.four-futures-foundation",
                "start_mode": "research",
                "topic": "Smoke-test inquiry",
            },
        )
        if foundation.get("workflow", {}).get("stage") != "four_futures" or len(foundation.get("nodes", [])) != 3:
            print("four futures workflow start failed")
            return 1

        guided_project = post_json(f"http://127.0.0.1:{port}/api/projects", {"title": "Guided smoke"}).get("project", {})
        guided_project_id = guided_project.get("id")
        guided_interaction = fetch_json(f"http://127.0.0.1:{port}/api/projects/{guided_project_id}/interaction").get("interaction", {})
        guided_session = (guided_interaction.get("conversation_sessions") or [{}])[0]
        session_id = guided_session.get("id")
        agent_guide = post_json(
            f"http://127.0.0.1:{port}/api/projects/{guided_project_id}/conversations/{session_id}/agent-guide",
            {
                "stage": "start",
                "start_mode": "research",
                "brief": {"topic": "Guided smoke inquiry"},
                "history": [],
            },
        )
        if not agent_guide.get("question") or not agent_guide.get("options"):
            print("agent guide endpoint failed")
            return 1
        guide_url = f"http://127.0.0.1:{port}/api/projects/{guided_project_id}/conversations/{session_id}/guide-actions"
        post_json(guide_url, {"action": "begin", "body": "Guided smoke inquiry"})
        post_json(guide_url, {"action": "answer", "body": "A focused question"})
        post_json(guide_url, {"action": "skip"})
        post_json(guide_url, {"action": "skip"})
        guided_result = post_json(guide_url, {"action": "answer", "body": "Care and control"})
        if guided_result.get("workflow", {}).get("stage") != "four_futures":
            print("conversation guide API failed")
            return 1
        guided_workflow = guided_result["workflow"]
        generated = post_json(
            f"http://127.0.0.1:{port}/api/projects/{guided_project_id}/nodes/{guided_workflow['operation_node_id']}/run",
            {"session_id": session_id},
        )
        if generated.get("workflow", {}).get("status") != "awaiting_selection":
            print("four futures run failed")
            return 1
        branch_id = generated["workflow"]["branch_node_ids"][0]
        post_json(
            f"http://127.0.0.1:{port}/api/projects/{guided_project_id}/workflows/{guided_workflow['id']}/select-branch",
            {"branch_node_id": branch_id, "session_id": session_id},
        )
        source_id = guided_workflow["source_node_ids"][0]
        patch_json(
            f"http://127.0.0.1:{port}/api/projects/{guided_project_id}/nodes/{source_id}",
            {
                "payload": {"text": "Topic: Care infrastructure\nCore tension: convenience and autonomy"},
                "session_id": session_id,
            },
        )
        invalidated = fetch_json(f"http://127.0.0.1:{port}/api/projects/{guided_project_id}/interaction").get("interaction", {})
        invalidated_workflow = next(
            item for item in invalidated.get("workflow_instances", []) if item.get("id") == guided_workflow["id"]
        )
        invalidated_session = next(
            item for item in invalidated.get("conversation_sessions", []) if item.get("id") == session_id
        )
        invalidated_canvas = fetch_json(
            f"http://127.0.0.1:{port}/api/projects/{guided_project_id}/canvas"
        ).get("canvas", {})
        keyword_node = next(
            item for item in invalidated_canvas.get("nodes", []) if item.get("id") == guided_workflow["keyword_node_id"]
        )
        if (
            invalidated_workflow.get("status") != "stale"
            or invalidated_session.get("active_scope_id") != "scope-global"
            or invalidated_session.get("guide", {}).get("stage_id") != "stale"
            or keyword_node.get("payload", {}).get("keywords") != ["Care infrastructure", "convenience and autonomy"]
        ):
            print(
                "direct Brief edit synchronization failed",
                json.dumps(
                    {
                        "workflow_status": invalidated_workflow.get("status"),
                        "session_scope": invalidated_session.get("active_scope_id"),
                        "guide_stage": invalidated_session.get("guide", {}).get("stage_id"),
                        "keywords": keyword_node.get("payload", {}).get("keywords"),
                    },
                    ensure_ascii=False,
                ),
            )
            return 1
        model = fetch_json(f"http://127.0.0.1:{port}/api/model/status")
        if "model" not in model:
            print("model endpoint failed")
            return 1
        print("smoke ok")
        return 0
    finally:
        process.terminate()
        process.wait(timeout=5)
        data_dir.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
