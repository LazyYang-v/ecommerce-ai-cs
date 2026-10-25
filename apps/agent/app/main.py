import logging
import secrets
import time
import uuid
from contextvars import ContextVar

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import Response

from app.core.config import get_settings
from app.graphs.customer_graph import customer_graph
from app.schemas.chat import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

# 当前请求的 X-Request-ID，供日志与响应回填使用
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdLogFilter(logging.Filter):
    """给所有经过根 handler 的日志记录附加 request_id 字段。"""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


def setup_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s [%(request_id)s] %(name)s: %(message)s"
        )
    )
    handler.addFilter(RequestIdLogFilter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)


setup_logging()

app = FastAPI(title="Customer Agent Service", version="0.1.0")


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    # 透传上游 X-Request-ID；缺失时生成 uuid4 hex
    request_id = request.headers.get("X-Request-ID", "").strip() or uuid.uuid4().hex
    token = request_id_var.set(request_id)
    start = time.perf_counter()
    try:
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "http_request method=%s path=%s status=%s duration_ms=%.1f",
            request.method,
            request.url.path,
            response.status_code,
            (time.perf_counter() - start) * 1000,
        )
        return response
    finally:
        request_id_var.reset(token)


def verify_internal_token(
    x_internal_token: str | None = Header(default=None),
) -> None:
    settings = get_settings()
    expected = settings.internal_service_token
    if (
        not expected  # 未配置令牌时拒绝所有内部请求（fail-closed）
        or not x_internal_token
        or not secrets.compare_digest(x_internal_token, expected)
    ):
        raise HTTPException(status_code=401, detail="Unauthorized internal request")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "agent"}


@app.post(
    "/internal/chat",
    response_model=ChatResponse,
    dependencies=[Depends(verify_internal_token)],
)
async def chat(request: ChatRequest) -> ChatResponse:
    logger.info(
        "internal_chat conversation_id=%s thread_id=%s message_len=%d",
        request.conversation_id,
        request.thread_id,
        len(request.message),
    )
    result = await customer_graph.ainvoke({"message": request.message, "response": ""})
    return ChatResponse(
        response=result["response"],
        conversation_id=request.conversation_id,
        thread_id=request.thread_id,
        request_id=request_id_var.get(),
    )
