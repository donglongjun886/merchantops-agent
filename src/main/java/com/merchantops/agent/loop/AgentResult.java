package com.merchantops.agent.loop;

import com.merchantops.agent.context.AgentContext;
import com.merchantops.agent.context.Message;

import java.util.List;

/**
 * Agent 一次运行的最终结果。
 *
 * @param answer          最终答案
 * @param steps           实际消耗的 LLM 调用轮数
 * @param maxStepsReached 是否因超过最大迭代次数而终止
 * @param messages        完整消息链（便于排查/测试）
 */
public record AgentResult(String answer, int steps, boolean maxStepsReached, List<Message> messages) {

    public static AgentResult finalAnswer(String answer, int steps, AgentContext ctx) {
        return new AgentResult(answer, steps, false, ctx.messages());
    }

    public static AgentResult maxStepsReached(String answer, int steps, AgentContext ctx) {
        return new AgentResult(answer, steps, true, ctx.messages());
    }
}
