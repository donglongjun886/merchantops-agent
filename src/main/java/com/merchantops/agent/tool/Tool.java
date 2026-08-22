package com.merchantops.agent.tool;

/**
 * Agent 可调用工具的统一抽象。
 *
 * <p>AgentLoop 不知道任何具体工具，只通过 {@link ToolRegistry} 按 name 查找并执行，
 * 因此新增工具 = 新增一个实现类并注册，不动 Agent 核心代码。</p>
 */
public interface Tool {

    /** 工具名（LLM 通过它发起调用），如 getMerchant */
    String name();

    /** 给 LLM 看的工具说明，帮助模型判断何时调用 */
    String description();

    /** 参数 JSON Schema（给 LLM 的 tools 声明），默认空对象 */
    default String parametersJson() {
        return "{\"type\":\"object\",\"properties\":{}}";
    }

    /**
     * 执行工具。
     *
     * @param argumentsJson 参数 JSON 字符串，由 LLM 生成
     * @return 执行结果（JSON 字符串），回填给 LLM
     */
    String execute(String argumentsJson);
}
