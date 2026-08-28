from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.modules.auth.models import User
from app.modules.auth.schemas import UserResponse
from .models import FriendRequest
from .schemas import FriendRequestResponse, FriendStatusResponse


class FriendService:
    async def _find_pair(
        self, db: AsyncSession, user_a: str, user_b: str
    ) -> Optional[FriendRequest]:
        stmt = select(FriendRequest).where(
            or_(
                and_(FriendRequest.sender_id == user_a, FriendRequest.receiver_id == user_b),
                and_(FriendRequest.sender_id == user_b, FriendRequest.receiver_id == user_a),
            )
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_status(
        self, db: AsyncSession, current_user: User, other_user_id: str
    ) -> FriendStatusResponse:
        if current_user.id == other_user_id:
            return FriendStatusResponse(status="self")

        row = await self._find_pair(db, current_user.id, other_user_id)
        if not row:
            return FriendStatusResponse(status="none")
        if row.status == "accepted":
            return FriendStatusResponse(status="friends", requestId=row.id)
        if row.sender_id == current_user.id:
            return FriendStatusResponse(status="pending_sent", requestId=row.id)
        return FriendStatusResponse(status="pending_received", requestId=row.id)

    async def send_request(
        self, db: AsyncSession, current_user: User, receiver_id: str
    ) -> FriendStatusResponse:
        if current_user.id == receiver_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You can't friend yourself")

        stmt = select(User).where(User.id == receiver_id, User.is_active == True)
        result = await db.execute(stmt)
        if not result.scalars().first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        existing = await self._find_pair(db, current_user.id, receiver_id)
        if existing:
            if existing.status == "accepted":
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already friends")
            if existing.sender_id == current_user.id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request already sent")
            # The other person already requested us — mutual interest, accept immediately.
            existing.status = "accepted"
            existing.responded_at = datetime.now(timezone.utc)
            await db.commit()
            return FriendStatusResponse(status="friends", requestId=existing.id)

        new_request = FriendRequest(sender_id=current_user.id, receiver_id=receiver_id, status="pending")
        db.add(new_request)
        await db.commit()
        await db.refresh(new_request)
        return FriendStatusResponse(status="pending_sent", requestId=new_request.id)

    async def respond_request(
        self, db: AsyncSession, current_user: User, request_id: str, accept: bool
    ) -> FriendStatusResponse:
        stmt = select(FriendRequest).where(
            FriendRequest.id == request_id,
            FriendRequest.receiver_id == current_user.id,
            FriendRequest.status == "pending",
        )
        result = await db.execute(stmt)
        req = result.scalars().first()
        if not req:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Friend request not found")

        if accept:
            req.status = "accepted"
            req.responded_at = datetime.now(timezone.utc)
            await db.commit()
            return FriendStatusResponse(status="friends", requestId=req.id)

        await db.delete(req)
        await db.commit()
        return FriendStatusResponse(status="none")

    async def cancel_request(self, db: AsyncSession, current_user: User, request_id: str) -> bool:
        stmt = select(FriendRequest).where(
            FriendRequest.id == request_id,
            FriendRequest.sender_id == current_user.id,
            FriendRequest.status == "pending",
        )
        result = await db.execute(stmt)
        req = result.scalars().first()
        if not req:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Friend request not found")
        await db.delete(req)
        await db.commit()
        return True

    async def unfriend(self, db: AsyncSession, current_user: User, other_user_id: str) -> bool:
        row = await self._find_pair(db, current_user.id, other_user_id)
        if not row or row.status != "accepted":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not friends")
        await db.delete(row)
        await db.commit()
        return True

    async def list_friends(self, db: AsyncSession, current_user: User) -> List[UserResponse]:
        stmt = (
            select(FriendRequest)
            .options(selectinload(FriendRequest.sender), selectinload(FriendRequest.receiver))
            .where(
                FriendRequest.status == "accepted",
                or_(FriendRequest.sender_id == current_user.id, FriendRequest.receiver_id == current_user.id),
            )
        )
        result = await db.execute(stmt)
        rows = result.scalars().all()
        friends = [r.receiver if r.sender_id == current_user.id else r.sender for r in rows]
        return [UserResponse.model_validate(f) for f in friends]

    async def list_requests(
        self, db: AsyncSession, current_user: User, direction: str
    ) -> List[FriendRequestResponse]:
        if direction == "outgoing":
            stmt = (
                select(FriendRequest)
                .options(selectinload(FriendRequest.receiver))
                .where(FriendRequest.sender_id == current_user.id, FriendRequest.status == "pending")
                .order_by(FriendRequest.created_at.desc())
            )
        else:
            stmt = (
                select(FriendRequest)
                .options(selectinload(FriendRequest.sender))
                .where(FriendRequest.receiver_id == current_user.id, FriendRequest.status == "pending")
                .order_by(FriendRequest.created_at.desc())
            )
        result = await db.execute(stmt)
        rows = result.scalars().all()

        return [
            FriendRequestResponse(
                id=r.id,
                user=UserResponse.model_validate(r.receiver if direction == "outgoing" else r.sender),
                status=r.status,  # type: ignore
                direction=direction,  # type: ignore
                createdAt=r.created_at.isoformat() if r.created_at else "",
            )
            for r in rows
        ]

    async def list_suggestions(
        self, db: AsyncSession, current_user: User, limit: int = 20
    ) -> List[UserResponse]:
        stmt = select(FriendRequest.sender_id, FriendRequest.receiver_id).where(
            or_(FriendRequest.sender_id == current_user.id, FriendRequest.receiver_id == current_user.id)
        )
        result = await db.execute(stmt)
        connected_ids = {current_user.id}
        for sender_id, receiver_id in result.all():
            connected_ids.add(sender_id)
            connected_ids.add(receiver_id)

        stmt = (
            select(User)
            .where(User.is_active == True, User.id.not_in(connected_ids))
            .order_by(User.is_online.desc(), User.name.asc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        return [UserResponse.model_validate(u) for u in result.scalars().all()]


friend_service = FriendService()
