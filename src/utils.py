"""
WhatsApp Chat Utility Functions

Common helper functions used across the analyzer.
"""

import re
from textblob import TextBlob
import emoji


def clean_name(name: str, max_length: int = 15) -> str:
    """
    Truncates and cleans names for display in charts.
    
    Time Complexity: O(n) where n is name length
    Space Complexity: O(n)
    
    Args:
        name: Raw author name from chat
        max_length: Maximum length before truncation
        
    Returns:
        Cleaned and possibly truncated name
    """
    if not isinstance(name, str):
        return str(name)
    cleaned = re.sub(r'[^\w\s\-]', '', name).strip()
    return (cleaned[:max_length] + "..") if len(cleaned) > max_length else (cleaned or "Unknown")


def get_sentiment(text: str) -> float:
    """
    Returns a polarity score between -1 (Negative) and 1 (Positive).
    
    Time Complexity: O(n) where n is text length
    Space Complexity: O(n)
    
    Args:
        text: Message text to analyze
        
    Returns:
        Float between -1.0 and 1.0
    """
    return TextBlob(str(text)).sentiment.polarity


def extract_emojis(text: str) -> list[str]:
    """
    Extract all emojis from text.
    
    Time Complexity: O(n) where n is text length
    Space Complexity: O(m) where m is number of emojis
    
    Args:
        text: Text to extract emojis from
        
    Returns:
        List of emoji characters
    """
    return [c for c in str(text) if c in emoji.EMOJI_DATA]


def is_media_message(message: str) -> bool:
    """
    Check if a message is a media/omitted message.
    
    Args:
        message: Message text to check
        
    Returns:
        True if message is media placeholder
    """
    lower_msg = str(message).lower()
    return any(keyword in lower_msg for keyword in ['omitted', 'deleted', '<media'])


def extract_links(message: str) -> list[str]:
    """
    Extract all URLs from a message.
    
    Time Complexity: O(n) where n is message length
    Space Complexity: O(m) where m is number of links
    
    Args:
        message: Message text
        
    Returns:
        List of URLs found
    """
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    return re.findall(url_pattern, str(message))


def has_link(message: str) -> bool:
    """
    Check if message contains a URL.
    
    Args:
        message: Message text
        
    Returns:
        True if message contains URL
    """
    return bool(re.search(r'http|www\.', str(message), re.IGNORECASE))
