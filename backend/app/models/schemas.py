"""
Pydantic models for request/response validation
"""

from pydantic import BaseModel, Field
from typing import Literal

class PredictionInput(BaseModel):
    """Input schema for all prediction endpoints"""
    hour: int = Field(..., ge=0, le=23, description="Hour of day (0-23)")
    day_of_week: int = Field(..., ge=0, le=6, description="Day of week (0=Monday, 6=Sunday)")
    is_weekend: int = Field(..., ge=0, le=1, description="Is weekend (0=No, 1=Yes)")
    is_peak_hour: int = Field(..., ge=0, le=1, description="Is peak hour (0=No, 1=Yes)")
    terminal: Literal["T1", "T2", "T3"] = Field(..., description="Terminal (T1, T2, or T3)")
    num_flights: int = Field(..., ge=1, description="Number of scheduled flights")
    security_staff: int = Field(..., ge=1, description="Number of security staff")
    checkin_staff: int = Field(..., ge=1, description="Number of check-in staff")
    gates_available: int = Field(..., ge=1, description="Number of available gates")
    is_holiday_season: int = Field(..., ge=0, le=1, description="Is holiday season (0=No, 1=Yes)")
    baggage_volume: int = Field(..., ge=0, description="Expected baggage volume")
    international_ratio: float = Field(..., ge=0.0, le=1.0, description="Ratio of international flights")
    weather: Literal["Clear", "Rainy", "Foggy"] = Field(..., description="Weather condition")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "hour": 8,
                "day_of_week": 1,
                "is_weekend": 0,
                "is_peak_hour": 1,
                "terminal": "T1",
                "num_flights": 25,
                "security_staff": 30,
                "checkin_staff": 20,
                "gates_available": 15,
                "is_holiday_season": 0,
                "baggage_volume": 3500,
                "international_ratio": 0.6,
                "weather": "Clear"
            }
        }
    }

class PassengerFlowResponse(BaseModel):
    """Response schema for passenger flow prediction"""
    predicted_passenger_flow: float = Field(..., description="Predicted number of passengers")
    input_data: dict = Field(..., description="Input data used for prediction")
    model: str = Field(default="Random Forest Regressor", description="Model used")
    
class QueueLengthResponse(BaseModel):
    """Response schema for queue length prediction"""
    predicted_queue_length: float = Field(..., description="Predicted queue length (number of people)")
    input_data: dict = Field(..., description="Input data used for prediction")
    model: str = Field(default="Random Forest Regressor", description="Model used")

class WaitingTimeResponse(BaseModel):
    """Response schema for waiting time prediction"""
    predicted_waiting_time: float = Field(..., description="Predicted waiting time (minutes)")
    input_data: dict = Field(..., description="Input data used for prediction")
    model: str = Field(default="Random Forest Regressor", description="Model used")

class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str = Field(..., description="Error message")
    detail: str = Field(None, description="Detailed error information")
