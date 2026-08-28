from datetime import datetime, timezone
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.auth.models import User
from .models import SupportMessage
from .schemas import SendSupportMessageResponse, SupportMessageResponse

WELCOME_MESSAGE = (
    "Hi! I'm the ConnectHub Assistant. Ask me about posts, stories, groups, or calls "
    "and I'll do my best to help. For anything else, our team follows up by email."
)


def format_timestamp(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime("%I:%M %p").lstrip("0")


def generate_reply(user_text: str) -> str:
    lower = user_text.lower()
    if any(k in lower for k in ["post", "photo", "picture", "upload"]):
        return (
            "You can share posts and upload photos using the 'Create Post' box at the top of "
            "your feed or the button in the left sidebar."
        )
    if any(k in lower for k in ["story", "stories"]):
        return (
            "Stories stay active for 24 hours. Tap '+ Create Story' on your stories carousel "
            "to share a quick update."
        )
    if any(k in lower for k in ["group", "community"]):
        return (
            "You can browse and join communities from the Groups tab, or create your own "
            "group from there."
        )
    if any(k in lower for k in ["call", "voice", "video"]):
        return "ConnectHub supports real audio and video calls — start one from the Calls tab or a chat window."
    if any(k in lower for k in ["password", "login", "account", "sign in"]):
        return "For account or password issues, use 'Forgot password' on the login screen, or change it from Settings."
    return (
        "Thanks for reaching out! Our team will review your message. In the meantime, feel "
        "free to ask about posts, stories, groups, or calls."
    )


class SupportService:
    async def get_history(self, db: AsyncSession, current_user: User) -> List[SupportMessageResponse]:
        stmt = (
            select(SupportMessage)
            .where(SupportMessage.user_id == current_user.id)
            .order_by(SupportMessage.created_at.asc())
        )
        result = await db.execute(stmt)
        messages = list(result.scalars().all())

        if not messages:
            welcome = SupportMessage(
                user_id=current_user.id,
                sender="assistant",
                text=WELCOME_MESSAGE,
            )
            db.add(welcome)
            await db.commit()
            await db.refresh(welcome)
            messages = [welcome]

        return [
            SupportMessageResponse(id=m.id, sender=m.sender, text=m.text, timestamp=format_timestamp(m.created_at))
            for m in messages
        ]

    async def send_message(
        self, db: AsyncSession, current_user: User, text: str
    ) -> SendSupportMessageResponse:
        user_msg = SupportMessage(user_id=current_user.id, sender="user", text=text.strip())
        db.add(user_msg)
        await db.flush()

        assistant_msg = SupportMessage(
            user_id=current_user.id,
            sender="assistant",
            text=generate_reply(text),
        )
        db.add(assistant_msg)
        await db.commit()
        await db.refresh(user_msg)
        await db.refresh(assistant_msg)

        return SendSupportMessageResponse(
            userMessage=SupportMessageResponse(
                id=user_msg.id, sender=user_msg.sender, text=user_msg.text, timestamp=format_timestamp(user_msg.created_at)
            ),
            assistantMessage=SupportMessageResponse(
                id=assistant_msg.id,
                sender=assistant_msg.sender,
                text=assistant_msg.text,
                timestamp=format_timestamp(assistant_msg.created_at),
            ),
        )


support_service = SupportService()
