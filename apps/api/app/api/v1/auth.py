from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.database import get_session
from app.models import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserPublic
from app.services.auth import (
    AuthService,
    EmailAlreadyExistsError,
    InvalidCredentialsError,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserPublic, status_code=201)
async def register(
    body: RegisterRequest, session: AsyncSession = Depends(get_session)
) -> UserPublic:
    try:
        user = await AuthService(session).register(
            email=body.email, password=body.password, nickname=body.nickname
        )
    except EmailAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail="Email already registered") from exc
    return UserPublic.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest, session: AsyncSession = Depends(get_session)
) -> TokenResponse:
    try:
        _, token = await AuthService(session).login(
            email=body.email, password=body.password
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=401, detail="Incorrect email or password"
        ) from exc
    except ValueError as exc:  # JWT_SECRET 未配置
        raise HTTPException(status_code=503, detail="Auth is not configured") from exc
    return TokenResponse(
        access_token=token, expires_in=get_settings().jwt_expire_minutes * 60
    )


@router.get("/me", response_model=UserPublic)
async def me(current_user: User = Depends(get_current_user)) -> UserPublic:
    return UserPublic.model_validate(current_user)
