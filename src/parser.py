"""
WhatsApp Chat Parser Module

Handles multiple WhatsApp export formats from Android, iOS, and Web.
Supports various date formats, time formats (12/24 hour), and separators.

Time Complexity: O(n) where n is the number of lines
Space Complexity: O(n) for storing parsed messages
"""

import re
import zipfile
from io import BytesIO
from typing import BinaryIO, Optional
import pandas as pd


# Multiple patterns to handle all WhatsApp export variations
MESSAGE_PATTERNS = [
    # Format 1: [DD/MM/YYYY, HH:MM:SS] or [DD/MM/YYYY, HH:MM:SS AM/PM] - Bracket format with seconds
    r'\[(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}:\d{2}(?:\s*[AaPp][Mm])?)\]\s*(.*?):\s*(.*)$',
    
    # Format 2: [DD/MM/YYYY, HH:MM] or [DD/MM/YYYY, HH:MM AM/PM] - Bracket format without seconds
    r'\[(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}(?:\s*[AaPp][Mm])?)\]\s*(.*?):\s*(.*)$',
    
    # Format 3: DD/MM/YYYY, HH:MM - Author: message - No bracket format (older exports)
    r'(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?)\s*-\s*(.*?):\s*(.*)$',
    
    # Format 4: [DD-MM-YYYY, HH:MM:SS] - Dash date separator
    r'\[(\d{1,2}-\d{1,2}-\d{2,4}),\s*(\d{1,2}:\d{2}:\d{2}(?:\s*[AaPp][Mm])?)\]\s*(.*?):\s*(.*)$',
    
    # Format 5: [DD.MM.YYYY, HH:MM:SS] - Dot date separator (some locales)
    r'\[(\d{1,2}\.\d{1,2}\.\d{2,4}),\s*(\d{1,2}:\d{2}:\d{2}(?:\s*[AaPp][Mm])?)\]\s*(.*?):\s*(.*)$',
]


def detect_best_pattern(lines: list[str], patterns: list[str]) -> str:
    """
    Auto-detect which pattern matches the most lines.
    
    Time Complexity: O(n*m) where n is sample size, m is number of patterns
    Space Complexity: O(1)
    
    Args:
        lines: List of chat lines
        patterns: List of regex patterns to test
        
    Returns:
        Best matching pattern string
    """
    best_pattern = patterns[0]
    best_count = 0
    
    # Sample first 100 lines for efficiency
    sample = lines[:100]
    
    for pattern in patterns:
        count = sum(1 for line in sample if re.match(pattern, line.strip()))
        if count > best_count:
            best_count = count
            best_pattern = pattern
    
    return best_pattern


def normalize_date(date_str: str) -> str:
    """
    Normalize date separators to forward slash.
    
    Time Complexity: O(n) where n is string length
    Space Complexity: O(n)
    
    Args:
        date_str: Date string with any separator
        
    Returns:
        Date string with / separators
    """
    return date_str.replace('-', '/').replace('.', '/')


def parse_chat_content(content: str) -> pd.DataFrame:
    """
    Parse WhatsApp chat content string into a DataFrame.
    
    Time Complexity: O(n) where n is number of lines
    Space Complexity: O(n) for storing messages
    
    Args:
        content: Raw chat file content as string
        
    Returns:
        DataFrame with columns: Date, Time, Author, Message, DateTime
    """
    lines = content.splitlines()
    
    if not lines:
        return pd.DataFrame(columns=['Date', 'Time', 'Author', 'Message', 'DateTime'])
    
    # Auto-detect the best matching pattern
    pattern = detect_best_pattern(lines, MESSAGE_PATTERNS)
    
    data = []
    message_buffer = []
    date, time, author = None, None, None
    
    for line in lines:
        line = line.strip()
        match = re.match(pattern, line)
        if match:
            if author:
                data.append([normalize_date(date), time, author, ' '.join(message_buffer)])
            date, time, author, message = match.groups()
            message_buffer = [message]
        else:
            if author:
                message_buffer.append(line)
    
    if author:
        data.append([normalize_date(date), time, author, ' '.join(message_buffer)])
    
    df = pd.DataFrame(data, columns=['Date', 'Time', 'Author', 'Message'])
    
    if df.empty:
        return df
    
    # Try multiple datetime parsing strategies
    datetime_col = None
    for dayfirst in [True, False]:  # Try DD/MM first, then MM/DD
        try:
            datetime_col = pd.to_datetime(
                df['Date'] + ' ' + df['Time'],
                dayfirst=dayfirst,
                errors='coerce'
            )
            # If most dates parsed successfully, use this format
            if datetime_col.notna().sum() > len(df) * 0.5:
                break
        except Exception:
            continue
    
    if datetime_col is not None:
        df['DateTime'] = datetime_col
    else:
        df['DateTime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], errors='coerce')
    
    df = df.dropna(subset=['DateTime'])
    return df


def parse_chat_file(file: str | bytes | BinaryIO) -> pd.DataFrame:
    """
    Parse WhatsApp chat file (TXT or ZIP) into a DataFrame.
    
    Time Complexity: O(n) where n is number of lines
    Space Complexity: O(n) for storing messages
    
    Args:
        file: File path (str), file bytes, or file-like object
        
    Returns:
        DataFrame with columns: Date, Time, Author, Message, DateTime
        
    Raises:
        ValueError: If file format is not supported or no content found
    """
    content = None
    
    # Handle file path
    if isinstance(file, str):
        if file.endswith('.zip'):
            with zipfile.ZipFile(file) as z:
                txt_files = [f for f in z.namelist() if f.endswith('.txt')]
                if not txt_files:
                    raise ValueError("No .txt file found in ZIP archive")
                with z.open(txt_files[0]) as f:
                    content = f.read().decode('utf-8')
        else:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
    
    # Handle bytes
    elif isinstance(file, bytes):
        # Check if it's a ZIP file
        if file[:4] == b'PK\x03\x04':
            with zipfile.ZipFile(BytesIO(file)) as z:
                txt_files = [f for f in z.namelist() if f.endswith('.txt')]
                if not txt_files:
                    raise ValueError("No .txt file found in ZIP archive")
                with z.open(txt_files[0]) as f:
                    content = f.read().decode('utf-8')
        else:
            content = file.decode('utf-8')
    
    # Handle file-like object
    else:
        file_content = file.read()
        if isinstance(file_content, bytes):
            # Check if it's a ZIP file
            if file_content[:4] == b'PK\x03\x04':
                with zipfile.ZipFile(BytesIO(file_content)) as z:
                    txt_files = [f for f in z.namelist() if f.endswith('.txt')]
                    if not txt_files:
                        raise ValueError("No .txt file found in ZIP archive")
                    with z.open(txt_files[0]) as f:
                        content = f.read().decode('utf-8')
            else:
                content = file_content.decode('utf-8')
        else:
            content = file_content
    
    if not content:
        raise ValueError("Could not read file content")
    
    return parse_chat_content(content)
