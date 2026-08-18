"""Роутер аутентификации: регистрация, авторизация, текущий пользователь."""

from auth import create_access_token, get_current_user, hash_password, verify_password
from database.connection import get_db
from database.models import User
from fastapi import APIRouter, Depends, HTTPException, status
from schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Зарегистрировать нового пользователя и вернуть JWT-токен."""
    existing = await db.scalar(
        select(User).where(
            or_(User.email == payload.email, User.nickname == payload.nickname)
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or nickname already registered",
        )

    user = User(
        nickname=payload.nickname,
        email=payload.email,
        password_hash=hash_password(payload.password),
        telegram_nickname=payload.telegram_nickname,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Авторизовать пользователя по email и паролю."""
    user = await db.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    return TokenResponse(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> User:
    """Вернуть данные текущего пользователя."""
    return current_user
