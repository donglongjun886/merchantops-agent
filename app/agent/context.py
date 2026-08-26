"""Agent 上下文：保存完整消息链（system + user + assistant + tool）。"""

from dataclasses import dataclass, field
from typing import Optional

from .tool import ToolCall, ToolResult


@dataclass
class Message:
    """一条对话消息。OpenAI 兼容的四种角色：system / user / assistant / tool。

    assistant 消息可能带 tool_calls（模型请求调用工具），此时 content 通常为 None；
    tool 消息通过 tool_call_id 关联它响应的那次调用。
    """

    role: str
    content: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_calls: Optional[list[ToolCall]] = None

    @classmethod
    def system(cls, content: str) -> "Message":
        return cls(role="system", content=content)

    @classmethod
    def user(cls, content: str) -> "Message":
        return cls(role="user", content=content)

    @classmethod
    def assistant(cls, content: Optional[str], tool_calls: Optional[list[ToolCall]]) -> "Message":
        return cls(role="assistant", content=content, tool_calls=tool_calls)

    @classmethod
    def tool(cls, tool_call_id: str, content: str) -> "Message":
        return cls(role="tool", content=content, tool_call_id=tool_call_id)


class AgentContext:
    """保存完整消息链，每轮 LLM 调用都传入全量消息。

    让模型"看到"它之前说了什么、调用了什么工具、拿到了什么结果——
    这是多轮 Tool Calling 能正确推进的基础。
    """

    def __init__(self, system_prompt: str):
        self._messages: list[Message] = [Message.system(system_prompt)]

    def add_user_message(self, content: str) -> None:
        self._messages.append(Message.user(content))

    def add_assistant_message(self, content: Optional[str], tool_calls: Optional[list[ToolCall]]) -> None:
        self._messages.append(Message.assistant(content, tool_calls))

    def add_tool_result(self, result: ToolResult) -> None:
        """把一次工具执行结果回填为 tool 消息（OpenAI 要求用 tool_call_id 关联）。"""
        self._messages.append(Message.tool(result.tool_call_id, result.content))

    def messages(self) -> list[Message]:
        """全量消息快照（不可变副本）。"""
        return list(self._messages)

    def size(self) -> int:
        return len(self._messages)
