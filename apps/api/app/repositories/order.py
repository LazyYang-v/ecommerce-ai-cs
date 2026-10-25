from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Order, OrderItem


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, order_id: UUID) -> Order | None:
        return await self._session.get(Order, order_id)

    async def list_page_by_user(
        self, *, user_id: UUID, page: int, page_size: int
    ) -> tuple[Sequence[Order], int]:
        condition = Order.user_id == user_id
        total = await self._session.scalar(
            select(func.count()).select_from(Order).where(condition)
        )
        stmt = (
            select(Order)
            .where(condition)
            .order_by(Order.created_at.desc(), Order.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = (await self._session.execute(stmt)).scalars().all()
        return items, int(total or 0)

    async def list_items(self, order_id: UUID) -> Sequence[OrderItem]:
        stmt = (
            select(OrderItem)
            .where(OrderItem.order_id == order_id)
            .order_by(OrderItem.created_at, OrderItem.id)
        )
        return (await self._session.execute(stmt)).scalars().all()
