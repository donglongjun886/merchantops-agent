"""FastAPI 入口。启动：uvicorn app.main:app --reload"""

from fastapi import FastAPI

from .observability import setup_tracing

# 必须先初始化 OTel，再创建应用（agent.chat span 才能挂到正确的 tracer provider 上）
setup_tracing()

from .api.agent_api import router  # noqa: E402

app = FastAPI(
    title="MerchantOps Agent",
    description="LLM + Tool Calling 企业业务 Agent",
    version="0.1.0",
)

app.include_router(router)


@app.get("/health")
def health() -> dict:
    return {"status": "UP", "service": "merchantops-agent"}
