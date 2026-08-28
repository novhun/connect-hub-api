from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.auth.models import User
from .schemas import (
    CallInitiateRequest,
    CallLogResponse,
    CallSessionResponse,
    CallStatusUpdateRequest,
)
from .services import call_service


class CallController:
    async def initiate(
        self, db: AsyncSession, current_user: User, req: CallInitiateRequest
    ) -> CallSessionResponse:
        return await call_service.initiate_call(db, current_user, req)

    async def update_status(
        self, db: AsyncSession, session_id: str, req: CallStatusUpdateRequest
    ) -> CallSessionResponse:
        return await call_service.update_status(db, session_id, req)

    async def get_history(
        self, db: AsyncSession, current_user: User, skip: int, limit: int
    ) -> List[CallLogResponse]:
        return await call_service.get_call_history(db, current_user, skip, limit)


call_controller = CallController()
