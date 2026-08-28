"""FastAPI 入口。启动：uvicorn app.main:app --reload"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

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

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

# 聊天页面（static/index.html）与静态资源
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> dict:
    return {"status": "UP", "service": "merchantops-agent"}
