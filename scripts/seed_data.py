import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta, timezone

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal, init_db, async_engine, Base
from app.core.security import get_password_hash
from app.modules.auth.models import User
from app.modules.calls.models import CallSession
from app.modules.chat.models import Message
from app.modules.groups.models import Group, GroupMember
from app.modules.notifications.models import Notification
from app.modules.posts.models import Comment, Post, PostMedia, Reaction, SavedPost
from app.modules.stories.models import Story

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_data")


async def seed():
    logger.info("Starting database re-seeding with full rich demo data...")
    
    # Recreate tables to guarantee clean state
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc)
        default_pwd = get_password_hash("password123")

        # 1. Seed Users
        sokun = User(
            id="user-sokun",
            email="sokun@connecthub.app",
            hashed_password=default_pwd,
            name="Sokun",
            avatar="https://lh3.googleusercontent.com/aida-public/AB6AXuB1horplrAC7-0mqM4pGaHQzkfN9hQFEbB-LQk1RVMQWmH4kvrm5Wi2JO13QXkYhIOkj4bbOvM2aNCt0HSVS1T0zd8j13I9XWJsCMLRdo0vKr96D66Qo_Vn_6n0gZc0kEdYkxfj1JWmlK6xcp_K-cL30veV-dcIDDc0mgJsnZ2BPcJzZigeSg8ujHuBS90WEtA2SijWotiMoc3XWG7OIZC9yEMnaTkUHaIBTImIm1YuUfbVS1u5VXgt",
            role="Product Designer",
            bio="Passionate about UI/UX systems and responsive modern web experiences.",
            is_online=True,
            is_active=True,
            is_verified=True,
        )

        dara = User(
            id="user-dara",
            email="dara@connecthub.app",
            hashed_password=default_pwd,
            name="Dara Kim",
            avatar="https://lh3.googleusercontent.com/aida-public/AB6AXuA3okZWj4HdiL1vFZUSxOjHIkXN_ZhmWwuflHAs89NBEBGO3KEg_K6q2-cxZVAGBNJR6ldoF2W8aJMf_-TfyWJIu8DDd7_3q4ALj3Vn8yt6_cqJJgOcW-mBiucYNZlXK2AgM3RjoeyGTc1omUabuTCgmTL8qP2wgc6hJJdfslDdjuch_0br44NUvM5P9t4KBSujHTQY0f5M1IxoAjvhz3xFcGafaPCZHAz_zukIikEULBMf15pmexPJ",
            role="Senior Frontend Dev",
            is_online=True,
            is_active=True,
            is_verified=True,
        )

        vireak = User(
            id="user-vireak",
            email="vireak@connecthub.app",
            hashed_password=default_pwd,
            name="Vireak Nith",
            avatar="https://lh3.googleusercontent.com/aida-public/AB6AXuACuRj8AsvmCk2C2ENMoXlaCBrk84ZIKWvia4_9KT38863N9ix0u4y5ubDCWxMQhGO6-JCsif_vm2roezQLKxqA0FI7gq1hniWl9N9pIsv6E9AtN99rH6X0bNjvTFzX1Ukl_3WegDUjbGZXpET760vP40KxgLYcfW8_Kin6hbWtqRxh3_QzKVsVS23PoygcfgdhnPmERGdKOlx93kP_HjJIosc3nvQc86KJ-yEnQqH_9pQ5wppN0atI",
            role="Cloud Architect",
            is_online=True,
            is_active=True,
            is_verified=True,
        )

        sokunthea = User(
            id="user-sokunthea",
            email="sokunthea@connecthub.app",
            hashed_password=default_pwd,
            name="Sokunthea Pen",
            avatar="https://lh3.googleusercontent.com/aida-public/AB6AXuD1qIT7A6u_m_KGG2bLC9XgjB1WX48cvdwhF-6-IXqZLzf2sg819AmILZLR2_F5N_Doxi60Xrf7YkP8JKPGnF220G5VnhmeU051WWcH7pEcc9YLHlPS-xJHJV4_TAMlWYUwNpLXg-iE8ufsOSnTHp02SPkPOXuvzEnCtWn-WhPgURlxHNoyHpISs_NbijzQt5zCc5lp0AmgcayHfAKNiz00uu-Jk1HpfDW-zAMmp4XSDN13-VR1YHg3",
            role="Product Lead",
            is_online=True,
            is_active=True,
            is_verified=True,
        )

        chanda = User(
            id="user-chanda",
            email="chanda@connecthub.app",
            hashed_password=default_pwd,
            name="Chanda Meas",
            avatar="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80",
            role="Graphic Designer",
            is_online=False,
            last_seen="15m ago",
            is_active=True,
            is_verified=True,
        )

        bopha = User(
            id="user-bopha",
            email="bopha@connecthub.app",
            hashed_password=default_pwd,
            name="Bopha Chen",
            avatar="https://images.unsplash.com/photo-1517841905240-472988babdf9?w=150&auto=format&fit=crop&q=80",
            role="Mobile Engineer",
            is_online=True,
            is_active=True,
            is_verified=True,
        )

        db.add_all([sokun, dara, vireak, sokunthea, chanda, bopha])
        await db.flush()

        # 2. Seed Groups
        grp_tech = Group(
            id="grp-tech",
            name="Tech Enthusiasts",
            icon="https://lh3.googleusercontent.com/aida-public/AB6AXuCplSj6BXPkfU_Iuh9sCT6pU65aKiS8Lob6Y1Ln5maOzufu3HkSd-j6k1rVqM7mtUd-2_rvFEgwIm6RfdtPo58R2TMfZA1wL66In_JmVzgQgr79S_yx2faFOYNZXwvXWTaAGj13UQooaKQylMVNQ3nbtkwArrSDi88vS83F0F-368wG8Efvo0RMJRxb1se9QRyoNIjvHOa_pL5rxe2L637EV1hB7CnqUd0peC3Bi2R1rkZzREcgFnkN",
            cover_image="https://images.unsplash.com/photo-1518770660439-4636190af475?w=800&auto=format&fit=crop&q=80",
            description="A global community discussing the latest tech breakthroughs, AI software architecture, and gadgets.",
            is_private=False,
            creator_id=sokun.id,
        )

        grp_design = Group(
            id="grp-design",
            name="UI/UX Designers",
            icon="https://lh3.googleusercontent.com/aida-public/AB6AXuDR_666Z-82yP8qQj4H-q0v-zD0j8-4v36qW-t1_Mv5lE087i3q0n8o16V6k9qC-dM9E1h3mQ5sJ0qO",
            cover_image="https://images.unsplash.com/photo-1507238691740-187a5b1d37b8?w=800&auto=format&fit=crop&q=80",
            description="Sharing design systems, Figma tokens, interactive components, and usability findings.",
            is_private=False,
            creator_id=sokun.id,
        )

        grp_travel = Group(
            id="grp-travel",
            name="Cambodia Travelers",
            icon="https://images.unsplash.com/photo-1528181304800-259b08848526?w=150&auto=format&fit=crop&q=80",
            cover_image="https://images.unsplash.com/photo-1528181304800-259b08848526?w=800&auto=format&fit=crop&q=80",
            description="Hidden gems, mountain trekking trails, and heritage travel throughout Cambodia.",
            is_private=False,
            creator_id=dara.id,
        )

        db.add_all([grp_tech, grp_design, grp_travel])
        await db.flush()

        # Add Memberships
        for user in [sokun, dara, vireak, sokunthea, chanda, bopha]:
            db.add(GroupMember(group_id=grp_tech.id, user_id=user.id, role="member"))
            db.add(GroupMember(group_id=grp_design.id, user_id=user.id, role="member"))
        db.add(GroupMember(group_id=grp_travel.id, user_id=sokun.id, role="member"))

        # 3. Seed Stories
        stories = [
            Story(
                id="story-1",
                user_id=dara.id,
                story_image="https://lh3.googleusercontent.com/aida-public/AB6AXuDmgd7Eo3HN-MvSLFtCvYIssbACFz_fXKPbEycxS4NSmz0YfVF6Xwg6InI_c3xTqdATHLIeFyZCJ50rLYSVpJcI0hr-C1LTGqoeKN0grey90KZgJLdk1lW2VeY411T_tZdqEjQ-mua2Ji6E8vi3cnvtQZdejgKEGwDM1M711xTRAYy5mjIqgybRMvGVtcxKYY5YEwimeA1_QcziLo4xj0lUvaAq-7VzRTJT911CdUOW-aTLBKIC9Eej",
                caption="Sunrise over the misty pine valley! 🌲✨",
                created_at=now - timedelta(hours=2),
                expires_at=now + timedelta(hours=22),
            ),
            Story(
                id="story-2",
                user_id=vireak.id,
                story_image="https://lh3.googleusercontent.com/aida-public/AB6AXuD69O9PDlJuSAwbVDyhA0pkNx2U-NBnp6xTyUH2F4Jx7-hNf_1o9DLCFVO_0aKQweQ_sZVbtMCTJUoc6Lm7jiJcCrfiB9nKjY7tiC9YriooTvhzJTMaJbbZu3g5Mp-y8OMMicuVdLHWW6bc9_pWXp2QpsiwiHhS9zqDL-ERAmWDBgMNLoJ8F5XUwaFGfcYHLPtufjSiscefqcewjHrzC1W56UuNWKKiXcYnDLE_fYWfSzt1AAF8XFqx",
                caption="Testing the new camera gear in the alpine pass 📷",
                created_at=now - timedelta(hours=5),
                expires_at=now + timedelta(hours=19),
            ),
            Story(
                id="story-3",
                user_id=sokunthea.id,
                story_image="https://lh3.googleusercontent.com/aida-public/AB6AXuAsdNeOaSY6BThEUzBImvL09qA1aPnAHQTmIcIsNXgWU6eSV8c9cA2avPXUHupn8jej_bkyLy_PkzLOfOlacGKgEKtP1-b1f2lPnhPWdk_g6GlN9Q36XWC1UhS8x_NgjQNpT5GiNtfeZ3yg87ilz5Z4o2JRtJw1TrdL4Ci1241nBPSn7kb4ZlcmVrFn2zhjMGVsXqmBTIDyFP5uRL1oZPWC8igL4XSZop3GiYn-t6QgrHnLfCY6CPQV",
                caption="Weekend coffee and design sketching ☕🎨",
                created_at=now - timedelta(hours=14),
                expires_at=now + timedelta(hours=10),
            ),
            Story(
                id="story-4",
                user_id=bopha.id,
                story_image="https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=600&auto=format&fit=crop&q=80",
                caption="Lakeside tranquility during afternoon golden hour 🌅",
                created_at=now - timedelta(hours=20),
                expires_at=now + timedelta(hours=4),
            ),
        ]
        db.add_all(stories)

        # 4. Seed Posts
        # Post 1 (Mountain hike with 3-image grid)
        post1 = Post(
            id="post-1",
            author_id=dara.id,
            content="Just finished an amazing hike with friends! ⛰️\nNature always finds a way to heal the soul.",
            privacy="public",
            feeling="adventurous",
            location="Phnom Kulen, Cambodia",
            tagged_group="Cambodia Travelers",
            shares_count=5,
            created_at=now - timedelta(hours=2),
        )
        db.add(post1)
        await db.flush()

        media1 = [
            PostMedia(post_id=post1.id, media_url="https://lh3.googleusercontent.com/aida-public/AB6AXuAMegsuKTHwuxVrN3neJU1g9JA_MfR5GVQTQy3SYqJbbh6VIVb_yfMFS9NjUDHPvNkDYndzE3Yj5J5eTO0h-h-rYwAD8wWdTgyZP9zxgF-xbxUuCqJfXQngkeBVcyMAYrmj3GPBfW8pDoFCLkA5_rAyhXxs4iValRnmXq08brtQvKZZdAG-lEL46SOLkR1nDV_0uyG5AY5zAma8VETQtsS-hoacMO_gDMD9mjQS4J-jHGKa-561ywGG"),
            PostMedia(post_id=post1.id, media_url="https://lh3.googleusercontent.com/aida-public/AB6AXuCPFOaXWrHjwtTU3DO_OWmgDYNRHto2p5GHOLttnNoAN0ghcfpokm04TFfyAQxmjYrtXAHMQb3jXl65LYHMKpTZrMYlFycSFT0B-chUwMrbw9weFpoPC0aheKbwTKVrc0gkxPEmAekGEy1chSpLLR4mEKFufh9nzwYoJVlM70WJzNNidmnXciB9nxqL2EqHkqMbytBTDixLud3a2bK7jfLSDQcJlzNQZT8R6eTRJ7yLeEJ28uBKcyYH"),
            PostMedia(post_id=post1.id, media_url="https://lh3.googleusercontent.com/aida-public/AB6AXuCFdrymCnIajKQp8-WY6QPvXkud6BAUpGe6dBLcLB-lI7uzkIIQfEH07GLSEo2acR9n2MfiQMMDpYYYcKTycRO8zs6w3NdScQIgsxf3U-N1tGtZ6Z-OlV1Xb7YM4txpZI6A0ml5zWi4bp6kersZlXSWqQSGCn7Wc7Wy4g8iiEpjrY44DdSmle4fpE36TaIANK8yKX6XaoNEORWHJV3MnMRcVzAhpn1JauTltEKufwM1BFVuS_9Ss_2q"),
        ]
        db.add_all(media1)

        db.add(Reaction(post_id=post1.id, user_id=sokun.id, reaction_type="like"))
        db.add(Reaction(post_id=post1.id, user_id=vireak.id, reaction_type="love"))
        db.add(Reaction(post_id=post1.id, user_id=sokunthea.id, reaction_type="wow"))

        db.add(Comment(
            post_id=post1.id,
            user_id=vireak.id,
            content="That mountain trail looks absolutely stunning! Which summit did you climb?",
            created_at=now - timedelta(hours=1),
            likes_count=5,
        ))
        db.add(Comment(
            post_id=post1.id,
            user_id=sokunthea.id,
            content="Love the golden lighting in that first shot! Glad you had a great trip 🌿🙌",
            created_at=now - timedelta(minutes=45),
            likes_count=3,
        ))

        # Post 2 (Tech System Announcement)
        post2 = Post(
            id="post-2",
            author_id=vireak.id,
            content="Excited to announce our new open source UI component system for React 19 and Tailwind CSS! 🚀 Check out the interactive playground and clean modular layout tokens.",
            privacy="public",
            feeling="accomplished",
            tagged_group="Tech Enthusiasts",
            shares_count=18,
            created_at=now - timedelta(hours=4),
        )
        db.add(post2)
        await db.flush()

        db.add(PostMedia(post_id=post2.id, media_url="https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=900&auto=format&fit=crop&q=80"))
        db.add(Reaction(post_id=post2.id, user_id=sokun.id, reaction_type="like"))
        db.add(Reaction(post_id=post2.id, user_id=dara.id, reaction_type="love"))
        db.add(Reaction(post_id=post2.id, user_id=sokunthea.id, reaction_type="care"))
        db.add(SavedPost(post_id=post2.id, user_id=sokun.id))

        db.add(Comment(
            post_id=post2.id,
            user_id=dara.id,
            content="Clean architecture! Already testing this on our staging branch.",
            created_at=now - timedelta(hours=2),
            likes_count=7,
        ))

        # Post 3 (UI/UX Design Token Sync)
        post3 = Post(
            id="post-3",
            author_id=sokunthea.id,
            content="Design tokens are officially synchronized between Figma and Tailwind v4. The developer experience is 10x smoother! 🎨💻",
            privacy="public",
            feeling="happy",
            location="Phnom Penh, Cambodia",
            tagged_group="UI/UX Designers",
            shares_count=9,
            created_at=now - timedelta(hours=8),
        )
        db.add(post3)
        await db.flush()

        db.add(PostMedia(post_id=post3.id, media_url="https://images.unsplash.com/photo-1507238691740-187a5b1d37b8?w=900&auto=format&fit=crop&q=80"))
        db.add(Reaction(post_id=post3.id, user_id=sokun.id, reaction_type="love"))
        db.add(Reaction(post_id=post3.id, user_id=vireak.id, reaction_type="like"))

        # 5. Seed Direct Messages
        msgs = [
            Message(
                sender_id=dara.id,
                receiver_id=sokun.id,
                text="Hey Sokun! Loved the latest prototype you shared in UI/UX Designers.",
                created_at=now - timedelta(minutes=45),
                is_read=True,
            ),
            Message(
                sender_id=sokun.id,
                receiver_id=dara.id,
                text="Thanks Dara! Appreciate the feedback. Let's iterate on the stories carousel tokens next.",
                created_at=now - timedelta(minutes=40),
                is_read=True,
            ),
            Message(
                sender_id=dara.id,
                receiver_id=sokun.id,
                text="Sounds like a plan! Let's do a quick audio call when you're free.",
                created_at=now - timedelta(minutes=35),
                is_read=False,
            ),
        ]
        db.add_all(msgs)

        # 6. Seed Call Sessions
        calls = [
            CallSession(
                caller_id=dara.id,
                receiver_id=sokun.id,
                call_type="video",
                status="missed",
                duration_seconds=0,
                created_at=now - timedelta(hours=1),
            ),
            CallSession(
                caller_id=sokun.id,
                receiver_id=vireak.id,
                call_type="audio",
                status="completed",
                duration_seconds=860,
                started_at=now - timedelta(days=1, minutes=30),
                ended_at=now - timedelta(days=1, minutes=15),
                created_at=now - timedelta(days=1, minutes=30),
            ),
        ]
        db.add_all(calls)

        # 7. Seed Notifications
        notifs = [
            Notification(
                recipient_id=sokun.id,
                sender_id=dara.id,
                type="like",
                content="reacted to your comment in Tech Enthusiasts",
                target="Post",
                created_at=now - timedelta(minutes=15),
            ),
            Notification(
                recipient_id=sokun.id,
                sender_id=sokunthea.id,
                type="comment",
                content="commented on your photo: 'The token consistency is top-notch!'",
                target="Comment",
                created_at=now - timedelta(hours=1),
            ),
            Notification(
                recipient_id=sokun.id,
                sender_id=vireak.id,
                type="group",
                content="invited you to join UI/UX Designers weekly critique meetup",
                target="Group",
                created_at=now - timedelta(hours=3),
            ),
            Notification(
                recipient_id=sokun.id,
                sender_id=bopha.id,
                type="call",
                content="started an audio call in General Room",
                target="Call",
                created_at=now - timedelta(days=1),
            ),
        ]
        db.add_all(notifs)

        await db.commit()
        logger.info("Database successfully re-seeded with all full rich demo posts, stories, groups, and chat history!")


if __name__ == "__main__":
    asyncio.run(seed())
