"""LLM 客户端抽象：LlmClient（ABC）+ LlmResponse + DeepSeekClient 实现。"""

from abc import ABC, abstractmethod
import json
from dataclasses import dataclass, field
from typing import Optional

from openai import OpenAI

from .context import Message
from .tool import Tool, ToolCall


@dataclass
class LlmResponse:
    """LLM 的一次响应：要么给最终答案（content），要么请求调用工具（tool_calls）。"""

    content: Optional[str] = None
    tool_calls: list[ToolCall] = field(default_factory=list)

    def has_tool_calls(self) -> bool:
        """是否请求调用工具（true 表示 Agent 还需要继续跑 Loop）。"""
        return bool(self.tool_calls)


class LlmClient(ABC):
    """LLM 客户端抽象。AgentLoop 只依赖这个接口，不关心具体厂商。

    生产用 DeepSeekClient，测试用 FakeLlmClient，可随时替换。
    """

    @abstractmethod
    def chat(self, messages: list[Message], tools: list[Tool]) -> LlmResponse:
        """发起一次对话补全。

        Args:
            messages: 完整消息链（含历史 tool 调用与结果）。
            tools: 当前可用的工具列表（空表示不启用 Tool Calling）。

        Returns:
            模型响应：最终答案 或 工具调用请求。
        """


class DeepSeekClient(LlmClient):
    """DeepSeek LLM 客户端（官方推荐 openai SDK，base_url 指向 DeepSeek）。"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.deepseek.com",
        model: str = "deepseek-v4-flash",
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ):
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens

    def chat(self, messages: list[Message], tools: list[Tool]) -> LlmResponse:
        oai_messages = [self._to_openai_message(m) for m in messages]
        oai_tools = [self._to_openai_tool(t) for t in tools] if tools else None

        kwargs: dict = {
            "model": self._model,
            "messages": oai_messages,
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
        }
        if oai_tools:
            kwargs["tools"] = oai_tools

        resp = self._client.chat.completions.create(**kwargs)
        msg = resp.choices[0].message

        # 翻译 tool_calls → 内部 ToolCall
        tool_calls: list[ToolCall] = []
        for tc in msg.tool_calls or []:
            tool_calls.append(ToolCall(id=tc.id, name=tc.function.name, arguments=tc.function.arguments))

        if tool_calls:
            return LlmResponse(tool_calls=tool_calls)
        return LlmResponse(content=msg.content)

    @staticmethod
    def _to_openai_message(m: Message) -> dict:
        msg: dict = {"role": m.role}
        if m.content is not None:
            msg["content"] = m.content
        if m.tool_call_id is not None:
            msg["tool_call_id"] = m.tool_call_id
        if m.tool_calls:
            msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.name, "arguments": tc.arguments},
                }
                for tc in m.tool_calls
            ]
        return msg

    @staticmethod
    def _to_openai_tool(t: Tool) -> dict:
        return {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                # openai SDK 要求 parameters 是 dict，不是 JSON 字符串
                "parameters": json.loads(t.parameters_json),
            },
        }
