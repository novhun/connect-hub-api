# 🚀 Connect-Hub API (FastAPI Backend)

High-performance, production-ready, modular **FastAPI** backend powering the **Connect-Hub** social platform. Built with async **SQLAlchemy 2.0**, **Alembic**, multi-database engine support (PostgreSQL, MySQL, SQLite, MongoDB), **PeerJS WebRTC** signaling, **Full-Duplex WebSockets**, **S3/R2** cloud object storage, and **Google OAuth2**.

---

## 🌟 Key Architecture & Features

- **Modular MVC Architecture**: Structured cleanly into `app/core/`, `app/middlewares/`, and domain modules:
  - `auth`: JWT Bearer authentication, password hashing with Bcrypt, Google OAuth2 ID token verification.
  - `users`: User profiles, bio updates, presence tracking, and directory search.
  - `posts`: Rich feed posts, multi-image collages, 7 reaction types (`like`, `love`, `care`, `haha`, `wow`, `sad`, `angry`), threaded comments, shares, and bookmarks.
  - `stories`: 24-hour disappearing stories with media attachments and viewed status tracking.
  - `groups`: Community discovery, membership management (join/leave), and group-tagged posts.
  - `chat`: Direct messaging with persistent chat history and duplex WebSocket streaming.
  - `calls`: Audio & video call session logging, duration tracking, and status synchronization.
  - `notifications`: User notifications with real-time mark-as-read and mark-all-read.
  - `media`: Multipart file upload with AWS S3 / Cloudflare R2 presigned URLs and local disk storage fallback.
- **SQLAlchemy 2.0 Async ORM**: Modern `select()`, async sessions (`AsyncSession`), relationship loading with `selectinload()`, and DeclarativeBase.
- **Alembic 1.16.5 Database Migrations**: Automated schema revision generation and database migrations.
- **Universal Multi-Database Engine**:
  - **SQLite** (Default local dev): `sqlite+aiosqlite:///./connect_hub.db`
  - **PostgreSQL**: `postgresql+asyncpg://user:password@localhost:5432/connect_hub`
  - **MySQL**: `mysql+aiomysql://user:password@localhost:3306/connect_hub`
  - **MongoDB**: `mongodb://localhost:27017` with Motor async client.
- **Real-Time WebRTC / PeerJS Broker**: Native PeerJS signaling protocol on HTTP `/peerjs/id` and WebSocket `/ws/peerjs/{peer_id}` for P2P video and audio rooms.
- **Full-Duplex WebSockets**: Real-time direct chat messaging at `/api/v1/chat/ws/{user_id}`.
- **Cloud Storage & Local Fallback**: AWS S3 & Cloudflare R2 support with automatic local storage in `./uploads`.
- **SMTP Email Service**: Async email delivery for welcome alerts and account notifications.

---

## 📁 Project Directory Structure

```text
connect-hub-api/
├── alembic/                  # Database migration environment and versions
├── app/
│   ├── core/                 # Core engine, database, config, security, storage, email
│   │   ├── config.py         # Pydantic v2 settings & environment loading
│   │   ├── database.py       # Async SQLAlchemy engine & session factory
│   │   ├── email.py          # SMTP async email client
│   │   ├── security.py       # JWT creation, decoding & password hashing
│   │   └── storage.py        # S3 / R2 and local disk storage manager
│   ├── middlewares/          # Custom middlewares (CORS, Request Logging, Errors)
│   ├── modules/              # Domain-driven modular MVC architecture
│   │   ├── auth/             # Models, schemas, services, and routes
│   │   ├── users/            # User profile, presence, and search
│   │   ├── posts/            # Posts, comments, reactions, saved posts
│   │   ├── stories/          # 24-hour stories and media
│   │   ├── groups/           # Community groups and membership
│   │   ├── chat/             # Direct messaging and WebSockets
│   │   ├── calls/            # Call logs and PeerJS WebRTC broker
│   │   ├── notifications/    # Notifications system
│   │   └── media/            # File upload endpoints
│   └── main.py               # FastAPI application entrypoint and route mounting
├── migrations/               # Database migration scripts
├── scripts/
│   ├── run.sh                # Server execution script
│   └── seed_data.py          # Database seeding script with rich demo data
├── tests/                    # Pytest test suite
├── uploads/                  # Local media uploads folder
├── .env.example              # Environment variables template
├── alembic.ini               # Alembic configuration
└── requirements.txt          # Python dependencies
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+
- Virtualenv (`python3 -m venv`)

### 2. Setup Virtual Environment & Dependencies
```bash
# Navigate to the API folder
cd connect-hub-api

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

### 3. Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Key environment variables in `.env`:
```env
APP_NAME="Connect-Hub API"
PORT=8008
HOST="0.0.0.0"
DEBUG=True
SECRET_KEY="your-super-secret-jwt-key"
DATABASE_URL="sqlite+aiosqlite:///./connect_hub.db"

# Optional Cloud Storage (AWS S3 / Cloudflare R2)
S3_ENABLED=False
S3_BUCKET_NAME=""
S3_ACCESS_KEY=""
S3_SECRET_KEY=""

# Optional SMTP Email
SMTP_ENABLED=False
SMTP_HOST="smtp.gmail.com"
SMTP_PORT=587
SMTP_USER=""
SMTP_PASSWORD=""
```

### 4. Seed Database with Rich Demo Data
```bash
python scripts/seed_data.py
```
> Seeds active user accounts (`sokun@connecthub.app` / `password123`), multi-image posts, stories, groups, chat history, and notifications.

### 5. Run the Server
```bash
./scripts/run.sh
# or directly with uvicorn:
uvicorn app.main:app --host 0.0.0.0 --port 8008 --reload
```

---

## 📖 Interactive API Documentation

Once the server is running on `http://localhost:8008`:
- **Swagger UI**: [http://localhost:8008/docs](http://localhost:8008/docs)
- **ReDoc**: [http://localhost:8008/redoc](http://localhost:8008/redoc)
- **Health Check**: [http://localhost:8008/health](http://localhost:8008/health)

---

## 🗄️ Database Migrations (Alembic)

Generate a new migration:
```bash
alembic revision --autogenerate -m "describe_changes"
```

Apply all pending migrations:
```bash
alembic upgrade head
```

Rollback the last migration:
```bash
alembic downgrade -1
```

---

## 🧪 Running Automated Tests

Run the test suite using `pytest`:
```bash
pytest -v
```

---

## 📡 REST & WebSocket Endpoints Summary

| Module | Method | Route | Description |
|---|---|---|---|
| **Health** | `GET` | `/health` | Server and database health check |
| **Auth** | `POST` | `/api/v1/auth/register` | Register new user |
| **Auth** | `POST` | `/api/v1/auth/login` | Email/password JWT login |
| **Auth** | `POST` | `/api/v1/auth/google` | Google OAuth ID token login |
| **Auth** | `GET` | `/api/v1/auth/me` | Get current authenticated user profile |
| **Users** | `GET` | `/api/v1/users` | List community members & online status |
| **Users** | `PUT` | `/api/v1/users/profile` | Update profile bio, avatar, and details |
| **Users** | `PATCH`| `/api/v1/users/presence` | Update online/offline presence |
| **Posts** | `GET` | `/api/v1/posts` | List posts feed (with group/saved filters) |
| **Posts** | `POST` | `/api/v1/posts` | Create a new post |
| **Posts** | `POST` | `/api/v1/posts/{id}/react` | React to post (`like`, `love`, `care`, etc.) |
| **Posts** | `POST` | `/api/v1/posts/{id}/comments` | Add comment to post |
| **Posts** | `POST` | `/api/v1/posts/{id}/save` | Toggle save/bookmark post |
| **Posts** | `POST` | `/api/v1/posts/{id}/share` | Increment post share count |
| **Posts** | `DELETE`| `/api/v1/posts/{id}` | Delete post |
| **Stories** | `GET` | `/api/v1/stories` | List active 24-hour stories |
| **Stories** | `POST` | `/api/v1/stories` | Upload and publish a story |
| **Stories** | `POST` | `/api/v1/stories/{id}/view` | Mark story as viewed |
| **Stories** | `DELETE`| `/api/v1/stories/{id}` | Delete a story |
| **Groups** | `GET` | `/api/v1/groups` | List community groups |
| **Groups** | `POST` | `/api/v1/groups` | Create a new community group |
| **Groups** | `POST` | `/api/v1/groups/{id}/join` | Join a community group |
| **Groups** | `POST` | `/api/v1/groups/{id}/leave` | Leave a community group |
| **Chat** | `GET` | `/api/v1/chat/{user_id}` | Retrieve chat message history |
| **Chat** | `POST` | `/api/v1/chat/{user_id}` | Send a direct message |
| **Chat** | `POST` | `/api/v1/chat/{user_id}/read` | Mark conversation messages as read |
| **Chat (WS)** | `WS` | `/api/v1/chat/ws/{user_id}` | Real-time duplex chat WebSocket |
| **Calls** | `POST` | `/api/v1/calls/initiate` | Start audio/video call session |
| **Calls** | `PATCH`| `/api/v1/calls/{id}/status` | Update call status & duration |
| **Calls** | `GET` | `/api/v1/calls/history` | Retrieve user call history |
| **PeerJS** | `GET` | `/peerjs/id` | Generate unique PeerJS WebRTC ID |
| **PeerJS (WS)**| `WS` | `/ws/peerjs/{peer_id}` | Real-time WebRTC PeerJS signaling |
| **Media** | `POST` | `/api/v1/media/upload` | Multipart file upload (S3/R2/Local) |
| **Notifications** | `GET` | `/api/v1/notifications` | List user notifications |
| **Notifications** | `POST` | `/api/v1/notifications/{id}/read` | Mark single notification as read |
| **Notifications** | `POST` | `/api/v1/notifications/read-all` | Mark all notifications as read |
