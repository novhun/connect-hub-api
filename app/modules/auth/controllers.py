from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.mailer import mailer_service
from app.core.security import get_password_hash, verify_password
from .models import User
from .schemas import (
    ChangePasswordRequest,
    GoogleLoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from .services import auth_service


class AuthController:
    async def register(self, db: AsyncSession, user_in: UserCreate) -> TokenResponse:
        return await auth_service.register(db, user_in)

    async def login(self, db: AsyncSession, user_in: UserLogin) -> TokenResponse:
        return await auth_service.login(db, user_in)

    async def google_login(self, db: AsyncSession, google_in: GoogleLoginRequest) -> TokenResponse:
        return await auth_service.google_login(db, google_in)

    async def forgot_password(self, db: AsyncSession, reset_in: PasswordResetRequest) -> dict:
        user = await auth_service.get_user_by_email(db, reset_in.email)
        if user:
            # Generate a 6-digit reset code
            import random
            code = f"{random.randint(100000, 999999)}"
            await mailer_service.send_password_reset_email(user.email, code)
        return {"success": True, "message": "If this email is registered, a password reset code has been sent."}

    async def change_password(self, db: AsyncSession, current_user: User, data: ChangePasswordRequest) -> dict:
        if not current_user.hashed_password or not verify_password(data.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password does not match.",
            )
        current_user.hashed_password = get_password_hash(data.new_password)
        await db.commit()
        return {"success": True, "message": "Password changed successfully."}

    async def get_me(self, current_user: User) -> UserResponse:
        return UserResponse.model_validate(current_user)


auth_controller = AuthController()
