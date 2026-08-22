package com.merchantops.agent.tool;

/**
 * 工具不存在异常。AgentLoop 捕获后构造 error ToolResult 回填给 LLM，
 * 让模型有机会纠正（比如换个参数或换一个存在的工具）。
 */
public class ToolNotFoundException extends RuntimeException {

    public ToolNotFoundException(String name) {
        super("工具不存在: " + name);
    }
}
