"""
Security API endpoints.
Provides system security status, audit logs, and anomaly detection.
"""

from fastapi import APIRouter, Depends, Request
from typing import Optional
from app.models.schemas import AnomalyCheckInput
from app.cybersecurity.auth import get_current_user, require_role
from app.cybersecurity.rbac import UserInDB, Role
from app.cybersecurity.audit import audit_logger
from app.cybersecurity.anomaly_detection import anomaly_detector

router = APIRouter(
    prefix="/api/security",
    tags=["Security"]
)


@router.get("/status")
async def security_status(
    current_user: UserInDB = Depends(require_role(Role.ADMIN))
):
    """
    Get overall security system status.
    Admin only.
    """
    detector_status = anomaly_detector.get_status()
    audit_stats = audit_logger.get_stats()
    
    return {
        "security_system": "active",
        "anomaly_detector": detector_status,
        "audit_log": {
            "total_events": audit_stats["total_events"],
            "events_by_action": audit_stats["by_action"],
            "events_by_status": audit_stats["by_status"],
            "recent_failures_count": len(audit_stats["recent_failures"])
        },
        "message": "Security systems operational"
    }


@router.get("/logs")
async def get_audit_logs(
    limit: int = 50,
    user: Optional[str] = None,
    action: Optional[str] = None,
    current_user: UserInDB = Depends(require_role(Role.ADMIN))
):
    """
    Retrieve audit logs with optional filtering.
    Admin only.
    
    Query Parameters:
    - limit: Maximum number of logs (default: 50)
    - user: Filter by username
    - action: Filter by action type
    """
    logs = audit_logger.get_logs(limit=limit, user=user, action=action)
    
    return {
        "total_returned": len(logs),
        "filters": {"user": user, "action": action, "limit": limit},
        "logs": logs
    }


@router.post("/check")
async def check_anomaly(
    request: Request,
    input_data: Optional[AnomalyCheckInput] = None,
    current_user: UserInDB = Depends(require_role(Role.ADMIN))
):
    """
    Run anomaly detection check.
    If no IP is specified, checks the requester's IP.
    Admin only.
    """
    # Determine which IP to check
    if input_data and input_data.ip_address:
        target_ip = input_data.ip_address
    else:
        target_ip = request.client.host if request.client else "unknown"
    
    # Run anomaly check
    result = anomaly_detector.check_anomaly(target_ip)
    
    # Log the security check
    audit_logger.log(
        user=current_user.username,
        action="anomaly_check",
        endpoint="/api/security/check",
        status="success",
        ip_address=request.client.host if request.client else "unknown",
        details=f"Checked IP: {target_ip}, Threat: {result['threat_level']}"
    )
    
    return result
