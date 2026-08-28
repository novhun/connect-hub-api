import json
import logging
import uuid
from typing import Dict, Optional, Set
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("connect_hub.peerjs")


class PeerJSServer:
    def __init__(self):
        # Maps peer_id -> WebSocket connection
        self.active_peers: Dict[str, WebSocket] = {}
        # Maps room_id -> Set of peer_ids
        self.rooms: Dict[str, Set[str]] = {}
        # Maps peer_id -> user_id
        self.peer_to_user: Dict[str, str] = {}
        # Maps user_id -> peer_id
        self.user_to_peer: Dict[str, str] = {}

    def generate_peer_id(self) -> str:
        """Generates a unique PeerJS client identifier."""
        return f"peer-{uuid.uuid4().hex[:12]}"

    async def connect_peer(self, websocket: WebSocket, peer_id: str, user_id: Optional[str] = None):
        """Registers a newly connected PeerJS client."""
        await websocket.accept()
        self.active_peers[peer_id] = websocket
        if user_id:
            self.peer_to_user[peer_id] = user_id
            self.user_to_peer[user_id] = peer_id

        # Send standard PeerJS OPEN acknowledgment
        await websocket.send_text(json.dumps({
            "type": "OPEN",
            "peerId": peer_id,
            "message": "Connected to Connect-Hub PeerJS Broker"
        }))
        logger.info(f"PeerJS Client connected: peer_id={peer_id}, user_id={user_id}")

    def disconnect_peer(self, peer_id: str):
        """Unregisters a disconnected PeerJS client."""
        if peer_id in self.active_peers:
            del self.active_peers[peer_id]
        
        user_id = self.peer_to_user.pop(peer_id, None)
        if user_id and self.user_to_peer.get(user_id) == peer_id:
            del self.user_to_peer[user_id]

        # Remove from any rooms
        for room_id, peers in list(self.rooms.items()):
            if peer_id in peers:
                peers.remove(peer_id)
                if not peers:
                    del self.rooms[room_id]

        logger.info(f"PeerJS Client disconnected: {peer_id}")

    async def handle_message(self, sender_peer_id: str, raw_message: str):
        """
        Processes and routes PeerJS / WebRTC signaling messages.
        Message types: OFFER, ANSWER, CANDIDATE, LEAVE, HEARTBEAT, JOIN_ROOM, CALL_INVITE.
        """
        try:
            data = json.loads(raw_message)
            msg_type = data.get("type", "").upper()
            dst_peer_id = data.get("dst")

            # Heartbeat handling
            if msg_type in ["HEARTBEAT", "PING"]:
                ws = self.active_peers.get(sender_peer_id)
                if ws:
                    await ws.send_text(json.dumps({"type": "PONG"}))
                return

            # Room management
            if msg_type == "JOIN_ROOM":
                room_id = data.get("roomId")
                if room_id:
                    if room_id not in self.rooms:
                        self.rooms[room_id] = set()
                    self.rooms[room_id].add(sender_peer_id)
                    # Broadcast to other room members
                    await self.broadcast_to_room(
                        room_id,
                        {"type": "PEER_JOINED", "peerId": sender_peer_id, "roomId": room_id},
                        exclude_peer=sender_peer_id
                    )
                return

            if msg_type == "LEAVE_ROOM":
                room_id = data.get("roomId")
                if room_id and room_id in self.rooms:
                    self.rooms[room_id].discard(sender_peer_id)
                    await self.broadcast_to_room(
                        room_id,
                        {"type": "PEER_LEFT", "peerId": sender_peer_id, "roomId": room_id},
                        exclude_peer=sender_peer_id
                    )
                return

            # Direct Peer-to-Peer Signaling (OFFER, ANSWER, CANDIDATE, LEAVE, CALL_INVITE)
            if dst_peer_id and dst_peer_id in self.active_peers:
                target_ws = self.active_peers[dst_peer_id]
                data["src"] = sender_peer_id
                await target_ws.send_text(json.dumps(data))
            else:
                # Target not connected or invalid
                ws = self.active_peers.get(sender_peer_id)
                if ws and dst_peer_id:
                    await ws.send_text(json.dumps({
                        "type": "ERROR",
                        "error": f"Peer {dst_peer_id} is not online or unreachable",
                        "dst": dst_peer_id
                    }))

        except Exception as e:
            logger.error(f"Error handling PeerJS message from {sender_peer_id}: {e}")

    async def broadcast_to_room(self, room_id: str, message_dict: dict, exclude_peer: Optional[str] = None):
        """Broadcasts a signaling payload to all peers inside a room."""
        if room_id not in self.rooms:
            return

        payload = json.dumps(message_dict)
        for peer_id in list(self.rooms[room_id]):
            if peer_id == exclude_peer:
                continue
            ws = self.active_peers.get(peer_id)
            if ws:
                try:
                    await ws.send_text(payload)
                except Exception as e:
                    logger.warning(f"Failed to send room broadcast to {peer_id}: {e}")


peerjs_manager = PeerJSServer()
