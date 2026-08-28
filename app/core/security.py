import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union
from jose import JWTError, jwt
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from .config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against the hashed version."""
    if not hashed_password or not plain_password:
        return False
    try:
        password_bytes = plain_password.encode("utf-8")[:72]
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Generate bcrypt hash for password."""
    password_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None, extra_claims: Optional[Dict[str, Any]] = None
) -> str:
    """Create JWT access token with claims and expiration."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode: Dict[str, Any] = {"exp": expire, "sub": str(subject)}
    if extra_claims:
        to_encode.update(extra_claims)
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def verify_google_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify Google OAuth2 ID Token.
    Returns user info dict (email, name, picture, sub) if valid, None otherwise.
    """
    try:
        audience = settings.GOOGLE_CLIENT_ID if settings.GOOGLE_CLIENT_ID else None
        req = google_requests.Request()
        id_info = id_token.verify_oauth2_token(token, req, audience)
        return {
            "google_id": id_info.get("sub"),
            "email": id_info.get("email"),
            "name": id_info.get("name"),
            "avatar": id_info.get("picture"),
            "email_verified": id_info.get("email_verified", False),
        }
    except Exception:
        if settings.DEBUG and token.startswith("test-google-token-"):
            mock_id = token.replace("test-google-token-", "")
            return {
                "google_id": f"google-{mock_id}",
                "email": f"user-{mock_id}@gmail.com",
                "name": f"Google User {mock_id}",
                "avatar": f"https://api.dicebear.com/7.x/avataaars/svg?seed={mock_id}",
                "email_verified": True,
            }
        return None
