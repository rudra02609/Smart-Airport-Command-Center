# API Usage Guide - Smart Airport Command Center

## 🌐 Base URL

```
http://localhost:8000
```

## 📚 Interactive Documentation

FastAPI provides automatic interactive API documentation:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## 🔍 Endpoints

### 1. Health Check

Check if the API is running.

**Endpoint:** `GET /api/health`

**Request:**
```bash
curl http://localhost:8000/api/health
```

**Response:**
```json
{
  "status": "healthy",
  "message": "Smart Airport Command Center API is running",
  "version": "1.0.0"
}
```

---

### 2. Predict Passenger Flow

Predict the number of passengers based on operational parameters.

**Endpoint:** `POST /api/predict/passenger-flow`

**Request:**
```bash
curl -X POST "http://localhost:8000/api/predict/passenger-flow" \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```

**Response:**
```json
{
  "predicted_passenger_flow": 5482.77,
  "input_data": { ... },
  "model": "Random Forest Regressor"
}
```

---

### 3. Predict Queue Length

Predict queue length at security and check-in counters.

**Endpoint:** `POST /api/predict/queue-length`

**Request:**
```bash
curl -X POST "http://localhost:8000/api/predict/queue-length" \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```

**Response:**
```json
{
  "predicted_queue_length": 200.0,
  "input_data": { ... },
  "model": "Random Forest Regressor"
}
```

---

### 4. Predict Waiting Time

Predict passenger waiting time in minutes.

**Endpoint:** `POST /api/predict/waiting-time`

**Request:**
```bash
curl -X POST "http://localhost:8000/api/predict/waiting-time" \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```

**Response:**
```json
{
  "predicted_waiting_time": 29.15,
  "input_data": { ... },
  "model": "Random Forest Regressor"
}
```

---

## 📋 Input Parameters

All prediction endpoints accept the same input parameters:

| Parameter | Type | Required | Description | Valid Values |
|-----------|------|----------|-------------|--------------|
| hour | Integer | Yes | Hour of day | 0-23 |
| day_of_week | Integer | Yes | Day of week | 0-6 (0=Monday) |
| is_weekend | Integer | Yes | Weekend indicator | 0 or 1 |
| is_peak_hour | Integer | Yes | Peak hour indicator | 0 or 1 |
| terminal | String | Yes | Airport terminal | "T1", "T2", "T3" |
| num_flights | Integer | Yes | Number of scheduled flights | >= 1 |
| security_staff | Integer | Yes | Number of security staff | >= 1 |
| checkin_staff | Integer | Yes | Number of check-in staff | >= 1 |
| gates_available | Integer | Yes | Number of available gates | >= 1 |
| is_holiday_season | Integer | Yes | Holiday season indicator | 0 or 1 |
| baggage_volume | Integer | Yes | Expected baggage volume | >= 0 |
| international_ratio | Float | Yes | Ratio of international flights | 0.0-1.0 |
| weather | String | Yes | Weather condition | "Clear", "Rainy", "Foggy" |

---

## 🧪 Testing with Python

### Using Requests Library

```python
import requests
import json

# API base URL
BASE_URL = "http://localhost:8000"

# Input data
data = {
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

# Make prediction
response = requests.post(
    f"{BASE_URL}/api/predict/passenger-flow",
    json=data
)

# Print result
if response.status_code == 200:
    result = response.json()
    print(f"Predicted Passenger Flow: {result['predicted_passenger_flow']}")
else:
    print(f"Error: {response.status_code}")
```

---

## 🎯 Example Scenarios

### Scenario 1: Peak Morning Hour
```json
{
  "hour": 7,
  "day_of_week": 1,
  "is_weekend": 0,
  "is_peak_hour": 1,
  "terminal": "T1",
  "num_flights": 28,
  "security_staff": 35,
  "checkin_staff": 25,
  "gates_available": 18,
  "is_holiday_season": 0,
  "baggage_volume": 4200,
  "international_ratio": 0.7,
  "weather": "Clear"
}
```

**Expected:** High passenger flow (~6,600), longer queues

---

### Scenario 2: Off-Peak Late Night
```json
{
  "hour": 23,
  "day_of_week": 3,
  "is_weekend": 0,
  "is_peak_hour": 0,
  "terminal": "T2",
  "num_flights": 8,
  "security_staff": 12,
  "checkin_staff": 10,
  "gates_available": 10,
  "is_holiday_season": 0,
  "baggage_volume": 800,
  "international_ratio": 0.4,
  "weather": "Clear"
}
```

**Expected:** Low passenger flow (~1,200), shorter queues

---

### Scenario 3: Holiday Weekend with Bad Weather
```json
{
  "hour": 10,
  "day_of_week": 6,
  "is_weekend": 1,
  "is_peak_hour": 0,
  "terminal": "T3",
  "num_flights": 22,
  "security_staff": 28,
  "checkin_staff": 20,
  "gates_available": 14,
  "is_holiday_season": 1,
  "baggage_volume": 3800,
  "international_ratio": 0.65,
  "weather": "Rainy"
}
```

**Expected:** High passenger flow (~5,800), moderate queues, increased waiting time

---

## ⚠️ Error Handling

### Invalid Input (422 Unprocessable Entity)

**Request with invalid hour:**
```json
{
  "hour": 25,  // Invalid: must be 0-23
  "day_of_week": 1,
  ...
}
```

**Response:**
```json
{
  "detail": [
    {
      "type": "less_than_equal",
      "loc": ["body", "hour"],
      "msg": "Input should be less than or equal to 23",
      "input": 25
    }
  ]
}
```

### Server Error (500 Internal Server Error)

If the model fails to load or prediction fails, you'll receive:
```json
{
  "detail": "Prediction failed: [error message]"
}
```

---

## 📊 Response Times

Typical response times:
- Health check: < 10ms
- Predictions: 50-200ms

---

## 🔐 Security Note

**Current Implementation:** Development mode with no authentication.

**Production Recommendations:**
- Add API key authentication
- Implement rate limiting
- Use HTTPS
- Add request logging
- Implement CORS restrictions

---

## 🐛 Troubleshooting

### Issue: Connection Refused
**Solution:** Make sure the FastAPI server is running:
```bash
uvicorn app.main:app --reload
```

### Issue: Module Not Found
**Solution:** Install dependencies:
```bash
pip install -r requirements.txt
```

### Issue: Model Not Found
**Solution:** Train the models first:
```bash
cd backend/scripts
python train_models.py
```

---

## 📞 Support

For issues or questions:
1. Check the [Week 3 ML Report](reports/WEEK3_ML_REPORT.md)
2. Review the interactive docs at `/docs`
3. Check server logs for errors

---

**Last Updated:** Week 3 Completion  
**API Version:** 1.0.0
