"""
WhatsApp Chat Analysis Endpoints

All analysis endpoints for the React/Recharts frontend.
"""

from fastapi import APIRouter, Query

from api.routes.upload import get_analyzer
from api.schemas import (
    VolumeResponse,
    SentimentResponse,
    ResponseTimeResponse,
    HourlyResponse,
    WeeklyResponse,
    EmojiResponse,
    LeaderboardResponse,
    MessageLengthResponse,
    LinkResponse,
    AchievementsResponse,
    ConversationRolesResponse,
    MonologueResponse,
    WordFrequencyResponse,
    ComparisonResponse,
    SummaryData,
    ErrorResponse,
)

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.get(
    "/summary",
    response_model=SummaryData,
    responses={404: {"model": ErrorResponse}}
)
async def get_summary(session_id: str = Query(..., description="Session ID from upload")):
    """
    Get executive summary of the chat.
    
    Includes total messages, participants, date range, and key stats.
    """
    analyzer = get_analyzer(session_id)
    return analyzer.get_summary()


@router.get(
    "/volume",
    response_model=VolumeResponse,
    responses={404: {"model": ErrorResponse}}
)
async def get_volume(
    session_id: str = Query(..., description="Session ID from upload"),
    limit: int = Query(10, ge=1, le=50, description="Max authors to return")
):
    """
    Get message volume per author.
    
    Returns data ready for Recharts BarChart.
    """
    analyzer = get_analyzer(session_id)
    return analyzer.analyze_volume(limit=limit)


@router.get(
    "/sentiment",
    response_model=SentimentResponse,
    responses={404: {"model": ErrorResponse}}
)
async def get_sentiment(
    session_id: str = Query(..., description="Session ID from upload"),
    limit: int = Query(10, ge=1, le=50, description="Max authors to return")
):
    """
    Get sentiment analysis per author.
    
    Positive values = positive sentiment, negative = negative.
    """
    analyzer = get_analyzer(session_id)
    return analyzer.analyze_sentiment(limit=limit)


@router.get(
    "/response-time",
    response_model=ResponseTimeResponse,
    responses={404: {"model": ErrorResponse}}
)
async def get_response_time(
    session_id: str = Query(..., description="Session ID from upload"),
    limit: int = Query(10, ge=1, le=50, description="Max authors to return")
):
    """
    Get average response time per author.
    
    Response time is in minutes.
    """
    analyzer = get_analyzer(session_id)
    return analyzer.analyze_response_time(limit=limit)


@router.get(
    "/activity/hourly",
    response_model=HourlyResponse,
    responses={404: {"model": ErrorResponse}}
)
async def get_hourly_activity(
    session_id: str = Query(..., description="Session ID from upload")
):
    """
    Get message activity by hour of day (0-23).
    
    Great for Recharts AreaChart or LineChart.
    """
    analyzer = get_analyzer(session_id)
    return analyzer.analyze_hourly_activity()


@router.get(
    "/activity/weekly",
    response_model=WeeklyResponse,
    responses={404: {"model": ErrorResponse}}
)
async def get_weekly_activity(
    session_id: str = Query(..., description="Session ID from upload")
):
    """
    Get message activity by day of week.
    
    Days are ordered Monday-Sunday.
    """
    analyzer = get_analyzer(session_id)
    return analyzer.analyze_weekly_activity()


@router.get(
    "/emojis",
    response_model=EmojiResponse,
    responses={404: {"model": ErrorResponse}}
)
async def get_emojis(
    session_id: str = Query(..., description="Session ID from upload"),
    limit: int = Query(10, ge=1, le=50, description="Max items to return")
):
    """
    Get emoji usage analysis.
    
    Includes top users, top emojis, and signature emojis.
    """
    analyzer = get_analyzer(session_id)
    return analyzer.analyze_emojis(limit=limit)


@router.get(
    "/leaderboard",
    response_model=LeaderboardResponse,
    responses={404: {"model": ErrorResponse}}
)
async def get_leaderboard(
    session_id: str = Query(..., description="Session ID from upload"),
    limit: int = Query(5, ge=1, le=20, description="Number of top contributors")
):
    """
    Get top contributors leaderboard.
    
    Includes rank, messages, and percentage.
    """
    analyzer = get_analyzer(session_id)
    return analyzer.get_leaderboard(limit=limit)


@router.get(
    "/message-length",
    response_model=MessageLengthResponse,
    responses={404: {"model": ErrorResponse}}
)
async def get_message_length(
    session_id: str = Query(..., description="Session ID from upload"),
    limit: int = Query(10, ge=1, le=50, description="Max authors to return")
):
    """
    Get average message length per author.
    
    Also includes the longest single message.
    """
    analyzer = get_analyzer(session_id)
    return analyzer.analyze_message_length(limit=limit)


@router.get(
    "/links",
    response_model=LinkResponse,
    responses={404: {"model": ErrorResponse}}
)
async def get_links(
    session_id: str = Query(..., description="Session ID from upload"),
    limit: int = Query(10, ge=1, le=50, description="Max authors to return")
):
    """
    Get link sharing analysis per author.
    """
    analyzer = get_analyzer(session_id)
    return analyzer.analyze_links(limit=limit)


@router.get(
    "/achievements",
    response_model=AchievementsResponse,
    responses={404: {"model": ErrorResponse}}
)
async def get_achievements(
    session_id: str = Query(..., description="Session ID from upload")
):
    """
    Get achievement badges for participants.
    
    Badges include Night Owl, Early Bird, Chatterbox, Professor, etc.
    """
    analyzer = get_analyzer(session_id)
    return analyzer.calculate_achievements()


@router.get(
    "/conversation-roles",
    response_model=ConversationRolesResponse,
    responses={404: {"model": ErrorResponse}}
)
async def get_conversation_roles(
    session_id: str = Query(..., description="Session ID from upload")
):
    """
    Get conversation starters and enders.
    
    Starters break silence after 3+ hours, enders are last before silence.
    """
    analyzer = get_analyzer(session_id)
    return analyzer.analyze_conversation_roles()


@router.get(
    "/monologues",
    response_model=MonologueResponse,
    responses={404: {"model": ErrorResponse}}
)
async def get_monologues(
    session_id: str = Query(..., description="Session ID from upload")
):
    """
    Get monologue analysis (who sends consecutive messages).
    """
    analyzer = get_analyzer(session_id)
    return analyzer.detect_monologues()


@router.get(
    "/words",
    response_model=WordFrequencyResponse,
    responses={404: {"model": ErrorResponse}}
)
async def get_word_frequency(
    session_id: str = Query(..., description="Session ID from upload"),
    limit: int = Query(100, ge=10, le=500, description="Number of words to return")
):
    """
    Get word frequency list for Word Cloud.
    """
    analyzer = get_analyzer(session_id)
    return analyzer.analyze_word_frequency(limit=limit)


@router.get(
    "/compare",
    response_model=ComparisonResponse,
    responses={404: {"model": ErrorResponse}}
)
async def compare_user(
    session_id: str = Query(..., description="Session ID from upload"),
    user_name: str = Query(..., description="Exact name of the user to compare")
):
    """
    Compare a specific user to the group averages.
    
    Includes messages, length, response time, positivity, and emojis.
    """
    analyzer = get_analyzer(session_id)
    comparison = analyzer.compare_user_to_group(user_name)
    if not comparison:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"User '{user_name}' not found in this session.")
    return comparison
