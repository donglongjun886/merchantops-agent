package com.merchantops.agent.loop;

import com.merchantops.agent.context.AgentContext;
import com.merchantops.agent.context.Message;
import com.merchantops.agent.llm.LlmClient;
import com.merchantops.agent.llm.LlmResponse;
import com.merchantops.agent.tool.Tool;
import com.merchantops.agent.tool.ToolCall;
import com.merchantops.agent.tool.ToolNotFoundException;
import com.merchantops.agent.tool.ToolRegistry;
import com.merchantops.agent.tool.ToolResult;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.util.List;

/**
 * 最小 Agent Loop。
 *
 * <pre>
 * 用户输入
 *   ↓
 * [循环] 组装全量消息链 → 调 LLM（附带可用工具声明）
 *   ↓
 * LLM 返回 tool_calls ？
 *   ├─ 否 → 拿到最终答案，结束
 *   └─ 是 → 逐个执行工具，结果回填消息链 → 回到 [循环]
 * </pre>
 *
 * <p>关键设计：AgentLoop 不写死任何具体工具，全部通过 {@link ToolRegistry}
 * 按名动态查找；执行失败（工具不存在/异常）也回填给 LLM 让它纠错，
 * 而不是中断整个 Agent。maxSteps 兜底防止死循环。</p>
 */
@Slf4j
@Component
public class AgentLoop {

    private static final String SYSTEM_PROMPT = """
            你是 MerchantOps 运营助手，帮助运营人员查询商户与任务信息。
            当用户的问题需要数据支撑时，调用可用的工具获取数据后再回答。
            只回答与商户运营相关的问题。
            """;

    private final LlmClient llmClient;
    private final ToolRegistry toolRegistry;
    private final int maxSteps;

    public AgentLoop(LlmClient llmClient,
                     ToolRegistry toolRegistry,
                     @Value("${merchantops.llm.max-steps:10}") int maxSteps) {
        this.llmClient = llmClient;
        this.toolRegistry = toolRegistry;
        this.maxSteps = maxSteps;
    }

    /**
     * 运行一次 Agent 会话，返回最终答案。
     *
     * @param userInput 用户自然语言输入
     */
    public AgentResult run(String userInput) {
        AgentContext ctx = new AgentContext(SYSTEM_PROMPT);
        ctx.addUserMessage(userInput);

        for (int step = 1; step <= maxSteps; step++) {
            log.info("[AgentLoop] step={}/{} messages={}", step, maxSteps, ctx.size());

            // 1. 调 LLM：传入全量消息链 + 当前可用工具声明
            List<Tool> tools = toolRegistry.all();
            LlmResponse response = llmClient.chat(ctx.messages(), tools);

            // 2. 没有 tool_calls → 这就是最终答案
            if (!response.hasToolCalls()) {
                String answer = response.content();
                ctx.addAssistantMessage(answer, null);
                log.info("[AgentLoop] 得到最终答案: {}", answer);
                return AgentResult.finalAnswer(answer, step, ctx);
            }

            // 3. 有 tool_calls → 记录 assistant 消息，逐个执行工具
            ctx.addAssistantMessage(null, response.toolCalls());
            for (ToolCall call : response.toolCalls()) {
                ToolResult result = executeTool(call);
                log.info("[AgentLoop] tool={} result={}", call.name(), result.content());
                ctx.addToolResult(result); // 工具结果回填消息链 → 下一轮 LLM 能看到
            }
            // 继续循环，让 LLM 基于工具结果给出下一步（或最终答案）
        }

        // 4. 超限兜底
        log.warn("[AgentLoop] 超过最大迭代次数 maxSteps={}", maxSteps);
        String fallback = "抱歉，我已经尝试了 " + maxSteps + " 轮仍未能完成，请换个问法或简化问题。";
        ctx.addAssistantMessage(fallback, null);
        return AgentResult.maxStepsReached(fallback, maxSteps, ctx);
    }

    /** 执行单个工具调用；任何失败都转为 error ToolResult 回填，不中断 Loop */
    private ToolResult executeTool(ToolCall call) {
        try {
            Tool tool = toolRegistry.get(call.name());
            String content = tool.execute(call.arguments());
            return new ToolResult(call.id(), call.name(), content, false);
        } catch (ToolNotFoundException e) {
            log.warn("工具不存在: {}", call.name());
            return new ToolResult(call.id(), call.name(),
                    "{\"error\":\"工具不存在: " + call.name() + "\"}", true);
        } catch (Exception e) {
            log.warn("工具执行异常: {} {}", call.name(), e.getMessage());
            return new ToolResult(call.id(), call.name(),
                    "{\"error\":\"工具执行异常: " + e.getMessage() + "\"}", true);
        }
    }
}
