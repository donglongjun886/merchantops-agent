package com.merchantops.agent.tool;

import org.springframework.stereotype.Component;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 工具注册表：按名称动态查找工具。AgentLoop 通过它拿到工具，不写死任何具体 Tool。
 */
@Component
public class ToolRegistry {

    private final Map<String, Tool> tools = new HashMap<>();

    public ToolRegistry(List<Tool> toolList) {
        toolList.forEach(this::register);
    }

    public void register(Tool tool) {
        tools.put(tool.name(), tool);
    }

    /** 按名查找；不存在抛 {@link ToolNotFoundException} */
    public Tool get(String name) {
        Tool tool = tools.get(name);
        if (tool == null) {
            throw new ToolNotFoundException(name);
        }
        return tool;
    }

    /** 当前全部工具（AgentLoop 每次调用 LLM 时把可用工具声明传进去） */
    public List<Tool> all() {
        return List.copyOf(tools.values());
    }
}
