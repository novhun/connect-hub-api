import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_stories_flow(client: AsyncClient, auth_headers: dict):
    # 1. Create Story
    create_res = await client.post(
        "/api/v1/stories",
        json={"storyImage": "https://example.com/story.png", "caption": "Hiking day! 🏔️"},
        headers=auth_headers,
    )
    assert create_res.status_code == 201
    story = create_res.json()
    assert story["caption"] == "Hiking day! 🏔️"
    story_id = story["id"]

    # 2. Get active stories
    list_res = await client.get("/api/v1/stories", headers=auth_headers)
    assert list_res.status_code == 200
    stories = list_res.json()
    assert len(stories) >= 1
    assert any(s["id"] == story_id for s in stories)

    # 3. Mark story viewed
    view_res = await client.post(f"/api/v1/stories/{story_id}/view", headers=auth_headers)
    assert view_res.status_code == 200
    assert view_res.json()["success"] is True


@pytest.mark.asyncio
async def test_groups_flow(client: AsyncClient, auth_headers: dict):
    # 1. Create Group
    create_res = await client.post(
        "/api/v1/groups",
        json={
            "name": "Design Explorers",
            "icon": "https://example.com/icon.png",
            "coverImage": "https://example.com/cover.png",
            "description": "Designers sharing Figma tokens and prototypes.",
            "isPrivate": False,
        },
        headers=auth_headers,
    )
    assert create_res.status_code == 201
    group = create_res.json()
    assert group["name"] == "Design Explorers"
    assert group["isManaged"] is True
    group_id = group["id"]

    # 2. List Groups
    list_res = await client.get("/api/v1/groups", headers=auth_headers)
    assert list_res.status_code == 200
    groups = list_res.json()
    assert len(groups) >= 1

    # 3. Leave and Join Group
    leave_res = await client.post(f"/api/v1/groups/{group_id}/leave", headers=auth_headers)
    assert leave_res.status_code == 200
    assert leave_res.json()["joined"] is False

    join_res = await client.post(f"/api/v1/groups/{group_id}/join", headers=auth_headers)
    assert join_res.status_code == 200
    assert join_res.json()["joined"] is True
