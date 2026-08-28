from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.modules.auth.models import User
from app.modules.auth.services import get_current_user
from .controllers import support_controller
from .schemas import SendSupportMessageRequest, SendSupportMessageResponse, SupportMessageResponse

router = APIRouter(prefix="/support", tags=["Support"])


@router.get("/messages", response_model=List[SupportMessageResponse])
async def get_messages(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's support chat history."""
    return await support_controller.get_history(db, current_user)


@router.post("/messages", response_model=SendSupportMessageResponse)
async def send_message(
    data: SendSupportMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a message to ConnectHub support and receive an automated reply."""
    return await support_controller.send_message(db, current_user, data.text)
