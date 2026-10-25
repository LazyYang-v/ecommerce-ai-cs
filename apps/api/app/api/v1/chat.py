from fastapi import APIRouter, Depends, HTTPException

from app.clients.agent_client import AgentClient, AgentServiceError, get_agent_client
from app.core.context import current_request_id
from app.schemas.chat import ChatTestRequest, ChatTestResponse

router = APIRouter()


@router.post("/chat/test", response_model=ChatTestResponse)
async def test_chat(
    request: ChatTestRequest,
    agent_client: AgentClient = Depends(get_agent_client),
) -> ChatTestResponse:
    """Phase 1 通信验收：经 Agent 服务执行最小 LangGraph 图。

    仅用于开发验证。正式客服接口需要登录鉴权、会话归属校验、
    限流与消息持久化，在后续步骤实现。
    """
    payload: dict = {"message": request.message}
    request_id = current_request_id()
    if request_id != "-":
        payload["request_id"] = request_id
    try:
        data = await agent_client.chat(payload)
    except AgentServiceError as exc:
        raise HTTPException(
            status_code=502, detail="Agent service unavailable"
        ) from exc
    return ChatTestResponse(**data)
