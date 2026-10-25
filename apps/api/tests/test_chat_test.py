import uuid

import pytest


def test_chat_test_happy_path_propagates_request_id(make_api_client):
    with make_api_client() as client:
        resp = client.post(
            "/api/v1/chat/test",
            json={"message": "你好，我想查询订单"},
            headers={"X-Request-ID": "req-chain-001"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["response"] == "已收到消息：你好，我想查询订单"
        # stub 回传它实际收到的 X-Request-ID，证明 API → Agent 透传成功
        assert body["request_id"] == "req-chain-001"
        assert resp.headers["X-Request-ID"] == "req-chain-001"


def test_chat_test_generates_request_id_when_missing(make_api_client):
    with make_api_client() as client:
        resp = client.post("/api/v1/chat/test", json={"message": "ping"})
        assert resp.status_code == 200
        generated = resp.json()["request_id"]
        assert generated and len(generated) == 32  # uuid4().hex
        try:
            uuid.UUID(hex=generated)
        except ValueError:
            pytest.fail("request_id 应为 uuid4 hex")
        assert resp.headers["X-Request-ID"] == generated


def test_chat_test_rejects_empty_message(make_api_client):
    with make_api_client() as client:
        resp = client.post("/api/v1/chat/test", json={"message": ""})
        assert resp.status_code == 422


def test_chat_test_maps_agent_401_to_502(make_api_client, stub_agent):
    # API 持有错误令牌 → Agent 拒绝 401 → 对前端统一 502
    with make_api_client(token="wrong-token") as client:
        resp = client.post("/api/v1/chat/test", json={"message": "你好"})
        assert resp.status_code == 502


def test_chat_test_agent_unreachable_returns_502(make_api_client):
    # 指向必然拒绝连接的端口，验证连接失败 → 502
    with make_api_client(agent_url="http://127.0.0.1:9") as client:
        resp = client.post("/api/v1/chat/test", json={"message": "你好"})
        assert resp.status_code == 502


def test_chat_test_agent_timeout_returns_502(make_api_client, stub_agent):
    # stub 对 "__sleep__" 延迟 5s，客户端超时 1s → 502
    with make_api_client(timeout="1") as client:
        resp = client.post("/api/v1/chat/test", json={"message": "__sleep__"})
        assert resp.status_code == 502
