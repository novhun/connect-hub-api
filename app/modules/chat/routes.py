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
from .schemas import (
    ConversationSummary,
    CreateGroupChatRequest,
    DirectMessage,
    GroupChatMessageResponse,
    GroupChatSummary,
    InviteMembersRequest,
    SendGroupMessageRequest,
    SendMessageRequest,
    UpdateGroupChatRequest,
)
from .services import chat_manager, chat_service

logger = logging.getLogger("connect_hub.chat_routes")
router = APIRouter(prefix="/chat", tags=["Chat & Messaging"])


# -----------------------------------------------------------------------------
# Direct Messages & Conversations
# -----------------------------------------------------------------------------

@router.get("/conversations", response_model=List[ConversationSummary])
async def get_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all conversations (friends and anyone who ever chatted with current user)."""
    return await chat_controller.get_conversations(db=db, current_user=current_user)


# -----------------------------------------------------------------------------
# Group Chat REST Endpoints (must precede /{user_id} path parameter!)
# -----------------------------------------------------------------------------

@router.post("/groups", response_model=GroupChatSummary, status_code=status.HTTP_201_CREATED)
async def create_group_chat(
    req: CreateGroupChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new group chat and invite initial members."""
    return await chat_controller.create_group_chat(db=db, current_user=current_user, data=req)


@router.get("/groups", response_model=List[GroupChatSummary])
async def get_user_group_chats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all group chats the current user is a member of."""
    return await chat_controller.get_user_group_chats(db=db, current_user=current_user)


@router.post("/groups/join/{invite_code}", response_model=GroupChatSummary)
async def join_group_by_invite_code(
    invite_code: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Join a group chat using an invite code link."""
    return await chat_controller.join_by_invite_code(db=db, current_user=current_user, invite_code=invite_code)


@router.get("/groups/{group_id}", response_model=GroupChatSummary)
async def get_group_chat_details(
    group_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get group chat details including active members."""
    return await chat_controller.get_group_chat(db=db, current_user=current_user, group_id=group_id)


@router.patch("/groups/{group_id}", response_model=GroupChatSummary)
async def update_group_chat_details(
    group_id: str,
    req: UpdateGroupChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update group chat name, avatar, or description."""
    return await chat_controller.update_group_chat(db=db, current_user=current_user, group_id=group_id, data=req)


@router.post("/groups/{group_id}/invite", response_model=GroupChatSummary)
async def invite_members_to_group(
    group_id: str,
    req: InviteMembersRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Invite/add members to an existing group chat."""
    return await chat_controller.invite_members(db=db, current_user=current_user, group_id=group_id, data=req)


@router.delete("/groups/{group_id}/leave")
async def leave_group_chat(
    group_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Leave a group chat."""
    return await chat_controller.leave_group_chat(db=db, current_user=current_user, group_id=group_id)


@router.get("/groups/{group_id}/messages", response_model=List[GroupChatMessageResponse])
async def get_group_messages(
    group_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve message history for a group chat."""
    return await chat_controller.get_group_messages(
        db=db, current_user=current_user, group_id=group_id, skip=skip, limit=limit
    )


@router.post("/groups/{group_id}/messages", response_model=GroupChatMessageResponse, status_code=status.HTTP_201_CREATED)
async def send_group_message(
    group_id: str,
    msg_in: SendGroupMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a message to a group chat."""
    return await chat_controller.send_group_message(
        db=db, current_user=current_user, group_id=group_id, data=msg_in
    )


# -----------------------------------------------------------------------------
# Direct Messages by user_id
# -----------------------------------------------------------------------------

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
    "GROUP_CALL_JOIN",
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

    # 1. Update user is_online status in DB and notify peers
    try:
        async with AsyncSessionLocal() as session:
            db_user = await session.get(User, user_id)
            if db_user:
                db_user.is_online = True
                await session.commit()
    except Exception as e:
        logger.warning(f"Failed to update online state for {user_id}: {e}")

    # 2. Send current online user list to this newly connected client
    online_ids = chat_manager.get_online_user_ids()
    await websocket.send_text(json.dumps({
        "type": "PRESENCE_SYNC",
        "onlineUserIds": online_ids,
    }))

    # 3. Broadcast this user's online presence to all other connected users
    await chat_manager.broadcast(
        {
            "type": "USER_PRESENCE",
            "userId": user_id,
            "isOnline": True,
        },
        exclude_user_id=user_id,
    )

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                msg_type = msg.get("type")

                if msg_type == "PING":
                    await websocket.send_text(json.dumps({"type": "PONG"}))

                elif msg_type == "SEND_MESSAGE":
                    target_id = msg.get("receiverId")
                    text = msg.get("text")
                    if target_id and text:
                        async with AsyncSessionLocal() as session:
                            await chat_service.send_message(session, user_id, target_id, text)

                elif msg_type == "SEND_GROUP_MESSAGE":
                    group_id = msg.get("groupId")
                    text = msg.get("text")
                    if group_id and text:
                        async with AsyncSessionLocal() as session:
                            user_obj = await session.get(User, user_id)
                            if user_obj:
                                await chat_service.send_group_message(session, user_obj, group_id, text=text)

                elif msg_type == "GROUP_CALL_INVITE":
                    group_id = msg.get("groupId")
                    if group_id:
                        async with AsyncSessionLocal() as session:
                            member_ids = await chat_service.get_group_member_ids(session, group_id)
                            user_obj = await session.get(User, user_id)
                            relay = dict(msg)
                            relay["fromUserId"] = user_id
                            relay["callerId"] = user_id
                            if user_obj:
                                relay["callerName"] = user_obj.name
                                relay["callerAvatar"] = user_obj.avatar
                            await chat_manager.send_to_users(member_ids, relay, exclude_user_id=user_id)

                elif msg_type in ["GROUP_CALL_END", "GROUP_CALL_LEAVE"]:
                    group_id = msg.get("groupId")
                    if group_id:
                        async with AsyncSessionLocal() as session:
                            member_ids = await chat_service.get_group_member_ids(session, group_id)
                            relay = dict(msg)
                            relay["fromUserId"] = user_id
                            await chat_manager.send_to_users(member_ids, relay, exclude_user_id=user_id)

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
        # Update user offline state in DB and broadcast to peers
        try:
            async with AsyncSessionLocal() as session:
                db_user = await session.get(User, user_id)
                if db_user:
                    db_user.is_online = False
                    await session.commit()
        except Exception as e:
            logger.warning(f"Failed to update offline state for {user_id}: {e}")

        await chat_manager.broadcast({
            "type": "USER_PRESENCE",
            "userId": user_id,
            "isOnline": False,
        })

