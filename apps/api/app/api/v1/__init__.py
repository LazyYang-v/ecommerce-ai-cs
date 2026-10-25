from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.chat import router as chat_router
from app.api.v1.conversations import router as conversations_router
from app.api.v1.orders import router as orders_router
from app.api.v1.products import router as products_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(products_router)
api_v1_router.include_router(orders_router)
api_v1_router.include_router(conversations_router)
api_v1_router.include_router(chat_router)
