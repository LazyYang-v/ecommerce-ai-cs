import logging
from typing import Any

import httpx
from fastapi import Request

from app.core.context import current_request_id

logger = logging.getLogger(__name__)


class AgentServiceError(Exception):
    """Agent 服务调用失败：网络错误、超时或非 2xx 响应。"""


class AgentClient:
    """Business API → Agent Service 的内部 HTTP 客户端。

    契约（docs/api-contracts.md）：
      POST {base_url}/internal/chat
      X-Internal-Token: 内部服务令牌（Agent 侧 compare_digest 校验）
      X-Request-ID: 透传当前请求 ID，用于全链路追踪
    """

    def __init__(self, base_url: str, token: str, timeout: float = 15.0) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            headers={"X-Internal-Token": token},
            timeout=timeout,
            # 连接阶段自动重试：Agent 重启等场景下避免瞬时 ConnectError 直接 502
            transport=httpx.AsyncHTTPTransport(retries=2),
        )

    async def chat(self, payload: dict[str, Any]) -> dict[str, Any]:
        request_id = current_request_id()
        headers = {"X-Request-ID": request_id} if request_id != "-" else None
        try:
            response = await self._client.post(
                "/internal/chat", json=payload, headers=headers
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            # 只记录异常类型，不记录令牌与消息内容
            logger.warning(
                "agent_call_failed path=/internal/chat error=%s", type(exc).__name__
            )
            raise AgentServiceError(str(exc)) from exc
        return response.json()

    async def aclose(self) -> None:
        await self._client.aclose()


def get_agent_client(request: Request) -> AgentClient:
    return request.app.state.agent_client
