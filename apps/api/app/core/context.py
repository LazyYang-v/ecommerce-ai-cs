"""请求上下文与可观测性：X-Request-ID 贯穿日志与跨服务调用。"""
import logging
import uuid
from contextvars import ContextVar

# 当前请求的 X-Request-ID；"-" 表示请求上下文之外（如启动阶段）
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


def current_request_id() -> str:
    return request_id_var.get()


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


def new_request_id() -> str:
    return uuid.uuid4().hex
