from pydantic import BaseModel, Field


class ChatTestRequest(BaseModel):
    """前端 → Business API 的 Phase 1 通信验收请求。"""

    message: str = Field(min_length=1, max_length=2000)


class ChatTestResponse(BaseModel):
    """Business API 对前端的响应。

    字段与 Agent 服务的 ChatResponse 契约一致（见
    packages/contracts/README.md 与 docs/api-contracts.md）；
    conversation_id / thread_id / request_id 为链路追踪与
    LangGraph 持久化预留。
    """

    response: str
    conversation_id: str | None = None
    thread_id: str | None = None
    request_id: str | None = None
