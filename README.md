# Connect-Hub FastAPI Backend API

High-performance, modular **FastAPI** backend powering **Connect-Hub** social feeds, 24-hour stories, communities/groups, real-time messaging, WebRTC / PeerJS audio & video calling, multi-database support (PostgreSQL, MySQL, SQLite, MongoDB), S3/R2 object storage, and Google OAuth.

---

## 🌟 Key Architecture & Features

- **Modular MVC Design**: Clean separation into `core/`, `middlewares/`, and domain modules (`auth`, `users`, `posts`, `stories`, `groups`, `chat`, `calls`, `notifications`, `media`).
- **SQLAlchemy 2.0 & Alembic 1.16.5**: Full async SQLAlchemy 2.0 ORM with asynchronous sessions and migrations.
- **Universal Multi-Database Engine**:
  - **SQLite** (Default local dev): `sqlite+aiosqlite:///./connect_hub.db`
  - **PostgreSQL**: `postgresql+asyncpg://user:pass@host:5432/dbname`
  - **MySQL**: `mysql+aiomysql://user:pass@host:3306/dbname`
  - **MongoDB**: `mongodb://localhost:27017` with Motor async client.
- **PeerJS & WebRTC Signaling**: Built-in PeerJS broker protocol at `/peerjs` and `/ws/peerjs/{peer_id}` with audio/video room routing.
- **Cloud Storage & Local Fallback**: AWS S3 and Cloudflare R2 compatible file uploads with direct presigned URLs and local disk fallback in `./uploads`.
- **Authentication & Security**: JWT Bearer tokens, Bcrypt password hashing, Google OAuth2 ID token verification.
- **SMTP Email Service**: Asynchronous email delivery for welcome messages and password resets.
- **Realtime Direct Messaging**: Low-latency WebSocket duplex communication at `/api/v1/chat/ws/{user_id}`.

---

## 🚀 Quick Start

### 1. Setup Virtual Environment & Dependencies
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and adjust database or cloud credentials if needed:
```bash
cp .env.example .env
```

### 3. Initialize Database & Seed Demo Data
```bash
python scripts/seed_data.py
```

### 4. Run Development Server
```bash
./scripts/run.sh
# or manually:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive API documentation will be available at:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 📦 Alembic Database Migrations

Generate new migration:
```bash
alembic revision --autogenerate -m "create_initial_schema"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback migration:
```bash
alembic downgrade -1
```

---

## 🧪 Running Automated Tests

```bash
pytest -v
```

---

## 📡 API Endpoints Summary

| Module | Method | Endpoint | Description |
|---|---|---|---|
| **Auth** | `POST` | `/api/v1/auth/register` | Register new user |
| **Auth** | `POST` | `/api/v1/auth/login` | Email/password login |
| **Auth** | `POST` | `/api/v1/auth/google` | Google OAuth token login |
| **Auth** | `GET` | `/api/v1/auth/me` | Current authenticated user |
| **Users** | `GET` | `/api/v1/users` | List users & presence |
| **Users** | `PUT` | `/api/v1/users/profile` | Update profile |
| **Posts** | `GET` | `/api/v1/posts` | Feed posts list |
| **Posts** | `POST` | `/api/v1/posts` | Create new post |
| **Posts** | `POST` | `/api/v1/posts/{id}/react` | React (like, love, care, etc.) |
| **Posts** | `POST` | `/api/v1/posts/{id}/comments` | Add comment |
| **Stories** | `GET` | `/api/v1/stories` | List active 24h stories |
| **Stories** | `POST` | `/api/v1/stories` | Publish new story |
| **Groups** | `GET` | `/api/v1/groups` | Explore / joined groups |
| **Groups** | `POST` | `/api/v1/groups` | Create group |
| **Chat** | `GET` | `/api/v1/chat/{user_id}` | Message history |
| **Chat** | `POST` | `/api/v1/chat/{user_id}` | Send direct message |
| **Chat** | `WS` | `/api/v1/chat/ws/{user_id}` | Duplex WebSocket |
| **Calls** | `POST` | `/api/v1/calls/initiate` | Start audio/video call |
| **Calls** | `GET` | `/api/v1/calls/history` | Call logs history |
| **PeerJS** | `WS` | `/peerjs` / `/ws/peerjs/{id}` | WebRTC signaling socket |
| **Media** | `POST` | `/api/v1/media/upload` | Multipart file upload |
| **Notifications** | `GET` | `/api/v1/notifications` | User notifications |
