package com.merchantops.agent.tool;

/**
 * 一次工具调用的执行结果。
 *
 * @param toolCallId 对应的 ToolCall ID
 * @param name       工具名
 * @param content    执行结果（JSON 字符串）；失败时为错误描述
 * @param isError    是否执行失败（工具不存在 / 抛异常）
 */
public record ToolResult(String toolCallId, String name, String content, boolean isError) {
}
