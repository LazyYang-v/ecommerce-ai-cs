import asyncio
from decimal import Decimal

from conftest import TestSessionFactory

from app.models import Order, OrderItem, Product
from app.models.enums import OrderStatus


def _register_and_login(client, email):
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    assert resp.status_code == 201
    resp = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "password123"}
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_paid_order(user_email):
    """直接写库构造一条已支付订单（Phase 1 无下单接口，列表/详情为只读）。"""

    async def _seed():
        async with TestSessionFactory() as session:
            from sqlalchemy import select

            from app.models import User

            # 用户已通过 HTTP 注册，这里复用而非再插入（email 唯一约束）
            user = (
                (
                    await session.execute(
                        select(User).where(User.email == user_email)
                    )
                )
                .scalar_one()
            )
            product = Product(name="快照商品", price=Decimal("199.00"), stock=50)
            session.add(product)
            await session.flush()
            order = Order(
                user_id=user.id,
                status=OrderStatus.PAID,
                total_amount=Decimal("398.00"),
            )
            session.add(order)
            await session.flush()
            session.add(
                OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    product_name="快照商品",
                    unit_price=Decimal("199.00"),
                    quantity=2,
                )
            )
            await session.commit()
            return {"order_id": str(order.id), "user_id": str(user.id)}

    return asyncio.run(_seed())


def test_list_own_orders(make_api_client):
    with make_api_client() as client:
        headers = _register_and_login(client, "orders-alice@test.com")
        _create_paid_order("orders-alice@test.com")
        resp = client.get("/api/v1/orders", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["status"] == "paid"
        assert body["items"][0]["total_amount"] == "398.00"


def test_order_detail_contains_item_snapshot(make_api_client):
    with make_api_client() as client:
        headers = _register_and_login(client, "orders-bob@test.com")
        order = _create_paid_order("orders-bob@test.com")
        resp = client.get(f"/api/v1/orders/{order['order_id']}", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "paid"
        assert len(body["items"]) == 1
        item = body["items"][0]
        # 订单明细保留下单时快照
        assert item["product_name"] == "快照商品"
        assert item["unit_price"] == "199.00"
        assert item["quantity"] == 2


def test_cannot_access_other_users_order(make_api_client):
    """补充要求：用户不能查询其他用户的订单（归属校验）。"""
    with make_api_client() as client:
        owner_headers = _register_and_login(client, "orders-owner@test.com")
        other_headers = _register_and_login(client, "orders-intruder@test.com")
        order = _create_paid_order("orders-owner@test.com")

        # 本人可见
        assert (
            client.get(f"/api/v1/orders/{order['order_id']}", headers=owner_headers).status_code
            == 200
        )
        # 他人访问 → 404（不泄露订单是否存在）
        resp = client.get(
            f"/api/v1/orders/{order['order_id']}", headers=other_headers
        )
        assert resp.status_code == 404
        # 他人订单列表也只包含自己的（0 条）
        listing = client.get("/api/v1/orders", headers=other_headers).json()
        assert listing["total"] == 0


def test_unknown_order_404(make_api_client):
    with make_api_client() as client:
        headers = _register_and_login(client, "orders-carol@test.com")
        resp = client.get(
            "/api/v1/orders/00000000-0000-0000-0000-000000000000", headers=headers
        )
        assert resp.status_code == 404
