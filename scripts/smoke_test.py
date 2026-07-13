from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def fetch_json(url: str) -> dict:
    with urlopen(url, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    port = "8765"
    process = subprocess.Popen(
        [PYTHON, str(ROOT / "app.py")],
        cwd=ROOT,
        env={**os.environ, "PORT": port},
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
        model = fetch_json(f"http://127.0.0.1:{port}/api/model/status")
        if "model" not in model:
            print("model endpoint failed")
            return 1
        print("smoke ok")
        return 0
    finally:
        process.terminate()
        process.wait(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
