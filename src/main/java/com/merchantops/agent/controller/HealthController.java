package com.merchantops.agent.controller;

import org.springframework.dao.DataAccessException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * 健康检查接口。
 *
 * <p>健康检查不只是返回 "UP" 空壳，而是验证真实依赖（数据库连通性）：
 * 依赖正常返回 200 + status=UP；依赖异常返回 503 + status=DOWN，
 * 便于负载均衡/监控探针做出正确判断。</p>
 */
@RestController
@RequestMapping("/api")
public class HealthController {

    private final JdbcTemplate jdbcTemplate;

    public HealthController(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> health() {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("service", "merchantops-agent");
        body.put("timestamp", Instant.now().toString());

        try {
            Integer one = jdbcTemplate.queryForObject("SELECT 1", Integer.class);
            boolean dbUp = one != null && one == 1;
            body.put("status", dbUp ? "UP" : "DOWN");
            body.put("database", dbUp ? "UP" : "DOWN");
            return dbUp ? ResponseEntity.ok(body)
                        : ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(body);
        } catch (DataAccessException e) {
            body.put("status", "DOWN");
            body.put("database", "DOWN");
            body.put("reason", e.getClass().getSimpleName());
            return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(body);
        }
    }
}
