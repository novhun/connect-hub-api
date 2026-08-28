from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.auth.models import User
from .models import UserSettings
from .schemas import SettingsResponse, SettingsUpdate


class SettingsService:
    async def _get_or_create(self, db: AsyncSession, user_id: str) -> UserSettings:
        stmt = select(UserSettings).where(UserSettings.user_id == user_id)
        result = await db.execute(stmt)
        settings = result.scalars().first()
        if not settings:
            settings = UserSettings(user_id=user_id)
            db.add(settings)
            await db.commit()
            await db.refresh(settings)
        return settings

    async def get_settings(self, db: AsyncSession, current_user: User) -> SettingsResponse:
        settings = await self._get_or_create(db, current_user.id)
        return SettingsResponse.model_validate(settings)

    async def update_settings(
        self, db: AsyncSession, current_user: User, data: SettingsUpdate
    ) -> SettingsResponse:
        settings = await self._get_or_create(db, current_user.id)
        update_data = data.model_dump(exclude_unset=True)

        if "pushNotifications" in update_data:
            settings.push_notifications = update_data["pushNotifications"]
        if "callRingtone" in update_data:
            settings.call_ringtone = update_data["callRingtone"]
        if "defaultAudience" in update_data:
            settings.default_audience = update_data["defaultAudience"]
        if "showOnlineStatus" in update_data:
            settings.show_online_status = update_data["showOnlineStatus"]
            if not update_data["showOnlineStatus"]:
                current_user.is_online = False

        await db.commit()
        await db.refresh(settings)
        return SettingsResponse.model_validate(settings)


settings_service = SettingsService()
