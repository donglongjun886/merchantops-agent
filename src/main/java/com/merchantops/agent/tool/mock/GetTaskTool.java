package com.merchantops.agent.tool.mock;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.merchantops.agent.tool.Tool;
import org.springframework.stereotype.Component;

import java.util.Map;

/**
 * Mock 工具：查询任务信息（演示用，返回固定数据）。
 */
@Component
public class GetTaskTool implements Tool {

    private static final ObjectMapper MAPPER = new ObjectMapper();

    @Override
    public String name() {
        return "getTask";
    }

    @Override
    public String description() {
        return "根据任务ID查询任务信息（标题、状态、负责人）";
    }

    @Override
    public String parametersJson() {
        return """
                {"type":"object","properties":{"taskId":{"type":"string","description":"任务ID"}},"required":["taskId"]}
                """.trim();
    }

    @Override
    public String execute(String argumentsJson) {
        try {
            JsonNode args = MAPPER.readTree(argumentsJson);
            String taskId = args.path("taskId").asText();
            Map<String, Object> data = Map.of(
                    "taskId", taskId,
                    "title", "处理商户入驻审核",
                    "status", "IN_PROGRESS",
                    "owner", "运营-小林")
            ;
            return MAPPER.writeValueAsString(data);
        } catch (Exception e) {
            throw new IllegalStateException("getTask 参数解析失败: " + e.getMessage(), e);
        }
    }
}
