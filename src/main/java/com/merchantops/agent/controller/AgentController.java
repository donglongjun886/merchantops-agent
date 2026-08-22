package com.merchantops.agent.controller;

import com.merchantops.agent.loop.AgentLoop;
import com.merchantops.agent.loop.AgentResult;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

/**
 * Agent 对话入口。
 */
@RestController
@RequestMapping("/api/agent")
public class AgentController {

    private final AgentLoop agentLoop;

    public AgentController(AgentLoop agentLoop) {
        this.agentLoop = agentLoop;
    }

    /**
     * 自然语言对话。
     *
     * <p>请求：{"message": "帮我查一下商户 M1001 的信息"}</p>
     * <p>响应：{"answer": "...", "steps": 2, "maxStepsReached": false}</p>
     */
    @PostMapping("/chat")
    public Map<String, Object> chat(@RequestBody Map<String, String> request) {
        String message = request.get("message");
        AgentResult result = agentLoop.run(message);
        return Map.of(
                "answer", result.answer(),
                "steps", result.steps(),
                "maxStepsReached", result.maxStepsReached()
        );
    }
}
