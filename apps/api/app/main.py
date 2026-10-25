import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import Response

from app.api.v1 import api_v1_router
from app.clients.agent_client import AgentClient
from app.core.config import get_settings
from app.core.context import new_request_id, request_id_var, setup_logging

logger = logging.getLogger(__name__)

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.agent_client = AgentClient(
        base_url=settings.agent_url,
        token=settings.internal_service_token,
        timeout=settings.agent_timeout_seconds,
    )
    logger.info("startup agent_url=%s", settings.agent_url)
    yield
    await app.state.agent_client.aclose()
    logger.info("shutdown agent_client_closed")


app = FastAPI(title="Ecommerce Business API", version="0.1.0", lifespan=lifespan)
app.include_router(api_v1_router)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    # 透传上游 X-Request-ID；缺失时生成 uuid4 hex
    request_id = request.headers.get("X-Request-ID", "").strip() or new_request_id()
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


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "business-api"}
