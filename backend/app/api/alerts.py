"""
Alert and Full Analysis API endpoints.
Provides combined prediction + alert + recommendation responses.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from app.models.schemas import (
    PredictionInput, FullAnalysisResponse, AlertEvaluationInput
)
from app.services.prediction import prediction_service
from app.services.alerts import alert_engine
from app.services.staff_recommendation import recommendation_engine
from app.cybersecurity.auth import get_current_user, require_role
from app.cybersecurity.rbac import UserInDB, Role
from app.cybersecurity.audit import audit_logger

router = APIRouter(
    prefix="/api/alerts",
    tags=["Smart Alerts & Analysis"]
)


@router.post("/check", response_model=FullAnalysisResponse)
async def full_analysis(
    input_data: PredictionInput,
    request: Request,
    current_user: UserInDB = Depends(require_role(Role.ADMIN, Role.OPERATOR))
):
    """
    Run all 3 predictions and generate combined analysis.
    Returns: predictions + alerts + congestion + risk score + recommendations.
    
    This is the primary endpoint for the airport command center.
    """
    try:
        input_dict = input_data.model_dump()
        
        # Run all 3 predictions
        pf = prediction_service.predict_passenger_flow(input_dict)
        ql = prediction_service.predict_queue_length(input_dict)
        wt = prediction_service.predict_waiting_time(input_dict)
        
        # Generate alerts and risk score
        alert_result = alert_engine.evaluate(pf, ql, wt)
        
        # Generate staff recommendations
        recs = recommendation_engine.recommend(
            pf, ql, wt,
            security_staff=input_data.security_staff,
            checkin_staff=input_data.checkin_staff
        )
        
        # Audit log
        client_ip = request.client.host if request.client else "unknown"
        audit_logger.log(
            user=current_user.username,
            action="full_analysis",
            endpoint="/api/alerts/check",
            status="success",
            ip_address=client_ip,
            details=f"PF={pf:.0f}, QL={ql:.0f}, WT={wt:.0f}, Risk={alert_result['security_risk_score']}"
        )
        
        return FullAnalysisResponse(
            passenger_flow=pf,
            queue_length=ql,
            waiting_time=wt,
            congestion_level=alert_result["congestion_level"],
            congestion_score=alert_result["congestion_score"],
            security_risk_score=alert_result["security_risk_score"],
            overall_severity=alert_result["overall_severity"],
            alerts=alert_result["alerts"],
            recommendations=recs,
            input_data=input_dict,
            model="Random Forest Regressor"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/evaluate")
async def evaluate_alerts(
    input_data: AlertEvaluationInput,
    current_user: UserInDB = Depends(require_role(Role.ADMIN, Role.OPERATOR))
):
    """
    Evaluate alerts from externally provided values (no ML prediction).
    Useful for testing thresholds or manual scenario analysis.
    """
    try:
        # Generate alerts
        alert_result = alert_engine.evaluate(
            input_data.passenger_flow,
            input_data.queue_length,
            input_data.waiting_time
        )
        
        # Generate recommendations
        recs = recommendation_engine.recommend(
            input_data.passenger_flow,
            input_data.queue_length,
            input_data.waiting_time,
            security_staff=input_data.security_staff,
            checkin_staff=input_data.checkin_staff
        )
        
        return {
            "passenger_flow": input_data.passenger_flow,
            "queue_length": input_data.queue_length,
            "waiting_time": input_data.waiting_time,
            "congestion_level": alert_result["congestion_level"],
            "congestion_score": alert_result["congestion_score"],
            "security_risk_score": alert_result["security_risk_score"],
            "overall_severity": alert_result["overall_severity"],
            "alerts": alert_result["alerts"],
            "recommendations": recs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")
