import json
import logging
from typing import List
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal, get_db
from app.core.security import decode_access_token
from app.modules.auth.models import User
from app.modules.auth.services import auth_service, get_current_user
from .controllers import chat_controller
from .schemas import DirectMessage, SendMessageRequest
from .services import chat_manager, chat_service

logger = logging.getLogger("connect_hub.chat_routes")
router = APIRouter(prefix="/chat", tags=["Chat & Messaging"])


@router.get("/{user_id}", response_model=List[DirectMessage])
async def get_messages(
    user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve direct message history between current user and target user."""
    return await chat_controller.get_messages(
        db=db, current_user=current_user, other_user_id=user_id, skip=skip, limit=limit
    )


@router.post("/{user_id}", response_model=DirectMessage, status_code=status.HTTP_201_CREATED)
async def send_message(
    user_id: str,
    msg_in: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a direct message to a user."""
    return await chat_controller.send_message(
        db=db, current_user=current_user, receiver_id=user_id, data=msg_in
    )


@router.post("/{user_id}/read")
async def mark_as_read(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark all messages from sender as read."""
    return await chat_controller.mark_as_read(db=db, current_user=current_user, sender_id=user_id)


# Message types relayed verbatim (plus a `fromUserId` stamp) to another connected user.
# Used for call signaling: invite/accept/decline/end plus the actual WebRTC handshake.
SIGNAL_RELAY_TYPES = {
    "CALL_INVITE",
    "CALL_ACCEPT",
    "CALL_DECLINE",
    "CALL_END",
    "WEBRTC_OFFER",
    "WEBRTC_ANSWER",
    "WEBRTC_ICE_CANDIDATE",
}


# Realtime WebSocket Endpoint for Chat & Call Signaling
@router.websocket("/ws/{user_id}")
async def websocket_chat_endpoint(websocket: WebSocket, user_id: str, token: str = Query(None)):
    """
    Single persistent connection per logged-in user, authenticated via a `token`
    query param (browsers can't set custom headers on WebSocket handshakes).
    Doubles as the transport for real-time chat delivery and WebRTC call signaling,
    so it must stay connected app-wide rather than only while a chat view is open.
    """
    payload = decode_access_token(token) if token else None
    if not payload or payload.get("sub") != user_id:
        await websocket.accept()
        await websocket.close(code=4401)
        return

    await chat_manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                msg_type = msg.get("type")

                if msg_type == "SEND_MESSAGE":
                    target_id = msg.get("receiverId")
                    text = msg.get("text")
                    if target_id and text:
                        async with AsyncSessionLocal() as session:
                            await chat_service.send_message(session, user_id, target_id, text)

                elif msg_type in SIGNAL_RELAY_TYPES:
                    target_id = msg.get("targetUserId")
                    if not target_id:
                        continue
                    relay = dict(msg)
                    relay["fromUserId"] = user_id
                    delivered = await chat_manager.send_personal_message(target_id, relay)
                    if msg_type == "CALL_INVITE" and not delivered:
                        await websocket.send_text(json.dumps({
                            "type": "CALL_UNAVAILABLE",
                            "roomId": msg.get("roomId"),
                            "targetUserId": target_id,
                        }))
            except Exception as e:
                logger.error(f"Error handling websocket frame from {user_id}: {e}")
    except WebSocketDisconnect:
        chat_manager.disconnect(user_id)
