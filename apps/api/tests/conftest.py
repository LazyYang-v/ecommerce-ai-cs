import asyncio
import os
import threading
import time
from types import SimpleNamespace

# —— 测试环境必须在导入 app 之前准备 ——
# 补充要求 1：测试数据库与开发数据库物理隔离；未显式指向 ecommerce_test 则拒绝运行
_TEST_DB_URL = os.environ.get("DATABASE_URL", "")
if "ecommerce_test" not in _TEST_DB_URL:
    raise RuntimeError(
        "测试必须使用独立测试库：请设置 DATABASE_URL 指向 ecommerce_test，"
        f"当前值: {_TEST_DB_URL!r}"
    )
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")

import pytest
import uvicorn
from fastapi import FastAPI, Header, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.core.database import get_session
from app.main import app

STUB_TOKEN = "stub-internal-token"

# 测试引擎：NullPool 保证跨事件循环安全（TestClient 门户循环 vs 测试循环）
test_engine = create_async_engine(_TEST_DB_URL, poolclass=NullPool)
TestSessionFactory = async_sessionmaker(test_engine, expire_on_commit=False)


async def _override_get_session():
    async with TestSessionFactory() as session:
        yield session


app.dependency_overrides[get_session] = _override_get_session


def _build_stub_agent() -> FastAPI:
    """真实 HTTP 测试替身（非 mock 库）。

    回传它实际收到的 X-Request-ID，用于验证 API → Agent 的透传；
    message == "__sleep__" 时延迟响应，用于验证超时。
    """

    stub = FastAPI()

    @stub.get("/health")
    async def health():
        return {"status": "ok", "service": "stub-agent"}

    @stub.post("/internal/chat")
    async def chat(
        payload: dict,
        x_internal_token: str | None = Header(default=None),
        x_request_id: str | None = Header(default=None),
    ):
        if x_internal_token != STUB_TOKEN:
            raise HTTPException(status_code=401, detail="Unauthorized internal request")
        if payload.get("message") == "__sleep__":
            await asyncio.sleep(5)
        return {
            "response": f"已收到消息：{payload['message']}",
            "request_id": x_request_id,
        }

    return stub


@pytest.fixture(scope="session")
def stub_agent():
    server = uvicorn.Server(
        uvicorn.Config(_build_stub_agent(), host="127.0.0.1", port=0, log_level="warning")
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    while not server.started and time.monotonic() < deadline:
        time.sleep(0.02)
    assert server.started, "stub agent 启动超时"
    port = server.servers[0].sockets[0].getsockname()[1]
    try:
        yield SimpleNamespace(url=f"http://127.0.0.1:{port}", token=STUB_TOKEN)
    finally:
        server.should_exit = True
        thread.join(timeout=5)


@pytest.fixture()
def make_api_client(monkeypatch, stub_agent):
    """按需构造指向不同 Agent 地址/令牌/超时的 API 测试客户端。"""

    def _make(
        agent_url: str | None = None,
        token: str = STUB_TOKEN,
        timeout: str = "2",
    ) -> TestClient:
        get_settings.cache_clear()
        monkeypatch.setenv("AGENT_URL", agent_url or stub_agent.url)
        monkeypatch.setenv("INTERNAL_SERVICE_TOKEN", token)
        monkeypatch.setenv("AGENT_TIMEOUT_SECONDS", timeout)
        return TestClient(app)

    yield _make
    get_settings.cache_clear()


_TRUNCATE_SQL = text(
    "TRUNCATE TABLE messages, order_items, orders, conversations, products, users CASCADE"
)


@pytest.fixture(autouse=True)
def clean_database():
    """每个测试结束后清空业务表，保证用例相互独立。"""
    yield

    async def _truncate():
        async with test_engine.begin() as conn:
            await conn.execute(_TRUNCATE_SQL)

    asyncio.run(_truncate())


def run_db(coro):
    """在独立事件循环中执行异步数据库操作（NullPool 引擎跨循环安全）。"""
    return asyncio.run(coro)
