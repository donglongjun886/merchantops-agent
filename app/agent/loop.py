"""最小 Agent Loop。

    用户输入
      ↓
    [循环] 组装全量消息链 → 调 LLM（附带可用工具声明）
      ↓
    LLM 返回 tool_calls ？
      ├─ 否 → 拿到最终答案，结束
      └─ 是 → 逐个执行工具，结果回填消息链 → 回到 [循环]

关键设计：AgentLoop 不写死任何具体工具，全部通过 ToolRegistry 按名动态查找；
执行失败（工具不存在/异常）也回填给 LLM 让它纠错，而不是中断整个 Agent。
max_steps 兜底防止死循环。
"""

import logging
from dataclasses import dataclass, field

from .context import AgentContext, Message
from .llm import LlmClient
from .registry import ToolRegistry
from .tool import ToolCall, ToolNotFound, ToolResult

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是 MerchantOps 运营助手，帮助运营人员查询商户与任务信息。
当用户的问题需要数据支撑时，调用可用的工具获取数据后再回答。
只回答与商户运营相关的问题。"""


@dataclass
class AgentResult:
    """Agent 一次运行的最终结果。"""

    answer: str
    steps: int                       # 实际消耗的 LLM 调用轮数
    max_steps_reached: bool          # 是否因超过最大迭代次数而终止
    messages: list[Message] = field(default_factory=list)  # 完整消息链（便于排查/测试）


class AgentLoop:
    def __init__(self, llm_client: LlmClient, tool_registry: ToolRegistry, max_steps: int = 10):
        self._llm_client = llm_client
        self._tool_registry = tool_registry
        self._max_steps = max_steps

    def run(self, user_input: str) -> AgentResult:
        """运行一次 Agent 会话，返回最终答案。"""
        ctx = AgentContext(SYSTEM_PROMPT)
        ctx.add_user_message(user_input)

        for step in range(1, self._max_steps + 1):
            logger.info("[AgentLoop] step=%s/%s messages=%s", step, self._max_steps, ctx.size())

            # 1. 调 LLM：传入全量消息链 + 当前可用工具声明
            response = self._llm_client.chat(ctx.messages(), self._tool_registry.all())

            # 2. 没有 tool_calls → 这就是最终答案
            if not response.has_tool_calls():
                answer = response.content
                ctx.add_assistant_message(answer, None)
                logger.info("[AgentLoop] 得到最终答案: %s", answer)
                return AgentResult(answer=answer, steps=step, max_steps_reached=False, messages=ctx.messages())

            # 3. 有 tool_calls → 记录 assistant 消息，逐个执行工具
            ctx.add_assistant_message(None, response.tool_calls)
            for call in response.tool_calls:
                result = self._execute_tool(call)
                logger.info("[AgentLoop] tool=%s result=%s", call.name, result.content)
                ctx.add_tool_result(result)  # 工具结果回填消息链 → 下一轮 LLM 能看到

            # 继续循环，让 LLM 基于工具结果给出下一步（或最终答案）

        # 4. 超限兜底
        logger.warning("[AgentLoop] 超过最大迭代次数 max_steps=%s", self._max_steps)
        fallback = f"抱歉，我已经尝试了 {self._max_steps} 轮仍未能完成，请换个问法或简化问题。"
        ctx.add_assistant_message(fallback, None)
        return AgentResult(answer=fallback, steps=self._max_steps, max_steps_reached=True, messages=ctx.messages())

    def _execute_tool(self, call: ToolCall) -> ToolResult:
        """执行单个工具调用；任何失败都转为 error ToolResult 回填，不中断 Loop。"""
        try:
            tool = self._tool_registry.get(call.name)
            content = tool.execute(call.arguments)
            return ToolResult(tool_call_id=call.id, name=call.name, content=content, is_error=False)
        except ToolNotFound:
            logger.warning("工具不存在: %s", call.name)
            return ToolResult(
                tool_call_id=call.id,
                name=call.name,
                content=f'{{"error":"工具不存在: {call.name}"}}',
                is_error=True,
            )
        except Exception as exc:
            logger.warning("工具执行异常: %s %s", call.name, exc)
            return ToolResult(
                tool_call_id=call.id,
                name=call.name,
                content=f'{{"error":"工具执行异常: {exc}"}}',
                is_error=True,
            )
