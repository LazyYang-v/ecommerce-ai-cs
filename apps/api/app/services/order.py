from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Order, OrderItem
from app.repositories.order import OrderRepository


class OrderService:
    def __init__(self, session: AsyncSession) -> None:
        self._orders = OrderRepository(session)

    async def list_for_user(
        self, *, user_id: UUID, page: int, page_size: int
    ) -> tuple[Sequence[Order], int]:
        return await self._orders.list_page_by_user(
            user_id=user_id, page=page, page_size=page_size
        )

    async def get_for_user(self, *, user_id: UUID, order_id: UUID) -> Order | None:
        """归属校验：订单不存在或属于他人时统一返回 None（对外 404）。"""
        order = await self._orders.get(order_id)
        if order is None or order.user_id != user_id:
            return None
        return order

    async def list_items(self, order_id: UUID) -> Sequence[OrderItem]:
        return await self._orders.list_items(order_id)
