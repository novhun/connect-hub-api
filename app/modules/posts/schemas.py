from typing import List, Literal, Optional
from pydantic import BaseModel, Field
from app.modules.auth.schemas import UserResponse

ReactionType = Literal["like", "love", "care", "haha", "wow", "sad", "angry"]


class ReactionCount(BaseModel):
    like: int = 0
    love: int = 0
    care: int = 0
    haha: int = 0
    wow: int = 0
    sad: int = 0
    angry: int = 0


class CommentResponse(BaseModel):
    id: str
    user: UserResponse
    content: str
    timestamp: str
    likes: int = 0
    isLiked: bool = False
    userReaction: Optional[ReactionType] = None
    parentId: Optional[str] = None
    replies: List["CommentResponse"] = Field(default_factory=list)


class CommentCreate(BaseModel):
    content: str
    parentId: Optional[str] = None


class CommentReactionRequest(BaseModel):
    reaction: Optional[ReactionType] = None


class ReactionRequest(BaseModel):
    reaction: Optional[ReactionType] = None  # None to remove reaction


class SharedPostResponse(BaseModel):
    id: str
    author: UserResponse
    timestamp: str
    privacy: Literal["public", "friends", "only_me"]
    content: str
    images: Optional[List[str]] = None
    feeling: Optional[str] = None
    location: Optional[str] = None
    taggedGroup: Optional[str] = None


class PostCreate(BaseModel):
    content: str
    privacy: Literal["public", "friends", "only_me"] = "public"
    images: Optional[List[str]] = None
    feeling: Optional[str] = None
    location: Optional[str] = None
    taggedGroup: Optional[str] = None
    sharedPostId: Optional[str] = None


class PostUpdate(BaseModel):
    content: Optional[str] = None
    privacy: Optional[Literal["public", "friends", "only_me"]] = None
    images: Optional[List[str]] = None
    feeling: Optional[str] = None
    location: Optional[str] = None
    taggedGroup: Optional[str] = None


class PostResponse(BaseModel):
    id: str
    author: UserResponse
    timestamp: str
    privacy: Literal["public", "friends", "only_me"]
    content: str
    images: Optional[List[str]] = None
    reactionCounts: ReactionCount
    userReaction: Optional[ReactionType] = None
    comments: List[CommentResponse] = []
    sharesCount: int = 0
    isSaved: bool = False
    feeling: Optional[str] = None
    location: Optional[str] = None
    taggedGroup: Optional[str] = None
    sharedPostId: Optional[str] = None
    sharedPost: Optional[SharedPostResponse] = None


class PostListResponse(BaseModel):
    total: int
    posts: List[PostResponse]
