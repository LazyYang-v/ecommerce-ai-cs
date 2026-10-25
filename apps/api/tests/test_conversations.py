import asyncio
import uuid
from datetime import UTC, datetime, timedelta

from conftest import TestSessionFactory

from app.models import Message
from app.models.enums import MessageSenderType


def _register_and_login(client, email):
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    assert resp.status_code == 201
    resp = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "password123"}
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_create_and_list_conversation(make_api_client):
    with make_api_client() as client:
        headers = _register_and_login(client, "conv-alice@test.com")
        created = client.post("/api/v1/conversations", headers=headers)
        assert created.status_code == 201
        assert created.json()["status"] == "open"
        assert created.json()["id"]

        listing = client.get("/api/v1/conversations", headers=headers)
        assert listing.status_code == 200
        body = listing.json()
        assert body["total"] == 1
        assert body["items"][0]["id"] == created.json()["id"]


def test_messages_ordered_and_paginated(make_api_client):
    with make_api_client() as client:
        headers = _register_and_login(client, "conv-bob@test.com")
        conversation_id = client.post(
            "/api/v1/conversations", headers=headers
        ).json()["id"]

        async def _add_messages():
            async with TestSessionFactory() as session:
                base = datetime.now(UTC) - timedelta(minutes=10)
                for i in range(3):
                    session.add(
                        Message(
                            conversation_id=uuid.UUID(conversation_id),
                            sender_type=(
                                MessageSenderType.USER if i % 2 == 0
                                else MessageSenderType.AGENT
                            ),
                            content=f"消息 {i}",
                            created_at=base + timedelta(seconds=i),
                        )
                    )
                await session.commit()

        asyncio.run(_add_messages())

        resp = client.get(
            f"/api/v1/conversations/{conversation_id}/messages", headers=headers
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 3
        assert [m["content"] for m in body["items"]] == ["消息 0", "消息 1", "消息 2"]
        assert body["items"][0]["sender_type"] == "user"

        page1 = client.get(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=headers,
            params={"page": 1, "page_size": 2},
        ).json()
        assert page1["total"] == 3
        assert len(page1["items"]) == 2


def test_cannot_access_other_users_conversation(make_api_client):
    """补充要求：用户不能查询其他用户的会话（归属校验）。"""
    with make_api_client() as client:
        owner_headers = _register_and_login(client, "conv-owner@test.com")
        intruder_headers = _register_and_login(client, "conv-intruder@test.com")
        conversation_id = client.post(
            "/api/v1/conversations", headers=owner_headers
        ).json()["id"]

        # 他人读取会话消息 → 404
        resp = client.get(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=intruder_headers,
        )
        assert resp.status_code == 404
        # 他人会话列表不含该会话
        listing = client.get(
            "/api/v1/conversations", headers=intruder_headers
        ).json()
        assert listing["total"] == 0


def test_unknown_conversation_404(make_api_client):
    with make_api_client() as client:
        headers = _register_and_login(client, "conv-carol@test.com")
        resp = client.get(
            "/api/v1/conversations/00000000-0000-0000-0000-000000000000/messages",
            headers=headers,
        )
        assert resp.status_code == 404


def test_conversations_require_auth(make_api_client):
    with make_api_client() as client:
        assert client.get("/api/v1/conversations").status_code == 401
        assert client.post("/api/v1/conversations").status_code == 401
