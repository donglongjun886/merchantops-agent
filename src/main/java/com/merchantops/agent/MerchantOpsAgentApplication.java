package com.merchantops.agent;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * MerchantOps Agent 启动类。
 *
 * <p>企业业务 Agent 实践：LLM + Tool Calling，让运营人员以自然语言查询订单、商品和任务数据。
 * 以 Pi 的 Agent Runtime 设计为主要研究参考，逐步实现 Agent Loop、Context Engineering、
 * MCP 和 Agent Observability。</p>
 */
@SpringBootApplication
public class MerchantOpsAgentApplication {

    public static void main(String[] args) {
        SpringApplication.run(MerchantOpsAgentApplication.class, args);
    }
}
