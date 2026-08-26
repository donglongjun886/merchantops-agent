"""Agent 对话 API。"""

from fastapi import APIRouter
from pydantic import BaseModel

from ..agent.llm import DeepSeekClient
from ..agent.loop import AgentLoop
from ..agent.registry import ToolRegistry
from ..config import settings
from ..tools.mock_tools import GetMerchantTool, GetTaskTool

router = APIRouter(prefix="/api/agent", tags=["agent"])

# 组装 Agent：DeepSeek LLM + 两个 Mock 工具
_llm_client = DeepSeekClient(
    api_key=settings.deepseek_api_key,
    base_url=settings.deepseek_base_url,
    model=settings.deepseek_model,
    temperature=settings.llm_temperature,
    max_tokens=settings.llm_max_tokens,
)
_tool_registry = ToolRegistry([GetMerchantTool(), GetTaskTool()])
_agent_loop = AgentLoop(_llm_client, _tool_registry, max_steps=settings.llm_max_steps)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str
    steps: int
    max_steps_reached: bool


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """自然语言对话：{"message": "帮我查一下商户 M1001 的信息"}"""
    result = _agent_loop.run(request.message)
    return ChatResponse(
        answer=result.answer,
        steps=result.steps,
        max_steps_reached=result.max_steps_reached,
    )
