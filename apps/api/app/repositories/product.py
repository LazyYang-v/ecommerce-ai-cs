from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Product
from app.models.enums import ProductStatus


class ProductRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, product_id: UUID) -> Product | None:
        return await self._session.get(Product, product_id)

    async def list_page(
        self, *, status: ProductStatus, page: int, page_size: int
    ) -> tuple[Sequence[Product], int]:
        condition = Product.status == status
        total = await self._session.scalar(
            select(func.count()).select_from(Product).where(condition)
        )
        stmt = (
            select(Product)
            .where(condition)
            .order_by(Product.created_at.desc(), Product.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = (await self._session.execute(stmt)).scalars().all()
        return items, int(total or 0)
