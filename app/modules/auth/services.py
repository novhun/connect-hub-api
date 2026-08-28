import logging
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.mailer import mailer_service
from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_google_token,
    verify_password,
)
from .models import OAuthAccount, User
from .schemas import GoogleLoginRequest, TokenResponse, UserCreate, UserLogin, UserResponse

logger = logging.getLogger("connect_hub.auth")
security_bearer = HTTPBearer(auto_error=False)


class AuthService:
    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email.lower().strip())
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_user_by_id(self, db: AsyncSession, user_id: str) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        return result.scalars().first()

    async def register(self, db: AsyncSession, user_in: UserCreate) -> TokenResponse:
        existing = await self.get_user_by_email(db, user_in.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email already exists.",
            )

        new_user = User(
            email=user_in.email.lower().strip(),
            hashed_password=get_password_hash(user_in.password),
            name=user_in.name.strip(),
            avatar=user_in.avatar or f"https://api.dicebear.com/7.x/avataaars/svg?seed={user_in.name}",
            role=user_in.role or "Member",
            bio=user_in.bio,
            is_online=True,
            is_active=True,
            is_verified=False,
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        # Trigger async welcome email
        await mailer_service.send_welcome_email(new_user.email, new_user.name)

        token = create_access_token(subject=new_user.id, extra_claims={"email": new_user.email})
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse.model_validate(new_user),
        )

    async def login(self, db: AsyncSession, user_in: UserLogin) -> TokenResponse:
        user = await self.get_user_by_email(db, user_in.email)
        if not user or not user.hashed_password or not verify_password(user_in.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password.",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated.",
            )

        user.is_online = True
        await db.commit()
        await db.refresh(user)

        token = create_access_token(subject=user.id, extra_claims={"email": user.email})
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )

    async def google_login(self, db: AsyncSession, google_in: GoogleLoginRequest) -> TokenResponse:
        google_data = verify_google_token(google_in.token)
        if not google_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Google OAuth token.",
            )

        email = google_data["email"].lower().strip()
        google_id = google_data["google_id"]
        name = google_data.get("name") or email.split("@")[0]
        avatar = google_data.get("avatar")

        user = await self.get_user_by_email(db, email)
        if not user:
            # Create new user via Google
            user = User(
                email=email,
                name=name,
                avatar=avatar or f"https://api.dicebear.com/7.x/avataaars/svg?seed={name}",
                role="Member",
                is_online=True,
                is_active=True,
                is_verified=True,
            )
            db.add(user)
            await db.flush()

            oauth = OAuthAccount(
                user_id=user.id,
                provider="google",
                provider_user_id=google_id,
            )
            db.add(oauth)
            await db.commit()
            await db.refresh(user)
        else:
            # Check or attach OAuth account
            stmt = select(OAuthAccount).where(
                OAuthAccount.user_id == user.id, OAuthAccount.provider == "google"
            )
            res = await db.execute(stmt)
            oauth = res.scalars().first()
            if not oauth:
                oauth = OAuthAccount(
                    user_id=user.id,
                    provider="google",
                    provider_user_id=google_id,
                )
                db.add(oauth)
            user.is_online = True
            if avatar and not user.avatar:
                user.avatar = avatar
            await db.commit()
            await db.refresh(user)

        token = create_access_token(subject=user.id, extra_claims={"email": user.email})
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )


auth_service = AuthService()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency to retrieve the authenticated user from JWT bearer token."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await auth_service.get_user_by_id(db, payload["sub"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Dependency to optionally retrieve the current user if token is provided."""
    if not credentials:
        return None
    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        return None
    return await auth_service.get_user_by_id(db, payload["sub"])
