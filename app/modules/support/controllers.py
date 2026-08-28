from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.auth.models import User
from .schemas import SendSupportMessageResponse, SupportMessageResponse
from .services import support_service


class SupportController:
    async def get_history(self, db: AsyncSession, current_user: User) -> List[SupportMessageResponse]:
        return await support_service.get_history(db, current_user)

    async def send_message(
        self, db: AsyncSession, current_user: User, text: str
    ) -> SendSupportMessageResponse:
        return await support_service.send_message(db, current_user, text)


support_controller = SupportController()
