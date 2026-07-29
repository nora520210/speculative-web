from __future__ import annotations

"""Backend executor helpers for the guided scenario operation.

The operation imports interaction patterns from the reviewed guided prototype without
importing its UI state machine: direct graph inputs become four durable branch
artifacts, and every branch carries only prompts for a later scoped conversation.
"""

import json
import re

from server.model_service import (
    ModelServiceError,
    ModelServiceNotConfigured,
    generate_modify_response,
    openai_runs_enabled,
)


FUTURES = (
    ("growth", "Growth"),
    ("collapse", "Collapse"),
    ("discipline", "Discipline"),
    ("transformation", "Transformation"),
)


def generate_guided_scenarios(source_context: list[dict], package_snapshot: list[dict], api_key: str | None = None) -> dict:
    """Return a validated four-branch artifact set with transparent fallback metadata."""

    fallback = fallback_branches(source_context)
    if not openai_runs_enabled():
        return {
            "branches": fallback,
            "model_snapshot": {
                "provider": "placeholder",
                "capability": "guided_scenario",
                "api_ready": False,
                "generated": False,
                "fallback_used": True,
                "fallback_reason": "OpenAI runs are disabled for this process.",
            },
        }

    try:
        model_result = generate_modify_response(
            build_guided_scenario_prompt(source_context, package_snapshot),
            api_key=api_key,
            # Four independent, evidence-bounded branches need more room than a
            # single Modify response. Keeping this explicit avoids truncating a
            # valid fourth branch and silently falling back to a placeholder set.
            max_output_tokens=3600,
        )
        branches = normalize_model_branches(model_result.get("text", ""))
        if branches:
            return {
                "branches": branches,
                "model_snapshot": {
                    "provider": model_result.get("provider", "openai"),
                    "api": model_result.get("api", "responses"),
                    "model": model_result.get("model", ""),
                    "capability": "guided_scenario",
                    "api_ready": True,
                    "generated": True,
                    "fallback_used": False,
                    "fallback_reason": model_result.get("fallback_reason", ""),
                },
            }
        reason = "The model response did not satisfy the four-branch contract."
        api_ready = True
        invalid_response_excerpt = str(model_result.get("text") or "")[:1200]
    except ModelServiceNotConfigured as exc:
        reason = str(exc)
        api_ready = False
        invalid_response_excerpt = ""
    except ModelServiceError as exc:
        reason = str(exc)
        api_ready = True
        invalid_response_excerpt = ""

    return {
        "branches": fallback,
        "model_snapshot": {
            "provider": "placeholder",
            "capability": "guided_scenario",
            "api_ready": api_ready,
            "generated": False,
            "fallback_used": True,
            "fallback_reason": reason,
            "invalid_response_excerpt": invalid_response_excerpt,
        },
    }


def build_guided_scenario_prompt(source_context: list[dict], package_snapshot: list[dict]) -> str:
    context = [
        {
            "node_id": str(item.get("id") or ""),
            "title": str(item.get("title") or ""),
            "text": str(item.get("text") or "")[:5000],
        }
        for item in source_context
        if str(item.get("text") or "").strip()
    ]
    tools = [
        {
            "id": tool.get("id"),
            "version": tool.get("version"),
            "theory_mapping": tool.get("theory_mapping", {}),
            "model_constraints": tool.get("model_constraints", []),
            "output_contract": tool.get("output_contract", {}),
        }
        for tool in package_snapshot
    ]
    response_shape = {
        "branches": [
            {
                "strategy": "growth | collapse | discipline | transformation",
                "what_if": "A precise question beginning with an altered condition.",
                "future_premise": "A concrete social, institutional, and everyday future condition.",
                "key_actors": ["Two to five affected actors"],
                "core_tension": "A conflict that should remain discussable.",
                "visual_brief": "A credible everyday scene, not a product advertisement.",
                "facilitation": {
                    "opening_question": "A question that exposes one default assumption.",
                    "role_prompts": ["Researcher prompt", "Designer prompt"],
                    "summary_lenses": ["shared ground", "disagreement", "unresolved question"],
                },
            }
        ]
    }
    payload = {
        "task": "Generate an independently discussable set of four futures for a scoped research conversation.",
        "rules": [
            "Return valid JSON only, with no Markdown fence or explanatory prose.",
            "Return exactly four branches in this order: growth, collapse, discipline, transformation.",
            "Use the input research material; do not invent evidence or present speculative claims as facts.",
            "Each branch must challenge a different default assumption and describe an everyday, institutional, or material consequence.",
            "Do not propose a final product or resolve the tension. The output opens a conversation rather than closing it.",
            "Use the dominant language of the research input.",
        ],
        "research_context": context,
        "tool_contract_snapshots": tools,
        "required_response_shape": response_shape,
    }
    return "Return valid JSON only.\n\n" + json.dumps(payload, ensure_ascii=False, indent=2)


def normalize_model_branches(raw_text: str) -> list[dict] | None:
    payload = parse_json_object(raw_text)
    branches = payload.get("branches") if isinstance(payload, dict) else None
    if not isinstance(branches, list) or len(branches) != len(FUTURES):
        return None

    normalized = []
    for index, (strategy_id, strategy_label) in enumerate(FUTURES):
        source = branches[index]
        # The array order is the authoritative contract. Some otherwise-valid model
        # responses localise the strategy label (or return "Growth future"), which
        # should not discard four concrete scenarios solely because a display value
        # is not the English machine id.
        if not isinstance(source, dict):
            return None
        actors = clean_strings(source.get("key_actors"), minimum=1, maximum=5, item_limit=90)
        facilitation = source.get("facilitation") if isinstance(source.get("facilitation"), dict) else {}
        role_prompts = clean_strings(facilitation.get("role_prompts"), minimum=1, maximum=3, item_limit=220)
        summary_lenses = clean_strings(facilitation.get("summary_lenses"), minimum=1, maximum=4, item_limit=120)
        opening_question = clean_text(facilitation.get("opening_question"), 300)
        if not actors:
            actors = ["directly affected participants", "institutional stewards"]
        if not opening_question:
            opening_question = "Which default assumption in this future should be tested before anyone proposes a solution?"
        if len(role_prompts) < 2:
            role_prompts = [
                *role_prompts,
                "Researcher: identify the evidence boundary or uncertainty this future changes.",
                "Designer: describe one ordinary material or institutional encounter under this rule.",
            ][:2]
        if len(summary_lenses) < 3:
            summary_lenses = [
                *summary_lenses,
                "provisional shared ground",
                "unresolved disagreement",
                "evidence still needed",
            ][:3]
        branch = {
            "id": strategy_id,
            "strategy": strategy_id,
            "strategy_label": strategy_label,
            "what_if": clean_text(source.get("what_if"), 300),
            "future_premise": clean_text(source.get("future_premise"), 650),
            "key_actors": actors,
            "core_tension": clean_text(source.get("core_tension"), 360),
            "visual_brief": clean_text(source.get("visual_brief"), 500),
            "facilitation": {
                "opening_question": opening_question,
                "role_prompts": role_prompts,
                "summary_lenses": summary_lenses,
            },
        }
        if not branch["what_if"] or not branch["future_premise"] or not branch["core_tension"] or not branch["visual_brief"]:
            return None
        if not branch["key_actors"] or not branch["facilitation"]["opening_question"]:
            return None
        if not branch["facilitation"]["role_prompts"] or not branch["facilitation"]["summary_lenses"]:
            return None
        normalized.append(branch)
    return normalized


def fallback_branches(source_context: list[dict]) -> list[dict]:
    topic = fallback_topic(source_context)
    chinese = bool(re.search(r"[\u4e00-\u9fff]", topic))
    if chinese:
        templates = {
            "growth": ("如果“{topic}”被扩展为默认基础设施，会怎样？", "它进入更多日常场景，效率与覆盖范围被视为首要公共价值。", "普及便利与拒绝、退出或保持沉默的权利之间的张力"),
            "collapse": ("如果“{topic}”在关键时刻不再被信任，会怎样？", "资源、维护或制度信任失效，原先被忽略的依赖关系成为日常风险。", "维持服务连续性与承认系统脆弱性之间的张力"),
            "discipline": ("如果“{topic}”只能在严格规则和许可下存在，会怎样？", "机构以安全、责任或公平为由设定进入条件，并重新分配谁能决定例外。", "可问责的治理与对参与者的过度规训之间的张力"),
            "transformation": ("如果“{topic}”改变了什么算作有效知识或正常日常，会怎样？", "新的协作、照护或判断方式出现，原有的专业边界和价值尺度被改写。", "创造新关系的可能与失去既有解释权之间的张力"),
        }
        actor_pairs = [
            ["直接使用者", "维护者", "公共机构"],
            ["依赖系统的人", "被系统排除的人", "维护者"],
            ["被管理的参与者", "规则制定者", "例外申请者"],
            ["新实践的参与者", "既有专业群体", "受影响的旁观者"],
        ]
        role_prompts = ["研究者：指出此分支改变了哪一项已知条件或默认假设。", "设计者：描述一个普通人会遇到的具体场景、物件或拒绝动作。"]
        summary_lenses = ["双方暂时同意什么", "双方在哪个责任或价值判断上分歧", "还需要哪项证据或实验"]
        opening = "先不要提出解决方案：这个未来前提改变了原研究中的哪一个默认假设？"
    else:
        templates = {
            "growth": ("What if {topic} became default infrastructure?", "It enters more everyday settings, and reach and efficiency become public expectations.", "The tension between broad convenience and the right to refuse, exit, or remain uncounted."),
            "collapse": ("What if {topic} was no longer trusted at a critical moment?", "A failure of resources, maintenance, or institutional trust makes hidden dependencies an everyday risk.", "The tension between service continuity and acknowledging system fragility."),
            "discipline": ("What if {topic} could exist only through strict rules and permissions?", "Institutions set conditions in the name of safety, responsibility, or fairness, redistributing who decides exceptions.", "The tension between accountable governance and over-disciplining participants."),
            "transformation": ("What if {topic} changed what counts as valid knowledge or ordinary life?", "New practices of collaboration, care, or judgement emerge and rewrite professional boundaries.", "The tension between creating new relations and losing existing interpretive authority."),
        }
        actor_pairs = [
            ["direct participants", "maintainers", "public institutions"],
            ["people who depend on the system", "people excluded by it", "maintainers"],
            ["regulated participants", "rule-makers", "exception seekers"],
            ["participants in new practices", "established professionals", "affected bystanders"],
        ]
        role_prompts = ["Researcher: name the known condition or default assumption this branch changes.", "Designer: describe one ordinary scene, object, or refusal action a person encounters."]
        summary_lenses = ["provisional shared ground", "disagreement about responsibility or value", "evidence or experiment still needed"]
        opening = "Do not solve it yet: which default assumption in the current research does this future premise change?"

    branches = []
    for index, (strategy_id, strategy_label) in enumerate(FUTURES):
        what_if, premise, tension = templates[strategy_id]
        branches.append(
            {
                "id": strategy_id,
                "strategy": strategy_id,
                "strategy_label": strategy_label,
                "what_if": what_if.format(topic=topic),
                "future_premise": premise,
                "key_actors": actor_pairs[index],
                "core_tension": tension,
                "visual_brief": fallback_visual_brief(topic, chinese),
                "facilitation": {
                    "opening_question": opening,
                    "role_prompts": role_prompts,
                    "summary_lenses": summary_lenses,
                },
            }
        )
    return branches


def render_branch_text(branch: dict) -> str:
    facilitation = branch.get("facilitation", {})
    chinese = bool(re.search(r"[\u4e00-\u9fff]", " ".join(str(value) for value in branch.values())))
    labels = (
        ("关键角色", "核心张力", "图像情境", "开场追问")
        if chinese
        else ("Key actors", "Core tension", "Visual brief", "Opening question")
    )
    return "\n\n".join(
        [
            branch.get("what_if", ""),
            branch.get("future_premise", ""),
            f"{labels[0]}: {', '.join(branch.get('key_actors', []))}",
            f"{labels[1]}: {branch.get('core_tension', '')}",
            f"{labels[2]}: {branch.get('visual_brief', '')}",
            f"{labels[3]}: {facilitation.get('opening_question', '')}",
        ]
    )


def parse_json_object(raw_text: str) -> dict | None:
    value = str(raw_text or "").strip()
    if value.startswith("```"):
        value = re.sub(r"^```(?:json)?\s*|\s*```$", "", value, flags=re.IGNORECASE)
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def clean_text(value, limit: int) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())[:limit]


def clean_strings(value, *, minimum: int, maximum: int, item_limit: int) -> list[str]:
    if not isinstance(value, list):
        return []
    result = [clean_text(item, item_limit) for item in value if clean_text(item, item_limit)]
    return result[:maximum] if len(result) >= minimum else []


def fallback_topic(source_context: list[dict]) -> str:
    texts = [str(item.get("text") or "").strip() for item in source_context if item.get("text")]
    # Structured foundation nodes keep their topic on a dedicated line. Prefer it
    # over the full brief so deterministic branches remain concise and do not leak
    # internal field labels into a user-facing What-if premise.
    for text in texts:
        match = re.search(r"^(?:Topic|研究议题)\s*:\s*(.+)$", text, flags=re.MULTILINE)
        if match:
            return clean_text(match.group(1), 180)
    text = " ".join(texts)
    return clean_text(text, 180) or "the current research condition"


def fallback_visual_brief(topic: str, chinese: bool) -> str:
    if chinese:
        return f"一个与“{topic}”有关的可信日常现场，显示角色、制度线索、使用痕迹和一个值得质疑的具体物件；不要做产品广告。"
    return f"A credible everyday scene around {topic}, showing roles, institutional traces, signs of use, and one concrete object worth questioning; not a product advertisement."
