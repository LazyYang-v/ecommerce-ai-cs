from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Business API → Agent 的内部对话请求。

    conversation_id / thread_id 为后续 LangGraph 持久化（checkpointer
    按 thread 存储对话状态）预留；request_id 用于全链路追踪。
    Phase 1 三者均可缺省。
    """

    message: str = Field(min_length=1, max_length=2000)
    conversation_id: str | None = Field(default=None, max_length=64)
    thread_id: str | None = Field(default=None, max_length=64)
    request_id: str | None = Field(default=None, max_length=64)


class ChatResponse(BaseModel):
    """Agent → Business API 的内部对话响应，回传预留字段以便链路追踪。"""

    response: str
    conversation_id: str | None = None
    thread_id: str | None = None
    request_id: str | None = None
