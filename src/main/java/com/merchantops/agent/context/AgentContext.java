package com.merchantops.agent.context;

import com.merchantops.agent.tool.ToolCall;
import com.merchantops.agent.tool.ToolResult;

import java.util.ArrayList;
import java.util.List;

/**
 * Agent 上下文：保存完整消息链（system + user + assistant + tool）。
 *
 * <p>每轮 LLM 调用都传入全量消息，让模型"看到"它之前说了什么、调用了什么工具、
 * 拿到了什么结果——这是多轮 Tool Calling 能正确推进的基础。</p>
 */
public class AgentContext {

    private final List<Message> messages = new ArrayList<>();

    public AgentContext(String systemPrompt) {
        messages.add(Message.system(systemPrompt));
    }

    public void addUserMessage(String content) {
        messages.add(Message.user(content));
    }

    public void addAssistantMessage(String content, List<ToolCall> toolCalls) {
        messages.add(Message.assistant(content, toolCalls));
    }

    /** 把一次工具执行结果回填为 tool 消息（OpenAI 要求用 toolCallId 关联） */
    public void addToolResult(ToolResult result) {
        messages.add(Message.tool(result.toolCallId(), result.content()));
    }

    /** 全量消息快照（不可变副本） */
    public List<Message> messages() {
        return List.copyOf(messages);
    }

    public int size() {
        return messages.size();
    }
}
