from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_session
from app.models import User
from app.schemas.conversation import (
    ConversationPage,
    ConversationPublic,
    MessagePage,
    MessagePublic,
)
from app.services.conversation import ConversationService

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("", response_model=ConversationPublic, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ConversationPublic:
    conversation = await ConversationService(session).create(user_id=current_user.id)
    return ConversationPublic.model_validate(conversation)


@router.get("", response_model=ConversationPage)
async def list_conversations(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ConversationPage:
    items, total = await ConversationService(session).list_for_user(
        user_id=current_user.id, page=page, page_size=page_size
    )
    return ConversationPage(
        items=[ConversationPublic.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{conversation_id}/messages", response_model=MessagePage)
async def list_messages(
    conversation_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> MessagePage:
    result = await ConversationService(session).list_messages_for_user(
        user_id=current_user.id,
        conversation_id=conversation_id,
        page=page,
        page_size=page_size,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    items, total = result
    return MessagePage(
        items=[MessagePublic.model_validate(m) for m in items],
        total=total,
        page=page,
        page_size=page_size,
    )
