from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Product
from app.models.enums import ProductStatus
from app.repositories.product import ProductRepository


class ProductService:
    def __init__(self, session: AsyncSession) -> None:
        self._products = ProductRepository(session)

    async def list_on_sale(
        self, *, page: int, page_size: int
    ) -> tuple[Sequence[Product], int]:
        return await self._products.list_page(
            status=ProductStatus.ON_SALE, page=page, page_size=page_size
        )

    async def get_on_sale(self, product_id: UUID) -> Product | None:
        """公开渠道只返回在售商品，其余一律视为不存在。"""
        product = await self._products.get(product_id)
        if product is None or product.status != ProductStatus.ON_SALE:
            return None
        return product
