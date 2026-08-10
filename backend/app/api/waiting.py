"""
Waiting Time Prediction API
"""

from fastapi import APIRouter, HTTPException
from app.models.schemas import PredictionInput, WaitingTimeResponse, ErrorResponse
from app.services.prediction import prediction_service

router = APIRouter(
    prefix="/api/predict",
    tags=["Waiting Time Prediction"]
)

@router.post("/waiting-time", response_model=WaitingTimeResponse)
async def predict_waiting_time(input_data: PredictionInput):
    """
    Predict waiting time based on airport operational parameters
    
    **Input Parameters:**
    - hour: Hour of day (0-23)
    - day_of_week: Day of week (0=Monday, 6=Sunday)
    - is_weekend: Is weekend (0=No, 1=Yes)
    - is_peak_hour: Is peak hour (0=No, 1=Yes)
    - terminal: Terminal (T1, T2, or T3)
    - num_flights: Number of scheduled flights
    - security_staff: Number of security staff
    - checkin_staff: Number of check-in staff
    - gates_available: Number of available gates
    - is_holiday_season: Is holiday season (0=No, 1=Yes)
    - baggage_volume: Expected baggage volume
    - international_ratio: Ratio of international flights (0.0-1.0)
    - weather: Weather condition (Clear, Rainy, Foggy)
    
    **Returns:**
    - predicted_waiting_time: Predicted waiting time (minutes)
    """
    try:
        # Convert input to dict
        input_dict = input_data.model_dump()
        
        # Make prediction
        prediction = prediction_service.predict_waiting_time(input_dict)
        
        return WaitingTimeResponse(
            predicted_waiting_time=prediction,
            input_data=input_dict,
            model="Random Forest Regressor"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )
