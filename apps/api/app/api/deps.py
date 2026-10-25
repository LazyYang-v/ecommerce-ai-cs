"""API 公共依赖：会话与当前用户。"""
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_session
from app.core.security import decode_access_token
from app.models import User
from app.repositories.user import UserRepository

_bearer = HTTPBearer(auto_error=False)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    session: AsyncSession = Depends(get_session),
) -> User:
    if credentials is None:
        raise _unauthorized("Not authenticated")
    settings = get_settings()
    try:
        payload = decode_access_token(
            token=credentials.credentials,
            secret=settings.jwt_secret,
            algorithm=settings.jwt_algorithm,
        )
    except ValueError as exc:
        raise HTTPException(503, "Auth is not configured") from exc
    except jwt.PyJWTError as exc:
        raise _unauthorized("Invalid or expired token") from exc
    try:
        user_id = UUID(str(payload.get("sub")))
    except (TypeError, ValueError) as exc:
        raise _unauthorized("Invalid token payload") from exc
    user = await UserRepository(session).get(user_id)
    if user is None or not user.is_active:
        raise _unauthorized("User not found or inactive")
    return user
