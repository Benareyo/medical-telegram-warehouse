from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class MessageBase(BaseModel):
    message_id: int
    channel_name: str
    message_date: Optional[datetime]
    message_text: Optional[str]
    views: Optional[int]
    forwards: Optional[int]
    has_media: Optional[bool]

    class Config:
        from_attributes = True


class TopProduct(BaseModel):
    term: str
    frequency: int


class ChannelActivity(BaseModel):
    channel_name: str
    total_messages: int
    total_views: int
    avg_views: float
    messages_with_images: int


class VisualContentStats(BaseModel):
    channel_name: str
    total_messages: int
    messages_with_images: int
    image_percentage: float


class SearchResult(BaseModel):
    message_id: int
    channel_name: str
    message_date: Optional[datetime]
    message_text: Optional[str]
    views: Optional[int]