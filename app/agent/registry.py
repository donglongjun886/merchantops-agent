"""工具注册表：按名称动态查找工具。AgentLoop 通过它拿到工具，不写死任何具体 Tool。"""

from .tool import Tool, ToolNotFound


class ToolRegistry:
    def __init__(self, tools: list[Tool] | None = None):
        self._tools: dict[str, Tool] = {}
        for tool in tools or []:
            self.register(tool)

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        """按名查找；不存在抛 ToolNotFound。"""
        tool = self._tools.get(name)
        if tool is None:
            raise ToolNotFound(name)
        return tool

    def all(self) -> list[Tool]:
        """当前全部工具（AgentLoop 每次调用 LLM 时把可用工具声明传进去）。"""
        return list(self._tools.values())
