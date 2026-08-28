import io
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_peerjs_id_handshake(client: AsyncClient):
    res = await client.get("/peerjs/id")
    assert res.status_code == 200
    peer_id = res.text
    assert peer_id.startswith("peer-")

    res_with_key = await client.get("/peerjs/customkey/id")
    assert res_with_key.status_code == 200
    assert res_with_key.text.startswith("peer-")


@pytest.mark.asyncio
async def test_media_upload_and_presigned(client: AsyncClient):
    # Test Multipart upload
    file_bytes = b"fake-image-content-for-connect-hub"
    files = {"file": ("test_avatar.png", io.BytesIO(file_bytes), "image/png")}
    upload_res = await client.post("/api/v1/media/upload", files=files)
    assert upload_res.status_code == 201
    data = upload_res.json()
    assert "url" in data
    assert data["filename"] == "test_avatar.png"
    assert data["size"] == len(file_bytes)

    # Test presigned URL generator
    presigned_res = await client.post(
        "/api/v1/media/presigned-url",
        json={"filename": "photo.jpg", "contentType": "image/jpeg"},
    )
    assert presigned_res.status_code == 200
    presigned_data = presigned_res.json()
    assert "fileUrl" in presigned_data
