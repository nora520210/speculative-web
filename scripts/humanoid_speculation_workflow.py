from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request


BASE_URL = "http://127.0.0.1:8002"


def request_json(path: str, method: str = "GET", payload: dict | None = None, timeout: int = 300) -> dict:
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} failed with HTTP {exc.code}: {detail}") from exc


def tool_config(selected_ids: set[str], output_type: str) -> dict:
    tools = request_json("/api/modifier-tools")["tools"]
    return {
        "composition": "parallel",
        "output_type": output_type,
        "tools": [
            {
                "id": tool["id"],
                "label": tool["label"],
                "version": tool.get("version", "0.1.0"),
                "selected": tool["id"] in selected_ids,
            }
            for tool in tools
        ],
    }


def create_project(title: str) -> dict:
    return request_json("/api/projects", "POST", {"title": title})["project"]


def add_node(project_id: str, payload: dict) -> dict:
    return request_json(f"/api/projects/{project_id}/nodes", "POST", payload)["node"]


def add_edge(project_id: str, source: str, target: str) -> dict:
    return request_json(
        f"/api/projects/{project_id}/edges",
        "POST",
        {
            "source_node_id": source,
            "target_node_id": target,
            "source_port": "out",
            "target_port": "in",
            "edge_kind": "data",
        },
    )["edge"]


def add_modify(project_id: str, title: str, tool_ids: set[str], output_type: str, position: dict) -> dict:
    return add_node(
        project_id,
        {
            "type": "modify",
            "title": title,
            "position": position,
            "config": tool_config(tool_ids, output_type),
            "status": "ready",
        },
    )


def run_modify(project_id: str, node_id: str) -> dict:
    started = time.time()
    result = request_json(f"/api/projects/{project_id}/nodes/{node_id}/run", "POST", {}, timeout=360)
    output = result["output_node"]
    print(
        json.dumps(
            {
                "modify_node": node_id,
                "status": result["run"]["status"],
                "output_node": output["id"],
                "output_type": output["type"],
                "elapsed_seconds": round(time.time() - started, 1),
                "image_url": output.get("payload", {}).get("image_url", ""),
                "image_error": output.get("payload", {}).get("image_error", ""),
                "text_preview": output.get("payload", {}).get("text", "")[:150],
            },
            ensure_ascii=False,
        )
    )
    return result


def main() -> int:
    project = create_project("Humanoid Hand + Mobility / 1X-inspired Speculation")
    project_id = project["id"]

    source = add_node(
        project_id,
        {
            "type": "text",
            "title": "Engineering Intake: dexterous hand + dynamic mobile manipulation",
            "position": {"x": 60, "y": 180},
            "payload": {
                "text": (
                    "We are a humanoid robotics engineering team developing a tendon-driven dexterous hand and whole-body mobile "
                    "manipulation stack for domestic tasks. Our development loop starts from a task library: grasping deformable "
                    "packages, opening articulated doors and drawers, carrying objects while walking, placing objects at variable "
                    "heights, and recovering from contact disturbances. The hand program combines tendon tension sensing, joint state, "
                    "wrist force/torque, tactile contact events, stereo vision, and synchronized gait state. Each candidate skill is first "
                    "tested against contact, slip, reachability, and recovery criteria, then evaluated in cluttered household mock-ups; "
                    "human teleoperation remains an engineering data-collection and safety fallback during early deployment.\n\n"
                    "Relevant public material from 1X Technologies: on 9 July 2026, 1X described NEO hands with 25 degrees of freedom "
                    "and tendon drive, framing dexterity, strength, safety, and reliability as core constraints. Its February 2025 NEO Gamma "
                    "announcement described natural walking, squatting, sitting, and visual manipulation across varied objects. Its January "
                    "2026 world-model account describes a development path in which a video-pretrained world model is grounded with egocentric "
                    "human and NEO sensorimotor data, then paired with an inverse-dynamics model to turn predicted scene changes into feasible "
                    "action sequences.\n\n"
                    "Sources: https://www.1x.tech/discover/neos-hands ; https://www.1x.tech/discover/introducing-neo-gamma ; "
                    "https://www.1x.tech/discover/world-model-self-learning"
                )
            },
            "status": "ready",
        },
    )

    excavation = add_modify(
        project_id,
        "Round 1: engineering assumptions",
        {"causal-layered-analysis"},
        "text",
        {"x": 460, "y": 90},
    )
    add_edge(project_id, source["id"], excavation["id"])
    excavation_output = run_modify(project_id, excavation["id"])["output_node"]

    counterfactual = add_modify(
        project_id,
        "Round 2A: contingent embodiment branch",
        {"counterfactual"},
        "text",
        {"x": 860, "y": 20},
    )
    add_edge(project_id, excavation_output["id"], counterfactual["id"])
    counterfactual_output = run_modify(project_id, counterfactual["id"])["output_node"]

    consequences = add_modify(
        project_id,
        "Round 2B: downstream consequence branch",
        {"futures-wheel"},
        "text",
        {"x": 860, "y": 370},
    )
    add_edge(project_id, excavation_output["id"], consequences["id"])
    consequences_output = run_modify(project_id, consequences["id"])["output_node"]

    cautionary = add_modify(
        project_id,
        "Round 3A: institutional stress test",
        {"cautionary-tales"},
        "text",
        {"x": 1260, "y": 370},
    )
    add_edge(project_id, consequences_output["id"], cautionary["id"])
    cautionary_output = run_modify(project_id, cautionary["id"])["output_node"]

    futures = add_modify(
        project_id,
        "Round 3B: structurally different trajectories",
        {"dators-four-futures"},
        "text",
        {"x": 1260, "y": 40},
    )
    add_edge(project_id, counterfactual_output["id"], futures["id"])
    add_edge(project_id, consequences_output["id"], futures["id"])
    futures_output = run_modify(project_id, futures["id"])["output_node"]

    domestic_artifact = add_modify(
        project_id,
        "Round 4A: domestic operating artifact",
        {"physical-fiction"},
        "multimodal",
        {"x": 1650, "y": 350},
    )
    add_edge(project_id, cautionary_output["id"], domestic_artifact["id"])
    domestic_result = run_modify(project_id, domestic_artifact["id"])

    economic_artifact = add_modify(
        project_id,
        "Round 4B: robotics market artifact",
        {"physical-fiction"},
        "multimodal",
        {"x": 1650, "y": 20},
    )
    add_edge(project_id, futures_output["id"], economic_artifact["id"])
    economic_result = run_modify(project_id, economic_artifact["id"])

    canvas = request_json(f"/api/projects/{project_id}/canvas")["canvas"]
    print(
        json.dumps(
            {
                "project_id": project_id,
                "project_title": project["title"],
                "nodes": len(canvas["nodes"]),
                "edges": len(canvas["edges"]),
                "runs": len(canvas["runs"]),
                "domestic_artifact_image": domestic_result["output_node"]["payload"].get("image_url", ""),
                "economic_artifact_image": economic_result["output_node"]["payload"].get("image_url", ""),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
