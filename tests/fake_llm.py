"""测试用 LLM：按脚本依次返回预设响应。

脚本耗尽后重复最后一条响应（模拟模型固执地反复调用同一个工具，
用于验证 max_steps 兜底）。同时记录每次请求的消息链，便于断言。
"""

from collections import deque

from app.agent.context import Message
from app.agent.llm import LlmClient, LlmResponse
from app.agent.tool import Tool


class FakeLlmClient(LlmClient):
    def __init__(self, *responses: LlmResponse):
        self._script: deque[LlmResponse] = deque(responses)
        self._last: LlmResponse | None = None
        self._requests: list[list[Message]] = []

    @classmethod
    def with_responses(cls, *responses: LlmResponse) -> "FakeLlmClient":
        return cls(*responses)

    def chat(self, messages: list[Message], tools: list[Tool]) -> LlmResponse:
        self._requests.append(list(messages))
        if self._script:
            self._last = self._script.popleft()
        assert self._last is not None, "FakeLlmClient 没有预设响应"
        return self._last

    def request_at(self, index: int) -> list[Message]:
        """第 index 次请求的消息链（index 从 0 开始）。"""
        return self._requests[index]

    @property
    def request_count(self) -> int:
        return len(self._requests)
