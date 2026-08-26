"""Agent 工具抽象：Tool / ToolCall / ToolResult / ToolNotFound。"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


class ToolNotFound(Exception):
    """工具不存在异常。AgentLoop 捕获后构造 error ToolResult 回填给 LLM。"""

    def __init__(self, name: str):
        super().__init__(f"工具不存在: {name}")


@dataclass
class ToolCall:
    """一次工具调用请求（由 LLM 在 assistant 消息中发起）。"""

    id: str                  # OpenAI 分配的调用 ID，tool 结果通过它回填
    name: str                # 工具名（如 getMerchant）
    arguments: str           # 工具参数，JSON 字符串（如 {"merchantId":"M1001"}）


@dataclass
class ToolResult:
    """一次工具调用的执行结果。"""

    tool_call_id: str        # 对应的 ToolCall ID
    name: str                # 工具名
    content: str             # 执行结果（JSON 字符串）；失败时为错误描述
    is_error: bool           # 是否执行失败（工具不存在 / 抛异常）


class Tool(ABC):
    """Agent 可调用工具的统一抽象。

    AgentLoop 不知道任何具体工具，只通过 ToolRegistry 按 name 查找并执行，
    因此新增工具 = 新增一个实现类并注册，不动 Agent 核心代码。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """工具名（LLM 通过它发起调用），如 getMerchant。"""

    @property
    @abstractmethod
    def description(self) -> str:
        """给 LLM 看的工具说明，帮助模型判断何时调用。"""

    @property
    def parameters_json(self) -> str:
        """参数 JSON Schema（给 LLM 的 tools 声明），默认空对象。"""
        return '{"type":"object","properties":{}}'

    @abstractmethod
    def execute(self, arguments_json: str) -> str:
        """执行工具。返回结果 JSON 字符串，回填给 LLM。"""
