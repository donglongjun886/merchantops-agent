"""FastAPI 入口。启动：uvicorn app.main:app --reload"""

from fastapi import FastAPI

from .api.agent_api import router

app = FastAPI(
    title="MerchantOps Agent",
    description="LLM + Tool Calling 企业业务 Agent",
    version="0.1.0",
)

app.include_router(router)


@app.get("/health")
def health() -> dict:
    return {"status": "UP", "service": "merchantops-agent"}
