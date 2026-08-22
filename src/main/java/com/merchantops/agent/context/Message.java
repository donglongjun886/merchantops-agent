package com.merchantops.agent.context;

import com.merchantops.agent.tool.ToolCall;

import java.util.List;

/**
 * 一条对话消息。OpenAI 兼容的四种角色：system / user / assistant / tool。
 *
 * <p>assistant 消息可能带 tool_calls（模型请求调用工具），此时 content 通常为 null；
 * tool 消息通过 toolCallId 关联它响应的那次调用。</p>
 */
public record Message(String role, String content, String toolCallId, List<ToolCall> toolCalls) {

    public static Message system(String content) {
        return new Message("system", content, null, null);
    }

    public static Message user(String content) {
        return new Message("user", content, null, null);
    }

    public static Message assistant(String content, List<ToolCall> toolCalls) {
        return new Message("assistant", content, null, toolCalls);
    }

    public static Message tool(String toolCallId, String content) {
        return new Message("tool", content, toolCallId, null);
    }
}
