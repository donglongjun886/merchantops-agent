package com.merchantops.agent.tool;

/**
 * 一次工具调用请求（由 LLM 在 assistant 消息中发起）。
 *
 * @param id        OpenAI 分配的调用 ID，tool 结果通过它回填
 * @param name      工具名（如 getMerchant）
 * @param arguments 工具参数，JSON 字符串（如 {"merchantId":"M1001"}）
 */
public record ToolCall(String id, String name, String arguments) {
}
