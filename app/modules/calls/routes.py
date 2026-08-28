import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, Header, Query, Request, Response, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.peerjs_server import peerjs_manager
from app.modules.auth.models import User
from app.modules.auth.services import get_current_user
from .controllers import call_controller
from .schemas import (
    CallInitiateRequest,
    CallLogResponse,
    CallSessionResponse,
    CallStatusUpdateRequest,
)

logger = logging.getLogger("connect_hub.calls_routes")
router = APIRouter(tags=["Calls & WebRTC PeerJS"])


# 1. Calls REST API
@router.post("/api/v1/calls/initiate", response_model=CallSessionResponse, status_code=status.HTTP_201_CREATED)
async def initiate_call(
    req: CallInitiateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Initiate an audio or video call session."""
    return await call_controller.initiate(db, current_user, req)


@router.patch("/api/v1/calls/{session_id}/status", response_model=CallSessionResponse)
async def update_call_status(
    session_id: str,
    req: CallStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update call session status (connected, completed, missed, declined)."""
    return await call_controller.update_status(db, session_id, req)


@router.get("/api/v1/calls/history", response_model=List[CallLogResponse])
async def get_call_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get call history logs for the current user."""
    return await call_controller.get_history(db, current_user, skip, limit)


# 2. PeerJS Server Protocol Endpoints
@router.get("/peerjs/id")
@router.get("/peerjs/{key}/id")
def get_peer_id(key: Optional[str] = None):
    """PeerJS client handshake: returns a new unique peer ID."""
    return Response(content=peerjs_manager.generate_peer_id(), media_type="text/plain")


@router.websocket("/peerjs")
@router.websocket("/ws/peerjs/{peer_id}")
async def peerjs_signaling_websocket(
    websocket: WebSocket,
    peer_id: Optional[str] = None,
    id: Optional[str] = Query(None),
    token: Optional[str] = Query(None),
    key: Optional[str] = Query(None),
):
    """PeerJS WebRTC Signaling WebSocket server."""
    actual_peer_id = peer_id or id or peerjs_manager.generate_peer_id()
    await peerjs_manager.connect_peer(websocket, actual_peer_id)
    try:
        while True:
            raw_msg = await websocket.receive_text()
            await peerjs_manager.handle_message(actual_peer_id, raw_msg)
    except WebSocketDisconnect:
        peerjs_manager.disconnect_peer(actual_peer_id)
    except Exception as e:
        logger.error(f"PeerJS socket error for {actual_peer_id}: {e}")
        peerjs_manager.disconnect_peer(actual_peer_id)
