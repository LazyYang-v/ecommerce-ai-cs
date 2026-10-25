from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_session
from app.models import User
from app.schemas.order import OrderDetail, OrderItemPublic, OrderPage, OrderSummary
from app.services.order import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("", response_model=OrderPage)
async def list_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> OrderPage:
    items, total = await OrderService(session).list_for_user(
        user_id=current_user.id, page=page, page_size=page_size
    )
    return OrderPage(
        items=[OrderSummary.model_validate(o) for o in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{order_id}", response_model=OrderDetail)
async def get_order(
    order_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> OrderDetail:
    order = await OrderService(session).get_for_user(
        user_id=current_user.id, order_id=order_id
    )
    if order is None:
        # 不存在与他人订单统一 404，不泄露资源是否存在
        raise HTTPException(status_code=404, detail="Order not found")
    items = await OrderService(session).list_items(order_id)
    return OrderDetail(
        id=order.id,
        status=order.status,
        total_amount=order.total_amount,
        created_at=order.created_at,
        items=[OrderItemPublic.model_validate(i) for i in items],
    )
