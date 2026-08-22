package com.merchantops.agent.tool.mock;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.merchantops.agent.tool.Tool;
import org.springframework.stereotype.Component;

import java.util.Map;

/**
 * Mock 工具：查询商户信息（演示用，返回固定数据）。
 */
@Component
public class GetMerchantTool implements Tool {

    private static final ObjectMapper MAPPER = new ObjectMapper();

    @Override
    public String name() {
        return "getMerchant";
    }

    @Override
    public String description() {
        return "根据商户ID查询商户信息（名称、状态、等级）";
    }

    @Override
    public String parametersJson() {
        return """
                {"type":"object","properties":{"merchantId":{"type":"string","description":"商户ID"}},"required":["merchantId"]}
                """.trim();
    }

    @Override
    public String execute(String argumentsJson) {
        try {
            JsonNode args = MAPPER.readTree(argumentsJson);
            String merchantId = args.path("merchantId").asText();
            Map<String, Object> data = Map.of(
                    "merchantId", merchantId,
                    "name", "测试商户-" + merchantId,
                    "status", "ACTIVE",
                    "level", "金牌")
            ;
            return MAPPER.writeValueAsString(data);
        } catch (Exception e) {
            throw new IllegalStateException("getMerchant 参数解析失败: " + e.getMessage(), e);
        }
    }
}
