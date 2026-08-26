# MerchantOps Agent

企业业务 Agent 实践：**LLM + Tool Calling**，让运营人员以自然语言查询商户和任务信息。

项目以 Pi 的 Agent Runtime 设计为主要研究参考，在此基础上逐步实现 **Agent Loop、Context Engineering、MCP 和 Agent Observability**。

## 技术栈

| 项 | 选型 |
|----|------|
| 语言 | Python 3.12 |
| Web 框架 | FastAPI |
| LLM SDK | openai（base_url 指向 DeepSeek） |
| 模型 | DeepSeek V4 Flash |
| 测试 | pytest |
| 配置 | pydantic-settings + .env |

## 快速开始

```bash
# 1. 创建虚拟环境并安装依赖
python3.12 -m venv .venv
.venv/bin/pip install -e ".[dev]"

# 2. 配置 API Key
cp .env.example .env        # 填入 DEEPSEEK_API_KEY（.env 已被 gitignore，不会提交）

# 3. 启动
.venv/bin/uvicorn app.main:app --reload --port 8080

# 4. 试一下
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
- max_steps 兜底防死循环（`LLM_MAX_STEPS`，默认 10）

## 目录结构

```
merchantops-agent/
├── pyproject.toml              # 依赖 + pytest 配置
├── .env.example                # 环境变量模板
├── app/
│   ├── main.py                 # FastAPI 入口（/health）
│   ├── config.py               # pydantic-settings 配置
│   ├── agent/
│   │   ├── loop.py             # ★ AgentLoop（核心循环）+ AgentResult
│   │   ├── context.py          # AgentContext + Message（完整消息链）
│   │   ├── llm.py              # LlmClient(ABC) + LlmResponse + DeepSeekClient
│   │   ├── tool.py             # Tool(ABC) + ToolCall + ToolResult + ToolNotFound
│   │   └── registry.py         # ToolRegistry（动态查找）
│   ├── tools/
│   │   └── mock_tools.py       # getMerchant / getTask 两个 Mock 工具
│   └── api/
│       └── agent_api.py        # POST /api/agent/chat
└── tests/
    ├── fake_llm.py             # 脚本化响应 LLM（测试用）
    └── test_agent_loop.py      # 6 个单元测试
```

## 测试

```bash
.venv/bin/python -m pytest -v
```

覆盖 6 个场景：直接答案 / 一次 Tool Call / 连续两次 Tool Call / 工具不存在 / 超过最大迭代 / 工具执行异常。

## API

### POST /api/agent/chat

请求：`{"message": "帮我查一下商户 M1001 的信息"}`

响应：

```json
{
  "answer": "根据查询结果，商户 M1001 的信息如下：...",
  "steps": 2,
  "max_steps_reached": false
}
```

### GET /health

健康检查：`{"status": "UP", "service": "merchantops-agent"}`

## 里程碑

- [x] M1 最小 Agent Loop：AgentLoop / LlmClient / AgentContext / Tool / ToolRegistry / ToolCall / ToolResult + 6 个单测 + 真实 API 验证
- [ ] M2 Context Engineering：多轮记忆 + 上下文截断/压缩
- [ ] M3 多工具协同：商品/任务工具 + 跨域查询
- [ ] M4 Observability：trace 记录 / 指标
- [ ] M5（可选）MCP 接入
