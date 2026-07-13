from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request


BASE_URL = "http://127.0.0.1:8001"


def request_json(path: str, method: str = "GET", payload: dict | None = None, timeout: int = 240) -> dict:
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


def add_edge(project_id: str, source: str, target: str, edge_kind: str = "data") -> dict:
    return request_json(
        f"/api/projects/{project_id}/edges",
        "POST",
        {
            "source_node_id": source,
            "target_node_id": target,
            "source_port": "out",
            "target_port": "in",
            "edge_kind": edge_kind,
        },
    )["edge"]


def run_modify(project_id: str, node_id: str) -> dict:
    started = time.time()
    result = request_json(f"/api/projects/{project_id}/nodes/{node_id}/run", "POST", {}, timeout=300)
    elapsed = round(time.time() - started, 1)
    node = result["output_node"]
    print(
        json.dumps(
            {
                "modify_node": node_id,
                "status": result["run"]["status"],
                "output_node": node["id"],
                "output_type": node["type"],
                "elapsed_seconds": elapsed,
                "image_url": node.get("payload", {}).get("image_url", ""),
                "image_error": node.get("payload", {}).get("image_error", ""),
                "text_preview": node.get("payload", {}).get("text", "")[:180],
            },
            ensure_ascii=False,
        )
    )
    return result


def main() -> int:
    project = create_project("Sample Workflow - Scientific Speculation")
    project_id = project["id"]

    source = add_node(
        project_id,
        {
            "type": "text",
            "title": "Research Field",
            "position": {"x": 80, "y": 90},
            "payload": {
                "text": (
                    "请所有生成输出使用中文。\n"
                    "我是一名材料化学与电化学方向的科研人员，研究领域是用于绿色制氢的生物启发型催化材料。"
                    "当前课题聚焦于将 DNA 水凝胶、金属单原子位点与导电碳材料复合，构建在温和条件下稳定工作的析氢反应催化界面。"
                    "现实科研目标不是宣称已经替代铂催化剂，而是探索低贵金属或非贵金属体系中，生物大分子如何影响离子传输、局部水结构、"
                    "活性位点暴露与长期稳定性。实验上会结合电化学极化曲线、阻抗谱、原位拉曼、XPS 和加速耐久测试，"
                    "同时关注材料来源、批次差异、可规模化制备、废弃物处理与生物安全合规。"
                )
            },
            "status": "ready",
        },
    )

    round_specs = [
        ("What-if Scenario", {"what-if"}, {"x": 500, "y": 80}),
        ("Counterfactual Branch", {"counterfactual"}, {"x": 500, "y": 330}),
        ("Cautionary Tale", {"cautionary-tales"}, {"x": 500, "y": 580}),
    ]
    outputs = []
    for title, tools, position in round_specs:
        modify = add_node(
            project_id,
            {
                "type": "modify",
                "title": title,
                "position": position,
                "config": tool_config(tools, "text"),
                "status": "ready",
            },
        )
        add_edge(project_id, source["id"], modify["id"])
        result = run_modify(project_id, modify["id"])
        outputs.append(result["output_node"])

    synthesis_instruction = add_node(
        project_id,
        {
            "type": "text",
            "title": "Image Synthesis Instruction",
            "position": {"x": 900, "y": 80},
            "payload": {
                "text": (
                    "请读取前三轮由 Modify 生成的思辨推演文字，整合为一个文生图 prompt，并生成图像。"
                    "图像应是写实摄影风格，但在现实认知上略微不成立：看似真实的实验室或社区能源场景中，"
                    "出现被制度化、商品化或日常化的 DNA 水凝胶催化耗材。"
                    "不要做抽象海报，不要科幻飞船，不要赛博朋克霓虹；要像新闻纪实照片或研究机构档案照片。"
                    "同时附上一段中文文字描述，说明图像中的物件、场景和思辨问题。"
                )
            },
            "status": "ready",
        },
    )
    final_modify = add_node(
        project_id,
        {
            "type": "modify",
            "title": "Image Prompt + Speculative Image",
            "position": {"x": 900, "y": 300},
            "config": tool_config({"physical-fiction", "what-if", "cautionary-tales"}, "multimodal"),
            "status": "ready",
        },
    )
    for output in outputs:
        add_edge(project_id, output["id"], final_modify["id"])
    add_edge(project_id, synthesis_instruction["id"], final_modify["id"])
    final_result = run_modify(project_id, final_modify["id"])

    canvas = request_json(f"/api/projects/{project_id}/canvas")["canvas"]
    summary = {
        "project_id": project_id,
        "project_title": project["title"],
        "nodes": len(canvas["nodes"]),
        "edges": len(canvas["edges"]),
        "runs": len(canvas["runs"]),
        "final_output_node": final_result["output_node"]["id"],
        "final_image_url": final_result["output_node"]["payload"].get("image_url", ""),
        "final_image_error": final_result["output_node"]["payload"].get("image_error", ""),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
