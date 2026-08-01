from __future__ import annotations

import json

from server.model_service import ModelServiceError, ModelServiceNotConfigured, generate_modify_response


FIELD_BY_STAGE = {
    "frame_focus": "research_focus",
    "frame_assumptions": "assumptions",
    "frame_stakeholders": "stakeholders",
    "frame_tensions": "tensions",
}


def fallback_agent_guide(payload: dict) -> dict:
    stage = str(payload.get("stage") or "start")
    brief = payload.get("brief") if isinstance(payload.get("brief"), dict) else {}
    topic = str(brief.get("topic") or payload.get("topic") or "这个议题")
    start_mode = str(payload.get("start_mode") or "research")
    material = "设计设想" if start_mode == "design" else "真实研究"

    if stage == "start":
        return {
            "question": f"先把这个{material}放进一个未来现场：谁会使用它，谁会被影响，哪里开始不确定？",
            "options": [
                f"围绕{topic}，先描述一个具体使用现场",
                f"补充{topic}背后的研究或设计背景",
                "先写出一个可能的反例",
                "直接把它改写成 What-if",
            ],
            "hint": "不用写完整报告，一句话也可以开始。",
        }
    if stage == "frame_focus":
        return {
            "question": f"{topic}里最值得被继续追问的研究关注是什么？",
            "options": [
                "技术机制与真实使用之间的边界",
                "哪些条件会让结果失效",
                "谁能解释系统给出的判断",
                "这个议题进入日常后的不确定性",
            ],
            "hint": "选择一个关注点，系统会写入研究议题卡。",
        }
    if stage == "frame_assumptions":
        return {
            "question": "这个议题目前默认相信了哪些判断？",
            "options": [
                "更多数据会带来更好判断",
                "使用者会接受系统建议",
                "风险可以通过流程控制",
                "技术稳定性会延续到真实现场",
            ],
            "hint": "可选择一个，也可以写多行假设。",
        }
    if stage == "frame_stakeholders":
        return {
            "question": f"围绕{topic}，哪些人会参与、受益、受影响或拥有否决权？",
            "options": [
                "直接使用者、研究人员、操作人员",
                "被间接影响的人、监管者、伦理审查者",
                "维护系统的人、解释结果的人",
                "可以拒绝或中止系统的人",
            ],
            "hint": "把角色写成短语即可。",
        }
    if stage == "frame_tensions":
        return {
            "question": "这轮讨论最值得保留的冲突是什么？",
            "options": [
                "效率提升与解释权之间的张力",
                "技术稳定性与真实使用复杂度之间的张力",
                "研究可控性与公共影响之间的张力",
                "个体拒绝权与系统默认流程之间的张力",
            ],
            "hint": "补完这一项后会直接进入 What-if，不再停留在关键词确认。",
        }
    if stage == "keywords":
        return {
            "question": "关键词、默认假设和利益相关者已经汇合。要不要进入四条 What-if 线路？",
            "options": ["确认关键词并进入 What-if", f"再补充{topic}的实验条件", "加入一个反例后再继续"],
            "hint": "确认后会解锁增长、崩溃、平衡、转变四条方向。",
        }
    if stage == "four_futures":
        if payload.get("has_branches"):
            return {
                "question": "四条线路已经生成。先选择一条最值得继续展开的未来方向。",
                "options": ["增长：放大机会", "崩溃：追踪失效", "平衡：寻找约束", "转变：重写关系"],
                "hint": "选择后会进入追问和工具介入。",
            }
        return {
            "question": "现在可以把议题生成四条 What-if 线路。",
            "options": ["生成增长、崩溃、平衡、转变四条线路", "先回看默认假设", "补一个被遗漏的角色"],
            "hint": "生成后只选择一条继续展开。",
        }
    if stage == "tools":
        return {
            "question": "选择一个工具介入当前节点，让分析结果进入这条情境线。",
            "options": ["警示故事", "未来锥", "未来三角", "影响轮", "体验阶梯"],
            "hint": "工具结果会成为冲突、角色、场景或逻辑节点。",
        }
    return {
        "question": "下一步先补哪一块材料？",
        "options": ["角色", "依据", "默认假设", "反例"],
        "hint": "选择一个短语即可继续。",
    }


def parse_agent_guide(text: str, payload: dict) -> dict:
    fallback = fallback_agent_guide(payload)
    try:
        json_text = text[text.index("{") : text.rindex("}") + 1] if "{" in text and "}" in text else text
        parsed = json.loads(json_text)
    except (ValueError, json.JSONDecodeError):
        fallback["usedFallback"] = True
        return fallback
    question = str(parsed.get("question") or fallback["question"]).strip()
    options = parsed.get("options") if isinstance(parsed.get("options"), list) else fallback["options"]
    options = [str(item).strip() for item in options if str(item).strip()][:5] or fallback["options"]
    hint = str(parsed.get("hint") or fallback.get("hint") or "").strip()
    secondary = parsed.get("secondaryOptions") if isinstance(parsed.get("secondaryOptions"), list) else []
    return {
        "question": question[:260],
        "options": options,
        "hint": hint[:220],
        "secondaryQuestion": str(parsed.get("secondaryQuestion") or "")[:220],
        "secondaryOptions": [str(item).strip() for item in secondary if str(item).strip()][:4],
    }


def build_agent_guide_prompt(payload: dict) -> str:
    stage = str(payload.get("stage") or "start")
    pending_field = FIELD_BY_STAGE.get(stage, "")
    return (
        "你是一个中文 AI Agent 共创引导师，正在帮助科研人员和设计师把一个议题推进为可复盘的未来情境。\n"
        "请参考 speculative-agent-tool 的对话模式：短问题、贴合上下文的选项、低负担填写，不要长篇解释。\n"
        "但本网页步骤固定为：研究议题 -> 关键词/默认假设/利益相关者 -> What-if -> 工具介入 -> 情境生成。\n"
        "当研究关注、默认假设、利益相关者、核心张力收集完毕后，系统会自动进入 What-if，不需要用户确认关键词。\n"
        "你只能生成当前步骤的下一轮引导问题和快捷填写选项，不要改变步骤，不要要求用户填写隐藏表单。\n"
        "输出必须是 JSON，格式：{\"question\":\"...\",\"options\":[\"...\"],\"hint\":\"...\",\"secondaryQuestion\":\"...\",\"secondaryOptions\":[\"...\"]}。\n"
        "要求：问题必须像现场主持人自然追问；options 生成 3 到 5 个，短而具体，至少 2 个选项要包含用户议题中的具体材料、角色、场景或行为；"
        "不要只给“隐私/公平/效率/信任”这种泛词；不要出现固定流程名；不要说教。\n\n"
        f"当前 stage: {stage}\n"
        f"当前待填写字段: {pending_field or payload.get('pending_field') or 'none'}\n"
        f"上下文 JSON: {json.dumps(payload, ensure_ascii=False)[:5000]}"
    )


def generate_agent_guide(payload: dict, api_key: str | None = None) -> dict:
    fallback = fallback_agent_guide(payload)
    try:
        model_result = generate_modify_response(build_agent_guide_prompt(payload), api_key=api_key, max_output_tokens=700)
    except (ModelServiceError, ModelServiceNotConfigured) as exc:
        fallback.update({"usedFallback": True, "error": str(exc)})
        return fallback
    parsed = parse_agent_guide(str(model_result.get("text") or ""), payload)
    parsed["model"] = {"provider": model_result.get("provider"), "model": model_result.get("model")}
    return parsed
