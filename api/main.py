"""
WhatsApp Chat Analyzer API

FastAPI backend for React/Recharts frontend integration.
Provides JSON endpoints for all chat analysis features.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import upload, analysis
from api.schemas import HealthResponse

app = FastAPI(
    title="WhatsApp Chat Analyzer API",
    description="Analyze WhatsApp chat exports with beautiful visualizations",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router)
app.include_router(analysis.router)


@app.get("/", tags=["root"])
async def root():
    """API root - redirects to documentation."""
    return {
        "message": "WhatsApp Chat Analyzer API",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """Health check endpoint for deployment monitoring."""
    return HealthResponse(status="healthy", version="1.0.0")


@app.get("/api/health", response_model=HealthResponse, tags=["health"])
async def api_health_check():
    """API health check endpoint."""
    return HealthResponse(status="healthy", version="1.0.0")


@app.get("/api/stats", tags=["stats"])
async def get_stats():
    """Get global usage statistics."""
    from api.stats import StatsService
    return {"total_vibes_checked": StatsService.get_count()}
