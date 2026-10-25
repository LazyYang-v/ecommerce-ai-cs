from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.schemas.product import ProductPage, ProductPublic
from app.services.product import ProductService

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=ProductPage)
async def list_products(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> ProductPage:
    items, total = await ProductService(session).list_on_sale(
        page=page, page_size=page_size
    )
    return ProductPage(
        items=[ProductPublic.model_validate(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{product_id}", response_model=ProductPublic)
async def get_product(
    product_id: UUID, session: AsyncSession = Depends(get_session)
) -> ProductPublic:
    product = await ProductService(session).get_on_sale(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductPublic.model_validate(product)
