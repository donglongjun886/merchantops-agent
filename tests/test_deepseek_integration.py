"""真实 DeepSeek 集成测试。

运行前提：.env 里配置了 DEEPSEEK_API_KEY。
无 Key 时自动 skip（不影响 CI / 离线开发）。

运行方式：
    .venv/bin/python -m pytest tests/test_deepseek_integration.py -v

注意：这是真实 API 调用，会产生少量费用。
"""

import os

import pytest

from app.agent.llm import DeepSeekClient
from app.agent.loop import AgentLoop
from app.agent.registry import ToolRegistry
from app.tools.merchant_tool import GetMerchantTool
from app.tools.order_tool import GetOrderTool
from app.tools.task_tool import GetTaskTool

pytestmark = [
    pytest.mark.integration,  # 默认不跑，-m integration 才执行
    pytest.mark.skipif(
        not os.environ.get("DEEPSEEK_API_KEY"),
        reason="未配置 DEEPSEEK_API_KEY，跳过真实集成测试",
    ),
]


@pytest.fixture(scope="module")
def client() -> DeepSeekClient:
    return DeepSeekClient(
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        model=os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash"),
    )


def test_llm_returns_answer(client):
    """场景 1：无工具直接返回答案。"""
    from app.agent.context import Message

    response = client.chat(
        [Message.system("你是一个简短助手"), Message.user("说一个字：好")],
        tools=[],
    )
    assert response.content is not None
    assert not response.has_tool_calls()


def test_real_tool_calling_merchant_then_task():
    """场景 2：真实链路——用户问商家+任务完成度，DeepSeek 应连续调用工具后给最终答案。

    期望：getMerchant(按ID查商家) → getTask(按商家查任务列表) → Final Answer
    """
    from app.config import settings

    llm = DeepSeekClient(
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url=os.environ.get("DEEPSEEK_BASE_URL", settings.deepseek_base_url),
        model=os.environ.get("DEEPSEEK_MODEL", settings.deepseek_model),
    )
    registry = ToolRegistry([GetMerchantTool(), GetTaskTool(), GetOrderTool()])
    loop = AgentLoop(llm, registry, max_steps=5)

    result = loop.run("先查询商家 1 的基本信息，再分析它的 GMV 任务完成度")

    assert not result.max_steps_reached
    assert result.steps >= 2          # 至少两轮：工具调用 + 最终答案
    assert result.answer              # 有最终答案

    # 消息链中应出现过 getMerchant 和 getTask 两个工具调用
    roles_and_tools = []
    for msg in result.messages:
        if msg.role == "assistant" and msg.tool_calls:
            roles_and_tools.extend(tc.name for tc in msg.tool_calls)
    assert "getMerchant" in roles_and_tools, f"未调用 getMerchant，实际调用: {roles_and_tools}"
    assert "getTask" in roles_and_tools, f"未调用 getTask，实际调用: {roles_and_tools}"
