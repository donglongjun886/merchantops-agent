package com.merchantops.agent.loop;

import com.merchantops.agent.context.Message;
import com.merchantops.agent.llm.LlmResponse;
import com.merchantops.agent.tool.ToolCall;
import com.merchantops.agent.tool.ToolRegistry;
import com.merchantops.agent.tool.mock.GetMerchantTool;
import com.merchantops.agent.tool.mock.GetTaskTool;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

/**
 * AgentLoop 单元测试，覆盖核心场景：
 * 1. 直接返回答案（无工具调用）
 * 2. 一次 Tool Call
 * 3. 连续两次 Tool Call
 * 4. 工具不存在（错误回填，Agent 不中断）
 * 5. 超过最大迭代次数（兜底终止）
 */
class AgentLoopTest {

    private static final int MAX_STEPS = 10;

    private ToolRegistry registry;
    private GetMerchantTool merchantTool;
    private GetTaskTool taskTool;

    @BeforeEach
    void setUp() {
        merchantTool = new GetMerchantTool();
        taskTool = new GetTaskTool();
        registry = new ToolRegistry(List.of(merchantTool, taskTool));
    }

    private AgentLoop loop(FakeLlmClient llm) {
        return new AgentLoop(llm, registry, MAX_STEPS);
    }

    // ---------- 场景 1：直接返回答案 ----------

    @Test
    void directAnswer_noToolCall() {
        FakeLlmClient llm = FakeLlmClient.with(LlmResponse.answer("商户运营数据正常"));
        AgentResult result = loop(llm).run("今天数据怎么样");

        assertEquals("商户运营数据正常", result.answer());
        assertFalse(result.maxStepsReached());
        assertEquals(1, result.steps());          // 只调了一次 LLM
        assertEquals(1, llm.requestCount());
    }

    // ---------- 场景 2：一次 Tool Call ----------

    @Test
    void singleToolCall_merchantLookup() {
        FakeLlmClient llm = FakeLlmClient.with(
                LlmResponse.toolCalls(List.of(new ToolCall("call_1", "getMerchant", "{\"merchantId\":\"M1001\"}"))),
                LlmResponse.answer("商户 M1001 是金牌商户，状态正常")
        );
        AgentResult result = loop(llm).run("查一下商户 M1001");

        assertEquals("商户 M1001 是金牌商户，状态正常", result.answer());
        assertEquals(2, result.steps());          // 两轮 LLM
        assertEquals(2, llm.requestCount());

        // 第二轮请求必须包含 tool 结果消息（回填成功）
        List<Message> second = llm.requestAt(1);
        Message toolMsg = second.stream().filter(m -> m.role().equals("tool")).findFirst().orElseThrow();
        assertTrue(toolMsg.content().contains("M1001"));
        assertTrue(toolMsg.content().contains("金牌"));
    }

    // ---------- 场景 3：连续两次 Tool Call ----------

    @Test
    void twoConsecutiveToolCalls() {
        FakeLlmClient llm = FakeLlmClient.with(
                LlmResponse.toolCalls(List.of(new ToolCall("call_1", "getMerchant", "{\"merchantId\":\"M1001\"}"))),
                LlmResponse.toolCalls(List.of(new ToolCall("call_2", "getTask", "{\"taskId\":\"T-2001\"}"))),
                LlmResponse.answer("商户 M1001 状态正常，关联任务 T-2001 处理中")
        );
        AgentResult result = loop(llm).run("查商户 M1001 的任务情况");

        assertEquals("商户 M1001 状态正常，关联任务 T-2001 处理中", result.answer());
        assertEquals(3, result.steps());          // 三轮 LLM
        assertEquals(3, llm.requestCount());

        // 消息链必须完整：两次工具结果都在
        long toolMsgCount = result.messages().stream().filter(m -> m.role().equals("tool")).count();
        assertEquals(2, toolMsgCount);

        // 第三轮请求应包含两个工具结果
        List<Message> third = llm.requestAt(2);
        assertEquals(2, third.stream().filter(m -> m.role().equals("tool")).count());
    }

    // ---------- 场景 4：工具不存在 ----------

    @Test
    void toolNotFound_errorFedBackToLlm() {
        FakeLlmClient llm = FakeLlmClient.with(
                LlmResponse.toolCalls(List.of(new ToolCall("call_1", "notExistTool", "{}"))),
                LlmResponse.answer("抱歉，我没有可用的工具来完成这个查询")
        );
        AgentResult result = loop(llm).run("用不存在的工具查一下");

        assertEquals("抱歉，我没有可用的工具来完成这个查询", result.answer());
        // Agent 没有中断：第二轮 LLM 收到了错误回填，仍能正常应答
        assertEquals(2, llm.requestCount());

        // 错误信息作为 tool 消息回填给 LLM
        List<Message> second = llm.requestAt(1);
        Message errorMsg = second.stream().filter(m -> m.role().equals("tool")).findFirst().orElseThrow();
        assertTrue(errorMsg.content().contains("工具不存在"));
    }

    // ---------- 场景 5：超过最大迭代次数 ----------

    @Test
    void maxStepsReached_loopStops() {
        // 模型每次都请求同一个工具（脚本耗尽后重复最后一条），模拟死循环
        FakeLlmClient llm = FakeLlmClient.with(
                LlmResponse.toolCalls(List.of(new ToolCall("call_1", "getMerchant", "{}"))),
                LlmResponse.toolCalls(List.of(new ToolCall("call_2", "getMerchant", "{}")))
        );
        AgentLoop loop = new AgentLoop(llm, registry, 3); // 故意设小
        AgentResult result = loop.run("一直查下去");

        assertTrue(result.maxStepsReached());
        assertEquals(3, result.steps());          // 恰好停在 maxSteps
        assertTrue(result.answer().contains("3")); // 兜底文案提到轮数
    }

    // ---------- 场景 6（附加）：工具执行抛异常 ----------

    @Test
    void toolExecutionException_errorFedBackToLlm() {
        FakeLlmClient llm = FakeLlmClient.with(
                LlmResponse.toolCalls(List.of(new ToolCall("call_1", "getMerchant", "invalid-json"))),
                LlmResponse.answer("工具执行出错了")
        );
        AgentResult result = loop(llm).run("触发异常");

        assertEquals("工具执行出错了", result.answer());
        List<Message> second = llm.requestAt(1);
        Message errorMsg = second.stream().filter(m -> m.role().equals("tool")).findFirst().orElseThrow();
        assertTrue(errorMsg.content().contains("工具执行异常"));
    }
}
