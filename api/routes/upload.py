"""
WhatsApp Chat Upload Endpoint

Handles file upload and creates analysis session.
"""

import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from src.parser import parse_chat_content
from src.analyzers import ChatAnalyzer
from api.schemas import UploadResponse, ErrorResponse

router = APIRouter(prefix="/api", tags=["upload"])

# In-memory session storage (use Redis in production)
sessions: dict[str, ChatAnalyzer] = {}


@router.post(
    "/upload",
    response_model=UploadResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def upload_chat_file(file: UploadFile = File(...)):
    """
    Upload a WhatsApp chat export file (.txt or .zip).
    
    Returns a session_id to use for subsequent analysis endpoints.
    
    Time Complexity: O(n) where n is number of lines
    Space Complexity: O(n) for storing parsed data
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    if not (file.filename.endswith('.txt') or file.filename.endswith('.zip')):
        raise HTTPException(
            status_code=400, 
            detail="Invalid file type. Only .txt and .zip files are supported."
        )
    
    try:
        content = await file.read()
        
        # Handle ZIP files
        if file.filename.endswith('.zip'):
            import zipfile
            from io import BytesIO
            
            with zipfile.ZipFile(BytesIO(content)) as z:
                txt_files = [f for f in z.namelist() if f.endswith('.txt')]
                if not txt_files:
                    raise HTTPException(status_code=400, detail="No .txt file found in ZIP")
                
                with z.open(txt_files[0]) as f:
                    text_content = f.read().decode('utf-8')
        else:
            text_content = content.decode('utf-8')
        
        # Parse the chat
        df = parse_chat_content(text_content)
        
        if df.empty:
            raise HTTPException(
                status_code=400, 
                detail="Could not parse any messages. Check the file format."
            )
        
        # Create session
        session_id = str(uuid.uuid4())
        analyzer = ChatAnalyzer(df)
        sessions[session_id] = analyzer
        
        # Clean up old sessions (keep max 100) - simple LRU
        if len(sessions) > 100:
            oldest_key = next(iter(sessions))
            del sessions[oldest_key]
        
        return UploadResponse(
            success=True,
            message="File uploaded and parsed successfully",
            session_id=session_id,
            total_messages=len(df),
            participants=df['Author'].nunique(),
            date_range={
                "start": df['DateTime'].min().isoformat(),
                "end": df['DateTime'].max().isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


def get_analyzer(session_id: str) -> ChatAnalyzer:
    """
    Get analyzer for a session.
    
    Args:
        session_id: Session ID from upload
        
    Returns:
        ChatAnalyzer instance
        
    Raises:
        HTTPException: If session not found
    """
    if session_id not in sessions:
        raise HTTPException(
            status_code=404, 
            detail="Session not found. Please upload a file first."
        )
    return sessions[session_id]
