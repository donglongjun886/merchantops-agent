# MerchantOps Agent

企业业务 Agent 实践：**LLM + Tool Calling**，让运营人员以自然语言查询订单、商品和任务数据。

项目以 Pi 的 Agent Runtime 设计为主要研究参考，在此基础上逐步实现 **Agent Loop、Context Engineering、MCP 和 Agent Observability**。

## 技术栈

| 项 | 选型 |
|----|------|
| 语言 | Java 21 |
| 框架 | Spring Boot 3.x (3.4.5) |
| 构建 | Maven |
| 数据库 | MySQL 8（Docker 部署） |
| ORM | MyBatis-Plus 3.5.x |
| LLM | DeepSeek（OpenAI-compatible API） |
| Tool Calling | 原生实现（自研 tools/tool_calls 协议层） |
| 测试 | JUnit 5 |

## 环境准备

### 1. JDK 21（本机默认 JDK 为 26，需安装 21 并对齐）

```bash
brew install openjdk@21
# 添加到 PATH（Homebrew 会提示具体路径，Intel/ARM 略有差异）
echo 'export PATH="/opt/homebrew/opt/openjdk@21/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
java -version   # 应显示 21.x
```

> pom.xml 已固定 `<java.version>21</java.version>`（编译目标 --release 21）。
> 即使默认 JDK 是 26 也能编译，但运行建议对齐 21。

### 2. Docker Desktop

```bash
# 安装 Docker Desktop（brew install --cask docker），启动后：
docker --version
```

### 3. 启动 MySQL 8

```bash
docker compose up -d        # 在项目根目录执行
docker compose ps           # 等待 healthy
```

- 连接：`localhost:3306`，库 `merchantops`，用户/密码 `root/root`（与 `application.yml` 默认值一致）
- 表结构与 seed 数据由应用启动时自动初始化（`db/schema.sql` + `db/data.sql`，幂等）

### 4. 配置 DeepSeek API Key

推荐方式（本地敏感配置，已被 .gitignore 排除，不会提交到 GitHub）：

```bash
# 创建 src/main/resources/application-local.yml：
#   merchantops:
#     llm:
#       api-key: sk-xxxx
# 然后带 local profile 启动：
mvn spring-boot:run -Dspring-boot.run.profiles=local
```

也可以直接用环境变量：

```bash
export DEEPSEEK_API_KEY=sk-xxxx
export DEEPSEEK_MODEL=deepseek-v4-flash   # 默认已是
```

## 启动应用

```bash
mvn spring-boot:run -Dspring-boot.run.profiles=local
# 或
mvn package && java -jar target/merchantops-agent-0.1.0-SNAPSHOT.jar --spring.profiles.active=local
```

启动成功标志：`Started MerchantOpsAgentApplication`。

### 试一下 Agent

```bash
curl -X POST http://localhost:8080/api/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"帮我查一下商户 M1001 的信息"}'
```

## Agent Loop 核心流程

```text
用户输入
 ↓
[循环] 组装全量消息链 → 调 LLM（附带可用工具声明）
 ↓
LLM 返回 tool_calls ？
 ├─ 否 → 拿到最终答案，结束
 └─ 是 → 逐个执行工具，结果回填消息链 → 回到 [循环]
```

- AgentLoop 不写死具体工具，通过 ToolRegistry 动态查找
- 工具不存在/执行异常 → 错误回填给 LLM 纠错，不中断 Agent
- maxSteps 兜底防死循环（`merchantops.llm.max-steps`，默认 10）

## 目录结构

```
merchantops-agent/
├── pom.xml
├── docker-compose.yml            # MySQL 8 本地依赖
├── src/main/java/com/merchantops/agent/
│   ├── MerchantOpsAgentApplication.java
│   ├── agent/                    # Agent 核心（loop / context / tool / llm）[规划中]
│   ├── business/                 # 订单 / 商品 / 任务 业务服务 [规划中]
│   ├── controller/               # REST API [规划中]
│   └── obs/                      # 可观测性 [规划中]
└── src/main/resources/
    ├── application.yml           # 数据源 / MyBatis-Plus / LLM 配置
    └── db/                       # schema.sql + data.sql（幂等初始化）
```

## 里程碑

- [x] M1 工程骨架：pom + 启动类 + 配置 + 建表脚本 + seed 数据
- [ ] M2 原生 Tool Calling：LlmClient + Agent Loop + 订单查询工具
- [ ] M3 Context Engineering：多轮记忆 + 上下文截断/压缩
- [ ] M4 多工具协同：商品 / 任务工具 + 跨域查询
- [ ] M5 Observability：trace 落库 / 指标 / JUnit 5 测试体系
- [ ] M6（可选）MCP 接入
