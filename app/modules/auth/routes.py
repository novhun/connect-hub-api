from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from .controllers import auth_controller
from .models import User
from .schemas import (
    ChangePasswordRequest,
    GoogleLoginRequest,
    PasswordResetRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from .services import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""
    return await auth_controller.register(db, user_in)


@router.post("/login", response_model=TokenResponse)
async def login(user_in: UserLogin, db: AsyncSession = Depends(get_db)):
    """Log in with email and password."""
    return await auth_controller.login(db, user_in)


@router.post("/google", response_model=TokenResponse)
async def google_login(google_in: GoogleLoginRequest, db: AsyncSession = Depends(get_db)):
    """Log in or sign up with Google OAuth token."""
    return await auth_controller.google_login(db, google_in)


@router.post("/forgot-password")
async def forgot_password(reset_in: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    """Request password reset code via email."""
    return await auth_controller.forgot_password(db, reset_in)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user profile."""
    return await auth_controller.get_me(current_user)


@router.put("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change current user's password."""
    return await auth_controller.change_password(db, current_user, data)
