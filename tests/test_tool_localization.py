from server.modifier_registry import public_modifier_tools


def test_each_tool_package_exposes_package_owned_chinese_display_copy():
    tools = public_modifier_tools()
    assert tools
    for tool in tools:
        chinese = tool.get("locales", {}).get("zh", {})
        assert tool.get("package_path", "").startswith("tool_packages/")
        assert chinese.get("label")
        assert chinese.get("description")
