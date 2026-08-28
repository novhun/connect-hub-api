from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.modules.auth.models import User
from app.modules.auth.schemas import UserResponse
from app.modules.posts.services import ensure_utc
from .models import CallSession
from .schemas import (
    CallInitiateRequest,
    CallLogResponse,
    CallSessionResponse,
    CallStatusUpdateRequest,
)


def format_call_date(dt: Optional[datetime]) -> str:
    if not dt:
        return "Today"
    dt = ensure_utc(dt)
    now = datetime.now(timezone.utc)
    diff = max(0.0, (now - dt).total_seconds())
    time_str = dt.strftime("%I:%M %p").lstrip("0")
    if diff < 86400 and now.day == dt.day:
        return f"Today, {time_str}"
    elif diff < 172800:
        return f"Yesterday, {time_str}"
    else:
        return f"{dt.strftime('%b %d')}, {time_str}"


def format_duration(seconds: int) -> Optional[str]:
    if not seconds or seconds <= 0:
        return None
    mins = seconds // 60
    secs = seconds % 60
    if mins > 0:
        return f"{mins}m {secs:02d}s"
    return f"{secs}s"


class CallService:
    async def initiate_call(
        self, db: AsyncSession, caller: User, req: CallInitiateRequest
    ) -> CallSessionResponse:
        session = CallSession(
            caller_id=caller.id,
            receiver_id=req.receiverId,
            call_type=req.callType,
            status="initiating",
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

        return CallSessionResponse.model_validate(session)

    async def update_status(
        self, db: AsyncSession, session_id: str, req: CallStatusUpdateRequest
    ) -> CallSessionResponse:
        stmt = select(CallSession).where(CallSession.id == session_id)
        result = await db.execute(stmt)
        session = result.scalars().first()
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Call session not found")

        session.status = req.status
        if req.status == "connected" and not session.started_at:
            session.started_at = datetime.now(timezone.utc)
        if req.status in ["completed", "declined", "missed"]:
            session.ended_at = datetime.now(timezone.utc)
            if req.durationSeconds is not None:
                session.duration_seconds = req.durationSeconds
            elif session.started_at:
                start_dt = ensure_utc(session.started_at)
                end_dt = ensure_utc(session.ended_at)
                session.duration_seconds = int((end_dt - start_dt).total_seconds())

        await db.commit()
        await db.refresh(session)

        return CallSessionResponse.model_validate(session)

    async def get_call_history(
        self, db: AsyncSession, current_user: User, skip: int = 0, limit: int = 50
    ) -> List[CallLogResponse]:
        stmt = (
            select(CallSession)
            .options(selectinload(CallSession.caller), selectinload(CallSession.receiver))
            .where(
                or_(
                    CallSession.caller_id == current_user.id,
                    CallSession.receiver_id == current_user.id,
                )
            )
            .order_by(CallSession.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        sessions = result.scalars().all()

        logs = []
        for s in sessions:
            is_incoming = s.receiver_id == current_user.id
            other_user = s.caller if is_incoming else s.receiver
            log_status = s.status if s.status in ["missed", "completed", "declined"] else "completed"

            user_res = (
                UserResponse.model_validate(other_user)
                if other_user
                else UserResponse(
                    id=s.caller_id if is_incoming else s.receiver_id,
                    name="Connect-Hub Member",
                    email="member@connecthub.app",
                    avatar="https://api.dicebear.com/7.x/avataaars/svg?seed=member",
                    role="Member",
                    isOnline=False,
                    isActive=True,
                )
            )

            logs.append(
                CallLogResponse(
                    id=s.id,
                    user=user_res,
                    type="incoming" if is_incoming else "outgoing",
                    date=format_call_date(s.created_at),
                    status=log_status,  # type: ignore
                    duration=format_duration(s.duration_seconds),
                    callType=s.call_type,  # type: ignore
                )
            )
        return logs


call_service = CallService()
