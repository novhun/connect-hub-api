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


import json
import urllib.request

def verify_google_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify real Google OAuth2 Token (ID Token or Access Token) directly with Google servers.
    Returns user info dict (google_id, email, name, avatar, email_verified) if valid, None otherwise.
    """
    if not token or not token.strip():
        return None

    # 1. Verify Google ID token via google-auth library
    try:
        audience = settings.GOOGLE_CLIENT_ID if settings.GOOGLE_CLIENT_ID else None
        req = google_requests.Request()
        id_info = id_token.verify_oauth2_token(token, req, audience)
        if id_info and id_info.get("email"):
            return {
                "google_id": id_info.get("sub"),
                "email": id_info.get("email"),
                "name": id_info.get("name") or id_info.get("email", "").split("@")[0],
                "avatar": id_info.get("picture"),
                "email_verified": id_info.get("email_verified", False),
            }
    except Exception:
        pass

    # 2. Verify Google UserInfo API (for Google Access Tokens from OAuth2 / TokenClient)
    try:
        url = "https://www.googleapis.com/oauth2/v3/userinfo"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                if data and data.get("email"):
                    return {
                        "google_id": data.get("sub"),
                        "email": data.get("email"),
                        "name": data.get("name") or data.get("email", "").split("@")[0],
                        "avatar": data.get("picture"),
                        "email_verified": data.get("email_verified", False),
                    }
    except Exception:
        pass

    # 3. Verify Google TokenInfo API (for Google ID Tokens)
    try:
        url = f"https://oauth2.googleapis.com/tokeninfo?id_token={token}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                if data and data.get("email"):
                    return {
                        "google_id": data.get("sub"),
                        "email": data.get("email"),
                        "name": data.get("name") or data.get("email", "").split("@")[0],
                        "avatar": data.get("picture"),
                        "email_verified": data.get("email_verified", False),
                    }
    except Exception:
        pass

    return None
