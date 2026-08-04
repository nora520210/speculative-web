from server.agent_guide import build_agent_guide_prompt, generate_agent_guide


def test_agent_guide_prompt_compacts_large_context():
    prompt = build_agent_guide_prompt(
        {
            "stage": "frame_focus",
            "pending_field": "research_focus",
            "brief": {"topic": "A", "research_focus": "x" * 12000},
            "history": [{"role": "user", "body": "y" * 12000}],
        }
    )
    assert len(prompt) < 3600
    assert "x" * 5000 not in prompt


def test_agent_guide_uses_small_output_budget():
    import server.agent_guide as agent_guide

    captured = {}
    original = agent_guide.generate_modify_response

    def fake_generate(prompt, api_key=None, max_output_tokens=1200):
        captured["max_output_tokens"] = max_output_tokens
        return {"provider": "test", "model": "test-model", "text": '{"question":"Q","options":["A"],"hint":"H"}'}

    agent_guide.generate_modify_response = fake_generate
    try:
        result = generate_agent_guide({"stage": "start"}, api_key="test")
        assert result["question"] == "Q"
        assert captured["max_output_tokens"] == 360
    finally:
        agent_guide.generate_modify_response = original
