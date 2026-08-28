from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.modules.auth.models import User
from app.modules.posts.models import Post
from .models import Group, GroupMember
from .schemas import GroupCreate, GroupMemberResponse, GroupResponse, GroupUpdate


def format_members_count(count: int) -> str:
    if count >= 1000:
        return f"{count / 1000:.1f}K members".replace(".0K", "K")
    return f"{count} members"


class GroupService:
    async def _format_group(
        self, db: AsyncSession, group: Group, current_user_id: Optional[str] = None
    ) -> GroupResponse:
        members_count = len(group.members)
        is_managed = False
        joined = False

        if current_user_id:
            for m in group.members:
                if m.user_id == current_user_id:
                    joined = True
                    if m.role == "admin" or group.creator_id == current_user_id:
                        is_managed = True

        # Count recent posts for this group
        stmt = select(func.count(Post.id)).where(Post.tagged_group == group.name)
        res = await db.execute(stmt)
        recent_posts_count = res.scalar() or 0

        return GroupResponse(
            id=group.id,
            name=group.name,
            icon=group.icon,
            coverImage=group.cover_image,
            description=group.description,
            isPrivate=group.is_private,
            membersCount=format_members_count(members_count),
            membersNumber=members_count,
            isManaged=is_managed,
            joined=joined,
            recentPostsCount=recent_posts_count,
        )

    async def list_groups(
        self,
        db: AsyncSession,
        current_user_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[GroupResponse]:
        stmt = (
            select(Group)
            .options(selectinload(Group.members))
            .offset(skip)
            .limit(limit)
            .order_by(Group.name.asc())
        )
        result = await db.execute(stmt)
        groups = result.scalars().all()
        return [await self._format_group(db, g, current_user_id) for g in groups]

    async def get_group_by_id(
        self, db: AsyncSession, group_id: str, current_user_id: Optional[str] = None
    ) -> GroupResponse:
        stmt = select(Group).options(selectinload(Group.members)).where(Group.id == group_id)
        result = await db.execute(stmt)
        group = result.scalars().first()
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
        return await self._format_group(db, group, current_user_id)

    async def create_group(
        self, db: AsyncSession, current_user: User, group_in: GroupCreate
    ) -> GroupResponse:
        # Check duplicate name
        stmt = select(Group).where(Group.name == group_in.name.strip())
        res = await db.execute(stmt)
        if res.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="A group with this name already exists"
            )

        new_group = Group(
            name=group_in.name.strip(),
            icon=group_in.icon,
            cover_image=group_in.coverImage,
            description=group_in.description.strip(),
            is_private=group_in.isPrivate,
            creator_id=current_user.id,
        )
        db.add(new_group)
        await db.flush()

        # Add creator as admin member
        member = GroupMember(group_id=new_group.id, user_id=current_user.id, role="admin")
        db.add(member)
        await db.commit()

        return await self.get_group_by_id(db, new_group.id, current_user.id)

    async def join_group(
        self, db: AsyncSession, current_user: User, group_id: str
    ) -> GroupResponse:
        stmt = select(GroupMember).where(
            GroupMember.group_id == group_id, GroupMember.user_id == current_user.id
        )
        result = await db.execute(stmt)
        if not result.scalars().first():
            member = GroupMember(group_id=group_id, user_id=current_user.id, role="member")
            db.add(member)
            await db.commit()
        return await self.get_group_by_id(db, group_id, current_user.id)

    async def leave_group(
        self, db: AsyncSession, current_user: User, group_id: str
    ) -> GroupResponse:
        stmt = select(GroupMember).where(
            GroupMember.group_id == group_id, GroupMember.user_id == current_user.id
        )
        result = await db.execute(stmt)
        member = result.scalars().first()
        if member:
            await db.delete(member)
            await db.commit()
        return await self.get_group_by_id(db, group_id, current_user.id)

    async def update_group(
        self, db: AsyncSession, current_user: User, group_id: str, data: GroupUpdate
    ) -> GroupResponse:
        stmt = select(Group).options(selectinload(Group.members)).where(Group.id == group_id)
        result = await db.execute(stmt)
        group = result.scalars().first()
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
        if group.creator_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

        if data.name is not None:
            new_name = data.name.strip()
            if new_name != group.name:
                # Check duplicate
                check_stmt = select(Group).where(Group.name == new_name)
                check_res = await db.execute(check_stmt)
                if check_res.scalars().first():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST, detail="A group with this name already exists"
                    )
                group.name = new_name

        if data.icon is not None:
            group.icon = data.icon
        if data.coverImage is not None:
            group.cover_image = data.coverImage or None
        if data.description is not None:
            group.description = data.description.strip()
        if data.isPrivate is not None:
            group.is_private = data.isPrivate

        await db.commit()
        await db.refresh(group)
        return await self.get_group_by_id(db, group.id, current_user.id)

    async def get_group_members(
        self, db: AsyncSession, group_id: str
    ) -> List[GroupMemberResponse]:
        stmt = select(Group).where(Group.id == group_id)
        result = await db.execute(stmt)
        group = result.scalars().first()
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

        stmt_members = (
            select(GroupMember, User)
            .join(User, GroupMember.user_id == User.id)
            .where(GroupMember.group_id == group_id)
            .order_by(GroupMember.joined_at.asc())
        )
        res = await db.execute(stmt_members)
        rows = res.all()

        members = []
        for member, user in rows:
            uname = getattr(user, "username", None) or (user.email.split("@")[0] if user.email else user.name.lower().replace(" ", ""))
            headline = user.job_title or user.role or user.bio
            members.append(
                GroupMemberResponse(
                    id=member.id,
                    user_id=user.id,
                    name=user.name,
                    username=uname,
                    avatar=user.avatar,
                    headline=headline,
                    role=member.role,
                    isCreator=user.id == group.creator_id,
                    joinedAt=member.joined_at.isoformat() if member.joined_at else "",
                )
            )
        return members

    async def delete_group(self, db: AsyncSession, current_user: User, group_id: str) -> bool:
        stmt = select(Group).where(Group.id == group_id)
        result = await db.execute(stmt)
        group = result.scalars().first()
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
        if group.creator_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
        await db.delete(group)
        await db.commit()
        return True


group_service = GroupService()
