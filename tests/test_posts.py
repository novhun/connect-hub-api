import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_get_posts(client: AsyncClient, auth_headers: dict):
    # 1. Create post
    create_payload = {
        "content": "Hello Connect-Hub community! 🚀",
        "privacy": "public",
        "feeling": "excited",
        "location": "Phnom Penh",
        "images": ["https://example.com/image1.png"],
    }
    create_res = await client.post("/api/v1/posts", json=create_payload, headers=auth_headers)
    assert create_res.status_code == 201
    post = create_res.json()
    assert post["content"] == "Hello Connect-Hub community! 🚀"
    assert post["feeling"] == "excited"
    assert post["reactionCounts"]["like"] == 0
    post_id = post["id"]

    # 2. Get feed
    feed_res = await client.get("/api/v1/posts", headers=auth_headers)
    assert feed_res.status_code == 200
    feed = feed_res.json()
    assert len(feed) >= 1
    assert feed[0]["id"] == post_id

    # 3. React to post
    react_res = await client.post(
        f"/api/v1/posts/{post_id}/react",
        json={"reaction": "love"},
        headers=auth_headers,
    )
    assert react_res.status_code == 200
    updated_post = react_res.json()
    assert updated_post["userReaction"] == "love"
    assert updated_post["reactionCounts"]["love"] == 1

    # 4. Add comment
    comment_res = await client.post(
        f"/api/v1/posts/{post_id}/comments",
        json={"content": "Great post! 🎉"},
        headers=auth_headers,
    )
    assert comment_res.status_code == 200
    post_with_comment = comment_res.json()
    assert len(post_with_comment["comments"]) == 1
    assert post_with_comment["comments"][0]["content"] == "Great post! 🎉"

    # 5. Save post
    save_res = await client.post(f"/api/v1/posts/{post_id}/save", headers=auth_headers)
    assert save_res.status_code == 200
    assert save_res.json()["isSaved"] is True

    # 6. Share post
    share_res = await client.post(f"/api/v1/posts/{post_id}/share")
    assert share_res.status_code == 200
    assert share_res.json()["sharesCount"] == 1
