"""AgentLoop 单元测试，覆盖核心场景：

1. 直接返回答案（无工具调用）
2. 一次 Tool Call
3. 连续两次 Tool Call
4. 工具不存在（错误回填，Agent 不中断）
5. 超过最大迭代次数（兜底终止）
6. 工具参数非法（错误回填）
7. 工具执行抛异常（错误回填）
"""

import pytest

from app.agent.llm import LlmResponse
from app.agent.loop import AgentLoop
from app.agent.registry import ToolRegistry
from app.agent.tool import ToolCall
from app.tools.mock_tools import GetMerchantTool, GetTaskTool

from .fake_llm import FakeLlmClient

MAX_STEPS = 10


@pytest.fixture
def registry() -> ToolRegistry:
    return ToolRegistry([GetMerchantTool(), GetTaskTool()])


def make_loop(llm: FakeLlmClient, registry: ToolRegistry, max_steps: int = MAX_STEPS) -> AgentLoop:
    return AgentLoop(llm, registry, max_steps=max_steps)


# ---------- 场景 1：直接返回答案 ----------

def test_direct_answer_no_tool_call(registry):
    llm = FakeLlmClient.with_responses(LlmResponse(content="商户运营数据正常"))
    result = make_loop(llm, registry).run("今天数据怎么样")

    assert result.answer == "商户运营数据正常"
    assert not result.max_steps_reached
    assert result.steps == 1          # 只调了一次 LLM
    assert llm.request_count == 1


# ---------- 场景 2：一次 Tool Call ----------

def test_single_tool_call_merchant_lookup(registry):
    llm = FakeLlmClient.with_responses(
        LlmResponse(tool_calls=[ToolCall(id="call_1", name="getMerchant", arguments='{"merchantId":"M1001"}')]),
        LlmResponse(content="商户 M1001 是金牌商户，状态正常"),
    )
    result = make_loop(llm, registry).run("查一下商户 M1001")

    assert result.answer == "商户 M1001 是金牌商户，状态正常"
    assert result.steps == 2          # 两轮 LLM
    assert llm.request_count == 2

    # 第二轮请求必须包含 tool 结果消息（回填成功）
    second = llm.request_at(1)
    tool_msg = next(m for m in second if m.role == "tool")
    assert "M1001" in tool_msg.content
    assert "金牌" in tool_msg.content


# ---------- 场景 3：连续两次 Tool Call ----------

def test_two_consecutive_tool_calls(registry):
    llm = FakeLlmClient.with_responses(
        LlmResponse(tool_calls=[ToolCall(id="call_1", name="getMerchant", arguments='{"merchantId":"M1001"}')]),
        LlmResponse(tool_calls=[ToolCall(id="call_2", name="getTask", arguments='{"taskId":"T-2001"}')]),
        LlmResponse(content="商户 M1001 状态正常，关联任务 T-2001 处理中"),
    )
    result = make_loop(llm, registry).run("查商户 M1001 的任务情况")

    assert result.answer == "商户 M1001 状态正常，关联任务 T-2001 处理中"
    assert result.steps == 3          # 三轮 LLM
    assert llm.request_count == 3

    # 消息链必须完整：两次工具结果都在
    tool_msg_count = sum(1 for m in result.messages if m.role == "tool")
    assert tool_msg_count == 2

    # 第三轮请求应包含两个工具结果
    third = llm.request_at(2)
    assert sum(1 for m in third if m.role == "tool") == 2


# ---------- 场景 4：工具不存在 ----------

def test_tool_not_found_error_fed_back_to_llm(registry):
    llm = FakeLlmClient.with_responses(
        LlmResponse(tool_calls=[ToolCall(id="call_1", name="notExistTool", arguments="{}")]),
        LlmResponse(content="抱歉，我没有可用的工具来完成这个查询"),
    )
    result = make_loop(llm, registry).run("用不存在的工具查一下")

    assert result.answer == "抱歉，我没有可用的工具来完成这个查询"
    # Agent 没有中断：第二轮 LLM 收到了错误回填，仍能正常应答
    assert llm.request_count == 2

    # 错误信息作为 tool 消息回填给 LLM
    second = llm.request_at(1)
    error_msg = next(m for m in second if m.role == "tool")
    assert "工具不存在" in error_msg.content


# ---------- 场景 5：超过最大迭代次数 ----------

def test_max_steps_reached_loop_stops(registry):
    # 模型每次都请求同一个工具（脚本耗尽后重复最后一条），模拟死循环
    llm = FakeLlmClient.with_responses(
        LlmResponse(tool_calls=[ToolCall(id="call_1", name="getMerchant", arguments="{}")]),
        LlmResponse(tool_calls=[ToolCall(id="call_2", name="getMerchant", arguments="{}")]),
    )
    loop = make_loop(llm, registry, max_steps=3)  # 故意设小
    result = loop.run("一直查下去")

    assert result.max_steps_reached
    assert result.steps == 3          # 恰好停在 max_steps
    assert "3" in result.answer       # 兜底文案提到轮数


# ---------- 场景 6：工具参数非法（JSON 解析失败） ----------

def test_tool_argument_error_fed_back_to_llm(registry):
    llm = FakeLlmClient.with_responses(
        LlmResponse(tool_calls=[ToolCall(id="call_1", name="getMerchant", arguments="invalid-json")]),
        LlmResponse(content="工具执行出错了"),
    )
    result = make_loop(llm, registry).run("触发异常")

    assert result.answer == "工具执行出错了"
    second = llm.request_at(1)
    error_msg = next(m for m in second if m.role == "tool")
    assert "参数非法" in error_msg.content      # 精确分类：参数非法，而非笼统的"执行异常"


# ---------- 场景 7：工具执行抛异常 ----------

def test_tool_execution_exception_error_fed_back_to_llm(registry):
    # getTask 参数合法但内部抛运行时异常 → 归为"工具执行异常"
    class BoomTool(GetTaskTool):
        def execute(self, arguments_json: str) -> str:
            raise RuntimeError("内部故障")

    boom_registry = ToolRegistry([GetMerchantTool(), BoomTool()])
    llm = FakeLlmClient.with_responses(
        LlmResponse(tool_calls=[ToolCall(id="call_1", name="getTask", arguments='{"taskId":"T1"}')]),
        LlmResponse(content="工具执行出错了"),
    )
    result = make_loop(llm, boom_registry).run("触发异常")

    assert result.answer == "工具执行出错了"
    second = llm.request_at(1)
    error_msg = next(m for m in second if m.role == "tool")
    assert "工具执行异常" in error_msg.content
