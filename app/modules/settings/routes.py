from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.modules.auth.models import User
from app.modules.auth.services import get_current_user
from .controllers import settings_controller
from .schemas import SettingsResponse, SettingsUpdate

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("", response_model=SettingsResponse)
async def get_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's account settings & preferences."""
    return await settings_controller.get_settings(db, current_user)


@router.put("", response_model=SettingsResponse)
async def update_settings(
    data: SettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user's account settings & preferences."""
    return await settings_controller.update_settings(db, current_user, data)
