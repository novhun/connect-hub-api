from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings


def setup_cors(app: FastAPI) -> None:
    origins = settings.CORS_ORIGINS
    if isinstance(origins, str):
        origins = [origins]

    has_wildcard = "*" in origins

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins if not has_wildcard else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_origin_regex=r"^https?://.*" if has_wildcard else None,
    )
