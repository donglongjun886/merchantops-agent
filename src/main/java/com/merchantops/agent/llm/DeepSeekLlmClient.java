package com.merchantops.agent.llm;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.merchantops.agent.context.Message;
import com.merchantops.agent.tool.Tool;
import com.merchantops.agent.tool.ToolCall;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * DeepSeek LLM 客户端（OpenAI 兼容 /chat/completions 协议）。
 *
 * <p>只做两件事：把 Agent 的消息链 + 工具声明翻译成 OpenAI 请求体，
 * 把响应里的 content / tool_calls 翻译回 {@link LlmResponse}。</p>
 */
@Component
public class DeepSeekLlmClient implements LlmClient {

    private final RestClient restClient;
    private final ObjectMapper objectMapper;
    private final String apiKey;
    private final String model;
    private final double temperature;
    private final int maxTokens;

    public DeepSeekLlmClient(
            @Value("${merchantops.llm.base-url:https://api.deepseek.com}") String baseUrl,
            @Value("${merchantops.llm.api-key:}") String apiKey,
            @Value("${merchantops.llm.model:deepseek-v4-flash}") String model,
            @Value("${merchantops.llm.temperature:0.3}") double temperature,
            @Value("${merchantops.llm.max-tokens:2048}") int maxTokens) {
        this.restClient = RestClient.builder().baseUrl(baseUrl).build();
        this.objectMapper = new ObjectMapper();
        this.apiKey = apiKey;
        this.model = model;
        this.temperature = temperature;
        this.maxTokens = maxTokens;
    }

    @Override
    public LlmResponse chat(List<Message> messages, List<Tool> tools) {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("model", model);
        body.put("messages", messages.stream().map(this::toOpenAiMessage).toList());
        body.put("temperature", temperature);
        body.put("max_tokens", maxTokens);
        if (!tools.isEmpty()) {
            body.put("tools", tools.stream().map(this::toOpenAiTool).toList());
        }

        String json = restClient.post()
                .uri("/chat/completions")
                .header("Authorization", "Bearer " + apiKey)
                .contentType(MediaType.APPLICATION_JSON)
                .body(body)
                .retrieve()
                .body(String.class);

        return parseResponse(json);
    }

    /** 把内部 Message 翻译成 OpenAI 消息格式 */
    private Map<String, Object> toOpenAiMessage(Message m) {
        Map<String, Object> msg = new LinkedHashMap<>();
        msg.put("role", m.role());
        if (m.content() != null) {
            msg.put("content", m.content());
        }
        if (m.toolCallId() != null) {
            msg.put("tool_call_id", m.toolCallId());
        }
        if (m.toolCalls() != null && !m.toolCalls().isEmpty()) {
            msg.put("tool_calls", m.toolCalls().stream().map(tc -> Map.of(
                    "id", tc.id(),
                    "type", "function",
                    "function", Map.of("name", tc.name(), "arguments", tc.arguments())
            )).toList());
        }
        return msg;
    }

    /** 把 Tool 翻译成 OpenAI tools 声明 */
    private Map<String, Object> toOpenAiTool(Tool t) {
        return Map.of(
                "type", "function",
                "function", Map.of(
                        "name", t.name(),
                        "description", t.description(),
                        "parameters", parseJson(t.parametersJson())
                )
        );
    }

    /** 解析 OpenAI 响应，提取 content 和 tool_calls */
    private LlmResponse parseResponse(String json) {
        try {
            JsonNode root = objectMapper.readTree(json);
            JsonNode message = root.path("choices").get(0).path("message");
            String content = message.path("content").isNull() ? null : message.path("content").asText();

            List<ToolCall> calls = new ArrayList<>();
            JsonNode toolCalls = message.path("tool_calls");
            for (JsonNode tc : toolCalls) {
                calls.add(new ToolCall(
                        tc.path("id").asText(),
                        tc.path("function").path("name").asText(),
                        tc.path("function").path("arguments").asText()
                ));
            }
            return calls.isEmpty() ? LlmResponse.answer(content) : LlmResponse.toolCalls(calls);
        } catch (JsonProcessingException e) {
            throw new IllegalStateException("LLM 响应解析失败", e);
        }
    }

    private Object parseJson(String s) {
        try {
            return objectMapper.readTree(s);
        } catch (JsonProcessingException e) {
            throw new IllegalArgumentException("JSON 解析失败: " + s, e);
        }
    }
}
