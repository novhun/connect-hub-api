from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.auth.models import User
from .schemas import SettingsResponse, SettingsUpdate
from .services import settings_service


class SettingsController:
    async def get_settings(self, db: AsyncSession, current_user: User) -> SettingsResponse:
        return await settings_service.get_settings(db, current_user)

    async def update_settings(
        self, db: AsyncSession, current_user: User, data: SettingsUpdate
    ) -> SettingsResponse:
        return await settings_service.update_settings(db, current_user, data)


settings_controller = SettingsController()
