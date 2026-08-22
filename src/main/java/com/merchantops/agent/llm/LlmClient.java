package com.merchantops.agent.llm;

import com.merchantops.agent.context.Message;
import com.merchantops.agent.tool.Tool;

import java.util.List;

/**
 * LLM 客户端抽象。AgentLoop 只依赖这个接口，不关心具体厂商
 * （生产用 DeepSeek，测试用 Fake，可随时替换）。
 */
public interface LlmClient {

    /**
     * 发起一次对话补全。
     *
     * @param messages 完整消息链（含历史 tool 调用与结果）
     * @param tools    当前可用的工具列表（空表示不启用 Tool Calling）
     * @return 模型响应：最终答案 或 工具调用请求
     */
    LlmResponse chat(List<Message> messages, List<Tool> tools);
}
