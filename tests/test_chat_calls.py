import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_chat_flow(client: AsyncClient, auth_headers: dict):
    # 1. Send direct message to another user
    target_user_id = "test-user-recipient"
    send_res = await client.post(
        f"/api/v1/chat/{target_user_id}",
        json={"text": "Hey there! Testing chat."},
        headers=auth_headers,
    )
    assert send_res.status_code == 201
    msg = send_res.json()
    assert msg["text"] == "Hey there! Testing chat."
    assert msg["isMe"] is True

    # 2. Get message history
    history_res = await client.get(f"/api/v1/chat/{target_user_id}", headers=auth_headers)
    assert history_res.status_code == 200
    msgs = history_res.json()
    assert len(msgs) >= 1
    assert msgs[-1]["text"] == "Hey there! Testing chat."


@pytest.mark.asyncio
async def test_calls_flow(client: AsyncClient, auth_headers: dict):
    # 1. Initiate audio call
    init_res = await client.post(
        "/api/v1/calls/initiate",
        json={"receiverId": "test-user-recipient", "callType": "video"},
        headers=auth_headers,
    )
    assert init_res.status_code == 201
    session = init_res.json()
    assert session["callType"] == "video"
    assert session["status"] == "initiating"
    session_id = session["id"]

    # 2. Update status to connected
    update_res = await client.patch(
        f"/api/v1/calls/{session_id}/status",
        json={"status": "connected"},
        headers=auth_headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "connected"

    # 3. Update status to completed with duration
    complete_res = await client.patch(
        f"/api/v1/calls/{session_id}/status",
        json={"status": "completed", "durationSeconds": 180},
        headers=auth_headers,
    )
    assert complete_res.status_code == 200
    assert complete_res.json()["status"] == "completed"
    assert complete_res.json()["durationSeconds"] == 180

    # 4. Get call history
    hist_res = await client.get("/api/v1/calls/history", headers=auth_headers)
    assert hist_res.status_code == 200
    logs = hist_res.json()
    assert len(logs) >= 1
    assert logs[0]["duration"] == "3m 00s"
