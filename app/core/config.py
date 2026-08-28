import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # App Info
    APP_NAME: str = "Connect-Hub API"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    API_V1_STR: str = "/api/v1"
    
    # CORS
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "https://connect2hub.vercel.app",
        "*"
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Security & JWT
    SECRET_KEY: str = "connect-hub-development-secret-jwt-key-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # Database URLs
    # Supports:
    # - SQLite: "sqlite+aiosqlite:///./connect_hub.db"
    # - Postgres: "postgresql+asyncpg://user:pass@host:5432/dbname"
    # - MySQL: "mysql+aiomysql://user:pass@host:3306/dbname"
    DATABASE_URL: str = "sqlite+aiosqlite:///./connect_hub.db"
    
    # MongoDB (Optional Document Store Mode)
    MONGODB_URI: str = ""
    MONGODB_DB_NAME: str = "connect_hub"

    # Cloud Object Storage (S3 / Cloudflare R2 / Local Disk)
    STORAGE_TYPE: str = "local"  # "local", "s3", or "r2"
    LOCAL_UPLOAD_DIR: str = "uploads"
    S3_ENDPOINT_URL: str = ""
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""
    S3_BUCKET_NAME: str = "connect-hub-media"
    S3_REGION: str = "auto"
    S3_PUBLIC_URL: str = ""

    # SMTP Configuration
    SMTP_ENABLED: bool = False
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@connecthub.app"
    SMTP_FROM_NAME: str = "Connect-Hub"
    SMTP_TLS: bool = True

    # PeerJS & WebRTC
    PEERJS_PATH: str = "/peerjs"
    PEERJS_KEY: str = "peerjs"
    PEERJS_ALLOW_DISCOVERY: bool = True


settings = Settings()
