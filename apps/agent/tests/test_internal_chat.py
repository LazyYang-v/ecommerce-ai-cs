import uuid

import pytest

TOKEN = "test-internal-token"


def test_chat_without_token_rejected(client):
    resp = client.post("/internal/chat", json={"message": "你好"})
    assert resp.status_code == 401


def test_chat_with_wrong_token_rejected(client):
    resp = client.post(
        "/internal/chat",
        json={"message": "你好"},
        headers={"X-Internal-Token": "wrong-token"},
    )
    assert resp.status_code == 401


def test_chat_with_valid_token_returns_echo(client):
    resp = client.post(
        "/internal/chat",
        json={
            "message": "我的订单在哪里？",
            "conversation_id": "conv-1",
            "thread_id": "thread-1",
        },
        headers={"X-Internal-Token": TOKEN, "X-Request-ID": "req-001"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["response"] == "已收到消息：我的订单在哪里？"
    assert body["conversation_id"] == "conv-1"
    assert body["thread_id"] == "thread-1"
    assert body["request_id"] == "req-001"
    assert resp.headers["X-Request-ID"] == "req-001"


def test_chat_generates_request_id_when_missing(client):
    resp = client.post(
        "/internal/chat",
        json={"message": "你好"},
        headers={"X-Internal-Token": TOKEN},
    )
    assert resp.status_code == 200
    generated = resp.json()["request_id"]
    assert generated and generated != "-"
    try:
        uuid.UUID(hex=generated)
    except ValueError:
        pytest.fail("request_id 应为 uuid4 hex")
    assert resp.headers["X-Request-ID"] == generated


def test_chat_rejects_empty_message(client):
    resp = client.post(
        "/internal/chat",
        json={"message": ""},
        headers={"X-Internal-Token": TOKEN},
    )
    assert resp.status_code == 422
