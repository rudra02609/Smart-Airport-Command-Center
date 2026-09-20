"""
Waiting Time Prediction API - Enhanced with auth, audit, and risk score.
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from app.models.schemas import PredictionInput, WaitingTimeResponse
from app.services.prediction import prediction_service
from app.services.alerts import alert_engine
from app.services.staff_recommendation import recommendation_engine
from app.cybersecurity.auth import get_current_user, require_role
from app.cybersecurity.rbac import UserInDB, Role
from app.cybersecurity.audit import audit_logger

router = APIRouter(
    prefix="/api/predict",
    tags=["Waiting Time Prediction"]
)

@router.post("/waiting-time", response_model=WaitingTimeResponse)
async def predict_waiting_time(
    input_data: PredictionInput,
    request: Request,
    current_user: UserInDB = Depends(require_role(Role.ADMIN, Role.OPERATOR))
):
    """
    Predict waiting time based on airport operational parameters.
    Requires Operator or Admin role.
    
    Returns prediction with Security Risk Score and recommendations.
    """
    try:
        input_dict = input_data.model_dump()
        client_ip = request.client.host if request.client else "unknown"
        
        # Run all predictions for risk score
        pf = prediction_service.predict_passenger_flow(input_dict)
        ql = prediction_service.predict_queue_length(input_dict)
        wt = prediction_service.predict_waiting_time(input_dict)
        
        # Generate alerts and risk score
        alert_result = alert_engine.evaluate(pf, ql, wt)
        recs = recommendation_engine.recommend(pf, ql, wt, input_data.security_staff, input_data.checkin_staff)
        
        # Audit log
        audit_logger.log(
            user=current_user.username,
            action="waiting_time_prediction",
            endpoint="/api/predict/waiting-time",
            status="success",
            ip_address=client_ip,
            details=f"Predicted: {wt:.0f} minutes"
        )
        
        return WaitingTimeResponse(
            predicted_waiting_time=wt,
            input_data=input_dict,
            model="Random Forest Regressor",
            congestion_level=alert_result["congestion_level"],
            security_risk_score=alert_result["security_risk_score"],
            alerts=alert_result["alerts"],
            recommendations=recs
        )
        
    except Exception as e:
        audit_logger.log(
            user=current_user.username if current_user else "unknown",
            action="waiting_time_prediction",
            endpoint="/api/predict/waiting-time",
            status="failed",
            details=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")
