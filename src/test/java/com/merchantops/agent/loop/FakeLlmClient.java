package com.merchantops.agent.loop;

import com.merchantops.agent.context.Message;
import com.merchantops.agent.llm.LlmClient;
import com.merchantops.agent.llm.LlmResponse;
import com.merchantops.agent.tool.Tool;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.List;
import java.util.Queue;

/**
 * 测试用 LLM：按脚本依次返回预设响应。
 *
 * <p>脚本耗尽后重复最后一条响应（模拟模型固执地反复调用同一个工具，
 * 用于验证 maxSteps 兜底）。同时记录每次请求的消息链，便于断言。</p>
 */
public class FakeLlmClient implements LlmClient {

    private final Queue<LlmResponse> script = new ArrayDeque<>();
    private final List<List<Message>> requests = new ArrayList<>();
    private LlmResponse last;

    public static FakeLlmClient with(LlmResponse... responses) {
        FakeLlmClient client = new FakeLlmClient();
        client.script.addAll(List.of(responses));
        return client;
    }

    @Override
    public LlmResponse chat(List<Message> messages, List<Tool> tools) {
        requests.add(List.copyOf(messages));
        LlmResponse next = script.poll();
        if (next == null) {
            return last; // 脚本耗尽：重复最后一条
        }
        last = next;
        return next;
    }

    /** 第 index 次请求的消息链（index 从 0 开始） */
    public List<Message> requestAt(int index) {
        return requests.get(index);
    }

    public int requestCount() {
        return requests.size();
    }
}
