"""
Pydantic Schemas for WhatsApp Chat Analyzer API

Request and Response models for all endpoints.
"""

from pydantic import BaseModel, Field
from typing import Any


# --- Response Models ---

class BaseResponse(BaseModel):
    """Base response wrapper."""
    success: bool = True
    message: str = "Success"
    data: Any = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = "1.0.0"


class UploadResponse(BaseModel):
    """File upload response."""
    success: bool
    message: str
    session_id: str
    total_messages: int
    participants: int
    date_range: dict[str, str]


class SummaryData(BaseModel):
    """Chat summary statistics."""
    start_date: str
    end_date: str
    total_messages: int
    total_days: int
    messages_per_day: float
    unique_participants: int
    top_contributor: dict[str, Any]
    peak_hour: int
    busiest_day: str
    key_insights: list[str] = []


class VolumeItem(BaseModel):
    """Single volume data point."""
    name: str
    messages: int


class VolumeResponse(BaseModel):
    """Volume analysis response."""
    data: list[VolumeItem]
    total_messages: int
    top_contributor: str | None
    insight: str | None = None


class SentimentItem(BaseModel):
    """Single sentiment data point."""
    name: str
    sentiment: float
    category: str


class SentimentResponse(BaseModel):
    """Sentiment analysis response."""
    data: list[SentimentItem]
    most_positive: str | None
    average_sentiment: float
    insight: str | None = None


class ResponseTimeItem(BaseModel):
    """Single response time data point."""
    name: str
    response_time: float


class ResponseTimeResponse(BaseModel):
    """Response time analysis response."""
    data: list[ResponseTimeItem]
    fastest_responder: str | None
    average_response_time: float | None
    insight: str | None = None


class HourlyItem(BaseModel):
    """Single hourly activity data point."""
    hour: int
    messages: int


class HourlyResponse(BaseModel):
    """Hourly activity response."""
    data: list[HourlyItem]
    peak_hour: int
    peak_hour_label: str
    insight: str | None = None


class WeeklyItem(BaseModel):
    """Single weekly activity data point."""
    day: str
    messages: int


class WeeklyResponse(BaseModel):
    """Weekly activity response."""
    data: list[WeeklyItem]
    busiest_day: str
    weekend_vs_weekday: dict[str, int]
    insight: str | None = None


class EmojiUserItem(BaseModel):
    """Emoji user data point."""
    name: str
    emoji_count: int


class AuthorEmojiItem(BaseModel):
    """Emoji count for a specific emoji."""
    emoji: str
    count: int


class AuthorSummaryItem(BaseModel):
    """Detailed emoji summary for an author."""
    name: str
    top_emojis: list[AuthorEmojiItem]
    primary_emoji: str


class EmojiResponse(BaseModel):
    """Emoji analysis response."""
    top_users: list[EmojiUserItem]
    top_emojis: list[TopEmojiItem]
    author_summaries: list[AuthorSummaryItem]
    total_emojis: int
    insight: str | None = None


class LeaderboardItem(BaseModel):
    """Leaderboard entry."""
    rank: int
    name: str
    messages: int
    percentage: float


class LeaderboardResponse(BaseModel):
    """Leaderboard response."""
    data: list[LeaderboardItem]


class MessageLengthItem(BaseModel):
    """Message length data point."""
    name: str
    avg_length: float


class LongestMessage(BaseModel):
    """Longest message info."""
    author: str
    length: int
    preview: str


class MessageLengthResponse(BaseModel):
    """Message length response."""
    data: list[MessageLengthItem]
    longest_message: LongestMessage
    insight: str | None = None


class LinkItem(BaseModel):
    """Link sharing data point."""
    name: str
    links: int


class LinkResponse(BaseModel):
    """Link sharing response."""
    data: list[LinkItem]
    total_links: int
    top_sharer: str | None
    insight: str | None = None


class AchievementItem(BaseModel):
    """Achievement data point."""
    name: str
    badges: list[str]


class AchievementsResponse(BaseModel):
    """Achievements response."""
    achievements: list[AchievementItem]
    insight: str | None = None


class ConversationRoleItem(BaseModel):
    """Conversation role data point."""
    name: str
    count: int


class ConversationRolesResponse(BaseModel):
    """Conversation roles response."""
    starters: list[ConversationRoleItem]
    enders: list[ConversationRoleItem]
    top_starter: str | None
    top_ender: str | None
    insight: str | None = None


class MonologueItem(BaseModel):
    """Monologue data point."""
    name: str
    consecutive_messages: int


class MonologueResponse(BaseModel):
    """Monologue response."""
    data: list[MonologueItem]
    top_monologuer: str | None
    insight: str | None = None


# --- Extended Models for Missing Features ---

class WordFrequencyItem(BaseModel):
    """Word frequency data point."""
    text: str
    value: int


class WordFrequencyResponse(BaseModel):
    """Word frequency analysis response."""
    data: list[WordFrequencyItem]
    insight: str | None = None


class ComparisonMetric(BaseModel):
    """Single metric in user comparison."""
    user: float | int
    group_avg: float | int


class ComparisonResponse(BaseModel):
    """User vs Group comparison response."""
    user_name: str
    messages: ComparisonMetric
    avg_message_length: ComparisonMetric
    response_time: ComparisonMetric
    positivity: ComparisonMetric
    emojis: ComparisonMetric


class ErrorResponse(BaseModel):
    """Error response."""
    success: bool = False
    message: str
    detail: str | None = None
