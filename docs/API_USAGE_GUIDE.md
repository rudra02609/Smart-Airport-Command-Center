# API Usage Guide - Smart Airport Command Center

**API Version:** 2.0.0

## 🌐 Base URL

```
http://localhost:8000
```

## 📚 Interactive Documentation

FastAPI provides automatic interactive API documentation:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## 🔐 Authentication

Most endpoints require a JWT obtained from the login endpoint. Pass it as a bearer token:

```
Authorization: Bearer <token>
```

**Login:**

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

**Response:**
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "role": "admin"
}
```

### RBAC Matrix

| Endpoint group | viewer | operator | admin |
| :--- | :---: | :---: | :---: |
| `/api/auth/me` | ✅ | ✅ | ✅ |
| Predictions (`/api/predict/*`) | ❌ (403) | ✅ | ✅ |
| Alerts (`/api/alerts/*`) | ❌ (403) | ✅ | ✅ |
| Security (`/api/security/*`) | ❌ (403) | ❌ (403) | ✅ |

Missing/malformed token → `401`; valid token without permission → `403`.

### Development users
| Role | Username | Password |
| :--- | :--- | :--- |
| admin | admin | admin123 |
| operator | operator | operator123 |
| viewer | viewer | viewer123 |

---

## 🔍 Endpoints

### 1. Health Check

`GET /api/health` (Public)

```bash
curl http://localhost:8000/api/health
```

**Response:**
```json
{
  "status": "healthy",
  "message": "Smart Airport Command Center API is running",
  "version": "2.0.0",
  "uptime": 12.34,
  "timestamp": "2026-01-01T00:00:00Z",
  "models_loaded": ["passenger_flow", "queue_length", "waiting_time"],
  "models_count": 3,
  "model_metrics": { "...": "train/test R² per model" }
}
```

---

### 2. Predict Passenger Flow `<operator|admin>`

`POST /api/predict/passenger-flow`

**Response:**
```json
{
  "predicted_passenger_flow": 5482.77,
  "input_data": { "...": "echo of input" },
  "model": "Random Forest Regressor",
  "congestion_level": "MODERATE",
  "security_risk_score": 45.2
}
```

---

### 3. Predict Queue Length `<operator|admin>`

`POST /api/predict/queue-length`

**Response:** `predicted_queue_length`, `model`, `congestion_level`, `security_risk_score`, `input_data`.

---

### 4. Predict Waiting Time `<operator|admin>`

`POST /api/predict/waiting-time`

**Response:** `predicted_waiting_time`, `model`, `congestion_level`, `security_risk_score`, `input_data`.

---

### 5. Alerts - Full Analysis `<operator|admin>`

`POST /api/alerts/check` — runs all three predictions plus congestion, alerts, staff recommendations, and risk score.

**Response keys:** `passenger_flow`, `queue_length`, `waiting_time`, `congestion_level`, `congestion_score`, `security_risk_score`, `overall_severity`, `alerts[]`, `recommendations[]`.

### 6. Alerts - Evaluate Manual Metrics `<operator|admin>`

`POST /api/alerts/evaluate` with `{"passenger_flow": 9000, "queue_length": 150, "waiting_time": 60}` → alerts/congestion/risk without running predictions.

### 7. Security - Status `<admin>`

`GET /api/security/status` → security system status, anomaly detector state, tracked IP counts.

### 8. Security - Logs `<admin>`

`GET /api/security/logs?limit=20` → recent audit log entries.

### 9. Security - Anomaly Check `<admin>`

`POST /api/security/check` (body `{"ip_address": "192.0.2.5"}` optional) → `threat_level`, `anomaly_score`, `features`, `model_status`.

---

## 📋 Input Parameters

All prediction endpoints accept the same input:

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

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Login
r = requests.post(f"{BASE_URL}/api/auth/login",
                  data={"username": "operator", "password": "operator123"})
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 2. Predict
data = {
    "hour": 8, "day_of_week": 1, "is_weekend": 0, "is_peak_hour": 1,
    "terminal": "T1", "num_flights": 25, "security_staff": 30,
    "checkin_staff": 20, "gates_available": 15, "is_holiday_season": 0,
    "baggage_volume": 3500, "international_ratio": 0.5, "weather": "Clear",
}
resp = requests.post(f"{BASE_URL}/api/predict/passenger-flow", json=data, headers=headers)
print(resp.json()["predicted_passenger_flow"])
```

---

## ⚠️ Error Handling

- **401** — Missing/invalid/expired token.
- **403** — Valid token but insufficient role.
- **422** — Invalid input (e.g., `hour: 25`, `terminal: "T9"`, negative values).
- **429** — Rate limit exceeded (default 100 requests / 60 s per IP).
- **500** — Prediction failure (e.g., models not loaded).

---

## 🔒 Security Note

**Current Implementation:** JWT authentication with RBAC (viewer/operator/admin), audit logging, anomaly detection, security headers, and in-memory rate limiting. Rate limiting and anomaly state reset on restart — appropriate for development/single-instance deployments; use Redis/PostgreSQL for production.

**Recommended for production:** persistent rate limiting, HTTPS, CORS allow-lists, and real secret management.

---

## 🐛 Troubleshooting

### Issue: Connection Refused
```bash
uvicorn app.main:app --reload
```

### Issue: Module Not Found
```bash
pip install -r requirements.txt
```

### Issue: Model Not Found / 500 on prediction
```bash
cd backend/scripts
python generate_dataset.py
python train_models.py
```

### Issue: Tests fail with `httpx2` RuntimeError
Use the project root `.venv` for tests, not `backend\venv` (pinned Starlette is incompatible).

---

## 📞 Support

1. Check [backend documentation](BACKEND_DOCUMENTATION.md)
2. Review the interactive docs at `/docs`
3. Check server logs for errors

---

**Last Updated:** Backend completion phase
**API Version:** 2.0.0