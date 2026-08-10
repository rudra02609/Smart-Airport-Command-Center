"""
Health Check API
"""

from fastapi import APIRouter

router = APIRouter(
    prefix="/api",
    tags=["Health Check"]
)

@router.get("/health")
async def health_check():
    """
    Health check endpoint to verify API is running
    """
    return {
        "status": "healthy",
        "message": "Smart Airport Command Center API is running",
        "version": "1.0.0"
    }
