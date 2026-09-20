"""
Health Check API - Enhanced with system status information.
"""

from fastapi import APIRouter
from app.services.prediction import prediction_service
import time

router = APIRouter(
    prefix="/api",
    tags=["Health Check"]
)

# Track server start time
_start_time = time.time()


@router.get("/health")
async def health_check():
    """
    Health check endpoint to verify API is running.
    Returns system status including loaded models and uptime.
    """
    uptime_seconds = int(time.time() - _start_time)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    models_loaded = list(prediction_service.models.keys())
    
    return {
        "status": "healthy",
        "message": "Smart Airport Command Center API is running",
        "version": "2.0.0",
        "uptime": f"{hours}h {minutes}m {seconds}s",
        "models_loaded": models_loaded,
        "models_count": len(models_loaded),
        "model_metrics": prediction_service.metrics,
        "features": [
            "passenger_flow_prediction",
            "queue_length_prediction",
            "waiting_time_prediction",
            "smart_alerts",
            "staff_recommendations",
            "congestion_detection",
            "security_risk_score",
            "jwt_authentication",
            "rbac",
            "audit_logging",
            "anomaly_detection",
            "rate_limiting"
        ]
    }
