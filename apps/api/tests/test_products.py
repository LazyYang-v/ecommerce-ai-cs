import asyncio
from decimal import Decimal

from conftest import TestSessionFactory

from app.models import Product
from app.models.enums import ProductStatus


def _add_products():
    async def _seed():
        async with TestSessionFactory() as session:
            session.add_all(
                [
                    Product(name="耳机", price=Decimal("399.00"), stock=10),
                    Product(name="手表", price=Decimal("899.00"), stock=5),
                    Product(
                        name="下架商品",
                        price=Decimal("99.00"),
                        stock=1,
                        status=ProductStatus.OFF_SALE,
                    ),
                ]
            )
            await session.commit()

    asyncio.run(_seed())


def test_empty_product_list(make_api_client):
    with make_api_client() as client:
        resp = client.get("/api/v1/products")
        assert resp.status_code == 200
        body = resp.json()
        assert body == {"items": [], "total": 0, "page": 1, "page_size": 20}


def test_list_only_on_sale_with_pagination(make_api_client):
    _add_products()
    with make_api_client() as client:
        resp = client.get("/api/v1/products", params={"page": 1, "page_size": 1})
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2
        assert len(body["items"]) == 1
        assert body["page"] == 1
        assert body["page_size"] == 1
        names = {item["name"] for item in body["items"]}
        assert names <= {"耳机", "手表"}


def test_product_detail_serializes_price_as_string(make_api_client):
    _add_products()
    with make_api_client() as client:
        listing = client.get("/api/v1/products").json()
        product_id = listing["items"][0]["id"]
        resp = client.get(f"/api/v1/products/{product_id}")
        assert resp.status_code == 200
        body = resp.json()
        # 金额以字符串序列化，避免浮点精度损失
        assert body["price"] in ("399.00", "899.00")
        assert body["status"] == "on_sale"


def test_off_sale_product_hidden_from_public(make_api_client):
    _add_products()
    with make_api_client() as client:
        async def _get_off_sale_id():
            async with TestSessionFactory() as session:
                from sqlalchemy import select

                result = await session.execute(
                    select(Product).where(Product.status == ProductStatus.OFF_SALE)
                )
                return str(result.scalar_one().id)

        off_sale_id = asyncio.run(_get_off_sale_id())
        assert client.get(f"/api/v1/products/{off_sale_id}").status_code == 404


def test_unknown_product_404(make_api_client):
    with make_api_client() as client:
        resp = client.get(
            "/api/v1/products/00000000-0000-0000-0000-000000000000"
        )
        assert resp.status_code == 404
