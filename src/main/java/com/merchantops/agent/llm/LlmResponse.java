package com.merchantops.agent.llm;

import com.merchantops.agent.tool.ToolCall;

import java.util.List;

/**
 * LLM 的一次响应：要么给最终答案（content），要么请求调用工具（toolCalls）。
 */
public record LlmResponse(String content, List<ToolCall> toolCalls) {

    public static LlmResponse answer(String content) {
        return new LlmResponse(content, List.of());
    }

    public static LlmResponse toolCalls(List<ToolCall> toolCalls) {
        return new LlmResponse(null, toolCalls);
    }

    /** 是否请求调用工具（true 表示 Agent 还需要继续跑 Loop） */
    public boolean hasToolCalls() {
        return toolCalls != null && !toolCalls.isEmpty();
    }
}
