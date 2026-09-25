from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from app.core.config import settings


def setup_cors(app: FastAPI) -> None:
    origins = list(settings.CORS_ORIGINS) if isinstance(settings.CORS_ORIGINS, (list, tuple)) else [settings.CORS_ORIGINS]

    # Guarantee common local development origins are present
    default_dev_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8008",
        "http://127.0.0.1:8008",
    ]
    for dev_orig in default_dev_origins:
        if dev_orig not in origins:
            origins.append(dev_orig)

    has_wildcard = "*" in origins

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins if not has_wildcard else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
        allow_origin_regex=r"^https?://.*" if has_wildcard else None,
        allow_private_network=True,
    )
