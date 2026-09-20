# Smart Airport Command Center - Backend Documentation

**Version:** 2.0.0

## 1. Project Overview
The Smart Airport Command Center is an AI-powered operational dashboard designed to optimize airport operations, manage passenger flow, and enhance security. The backend provides machine learning predictions, smart alerts, congestion detection, role-based access control, audit logging, anomaly detection, rate limiting, and a comprehensive RESTful API to serve the frontend dashboard.

## 2. Architecture
The backend is built with FastAPI and follows a modular, layered architecture:

```text
backend/
├── app/
│   ├── api/            # API routers (health, auth, predict, alerts, security)
│   ├── core/           # Configuration (config.py), security utilities (security.py)
│   ├── cybersecurity/  # RBAC, auth flows, middleware, anomaly detection, audit
│   ├── models/         # Pydantic schemas for requests/responses
│   ├── services/       # Business logic: preprocessing, prediction, alerts, staff recommendations
│   └── main.py         # FastAPI application entry point (lifespan loads models)
├── scripts/            # Dataset generation and training scripts
├── tests/              # pytest test suites
├── datasets/           # Raw and processed data
├── logs/               # Audit log output (audit.log)
└── models/             # Trained ML models and preprocessors (.pkl) + metrics (.json)
```

Application settings are read from `backend/.env` (see `backend/.env.example`). Unknown/missing values fall back to development defaults, and a startup warning is printed if the default `SECRET_KEY` is in use.

## 3. ML Models
The system uses Random Forest Regressors (primary) and Linear Regression (comparison) for 3 key targets:
- **Passenger Flow**: Predicts number of passengers in the terminal.
- **Queue Length**: Predicts number of passengers waiting at security.
- **Waiting Time**: Predicts average waiting time in minutes.

**Features (19):** hour, day_of_week, is_weekend, is_peak_hour, num_flights, security_staff, checkin_staff, gates_available, is_holiday_season, baggage_volume, international_ratio, terminal (T1/T2/T3), weather (Clear/Rainy/Foggy), and derived fields produced by `DataPreprocessor` / `preprocess_single_input` in `app/services/preprocessing.py`. The canonical feature list is the `FEATURE_COLUMNS` constant shared by prediction and training code.

**Pipeline:** `scripts/generate_dataset.py` produces the synthetic dataset; `scripts/train_models.py` trains and saves `*.pkl` via joblib plus `models/model_metrics.json`. On startup, `app/main.py`'s lifespan loads all models into `prediction_service` and reports `models_loaded`/`models_count` via the health endpoint.

**Metrics** on the current Random Forest models (from `models/model_metrics.json`):

| Target | R² (Random Forest) | Method |
| :--- | :--- | :--- |
| passenger_flow | ~0.973 | Random Forest |
| queue_length | ~0.626 | Random Forest |
| waiting_time | ~0.670 | Random Forest |

## 4. API Reference

### Health & Root
- `GET /` — Service info and endpoint map (no credentials exposed).
- `GET /api/health` — Status, version, uptime, `models_loaded`, `models_count`, and `model_metrics`. (Public)

### Auth Endpoints
- `POST /api/auth/login`: Form login (`username`/`password`) → JWT. (Public). Success and failure are audited; failed attempts feed the anomaly detector.
- `GET /api/auth/me`: Current user info. (Requires Auth)

### Prediction Endpoints (Requires 'operator' or 'admin' role)
- `POST /api/predict/passenger-flow`
- `POST /api/predict/queue-length`
- `POST /api/predict/waiting-time`

Each returns the predicted value, `model`, `congestion_level`, `security_risk_score`, and the echoed `input_data`.

### Alerts Endpoints (Requires 'operator' or 'admin' role)
- `POST /api/alerts/check`: Full analysis (predictions, congestion, alerts, recommendations, risk score).
- `POST /api/alerts/evaluate`: Evaluate manual metrics for alerts.

### Security Endpoints (Requires 'admin' role)
- `GET /api/security/status`: Security system status.
- `GET /api/security/logs?limit=N`: Retrieve audit logs.
- `POST /api/security/check` (optional `ip_address` body): Run anomaly detection check.

*Example Request (`POST /api/predict/passenger-flow`):*
```bash
curl -X POST "http://localhost:8000/api/predict/passenger-flow" \
     -H "Authorization: Bearer <TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{
           "hour": 8, "day_of_week": 1, "is_weekend": 0, "is_peak_hour": 1,
           "terminal": "T1", "num_flights": 25, "security_staff": 30,
           "checkin_staff": 20, "gates_available": 15, "is_holiday_season": 0,
           "baggage_volume": 3500, "international_ratio": 0.6, "weather": "Clear"
         }'
```

Input validation: `hour` 0-23, `terminal` in {T1,T2,T3}, `weather` in {Clear,Rainy,Foggy}, non-negative counts, `international_ratio` 0.0-1.0. Invalid input returns `422`.

## 5. Cybersecurity Layer (`backend/app/cybersecurity/`)
- **auth.py**: Login, JWT creation/validation, `get_current_user`, `require_role`. Audits `login` (success/failure), `authentication_failed`, and `authorization_failed` events. Failed logins are recorded into the anomaly detector.
- **rbac.py**: Roles `admin`, `operator`, `viewer` with a permission hierarchy; in-memory `users_db` for development.
- **middleware.py**: `SecurityHeadersMiddleware` (adds `X-Content-Type-Options`, `X-Frame-Options`, etc.) and `RateLimitMiddleware` (in-memory sliding window, default 100 requests / 60 s per IP → `429`). The rate limiter records every request into the anomaly detector before throttling, making it the single source of request observation.
- **anomaly_detection.py**: Rule-based scoring + optional Isolation Forest model. Features per IP: request rate, unique endpoints, failed logins, and 30-second burst score. Threat levels: `normal` (< 35), `suspicious` (35-69), `critical` (>= 70).
- **audit.py**: `audit_logger` writes JSON-lines to `backend/logs/audit.log` with fields `timestamp`, `user`, `action`, `endpoint`, `status`, `ip_address`, `details`.

### RBAC Permission Matrix
| Capability | viewer | operator | admin |
| :--- | :---: | :---: | :---: |
| Login / /api/auth/me | ✅ | ✅ | ✅ |
| Predictions & alerts | ❌ | ✅ | ✅ |
| Security status/logs/check | ❌ | ❌ | ✅ |

## 6. Security Risk Score
Calculated as a weighted combination of operational metrics and predictions (waiting time, queue length, staff shortage, baggage volume, congestion). Returns 0-100. Higher is riskier; alerts and congestion levels depend on it.

## 7. Smart Alerts & Congestion
Alert thresholds are configurable via `.env` (see `backend/.env.example`). Defaults in `app/core/config.py`:

| Metric | HIGH threshold | MEDIUM threshold |
| :--- | :--- | :--- |
| Queue length (pax) | 100 | 50 |
| Waiting time (min) | 45 | 25 |
| Passenger flow | 8000 | 5000 |

- Congestion level: MINIMAL / LOW / MODERATE / HIGH / CRITICAL (composite of predictions vs thresholds).
- Security risk: Safe (< 40) / Elevated (40-70) / High (> 70).
- Alerts carry `category` (congestion, capacity, staffing, security, weather), `severity`, and `message`.

## 8. Staff Recommendations
Rules generate actionable advice from predictions, e.g.:
- If `queue_length` > 150 → "Deploy 3 additional security staff."
- If `passenger_flow` > 8000 → "Open 2 additional check-in counters."
- If `baggage_volume` > 5000 → "Assign extra baggage handlers."
Each recommendation includes `priority` and `reason`.

## 9. RAG / LLM Assistant — Not Implemented
`backend/app/services/rag_service.py` and `backend/app/api/rag.py` are intentional placeholders that document this status. The `rag/` directory contains empty scaffolding only. A future implementation requires a vector store, an embedding model, and an LLM provider. The RAG router is NOT registered in `app/main.py`.

## 10. How to Run
1. Create virtual environment: `python -m venv .venv`
2. Activate: `.venv\Scripts\activate` (Windows)
3. Install dependencies: `pip install -r requirements.txt`
4. Create config: `copy .env.example .env` and set a strong `SECRET_KEY`.
5. Run server: `uvicorn app.main:app --reload`
   Server runs at `http://localhost:8000`.

## 11. How to Test
- **Swagger UI**: Go to `http://localhost:8000/docs`.
- **pytest suite** (from the `backend` directory):
  ```bash
  python -m pytest tests/test_backend.py -v
  ```
  Uses the project root `.venv` (the `backend\venv` Starlette pin is incompatible with `fastapi.testclient`'s httpx2 requirement).
- **Exploratory scripts** `tests/test_all_endpoints*.py` require a live server.

## 12. Default Credentials (Development Only)
| Username | Password | Role |
| :--- | :--- | :--- |
| admin | admin123 | admin |
| operator | operator123 | operator |
| viewer | viewer123 | viewer |

## 13. Known Limitations
- Models trained on synthetic data; metrics are not real-world accuracy claims.
- Queue-length/waiting-time predictions saturate near dataset bounds → frequent HIGH alerts for extreme inputs.
- Rate limiting and anomaly detection are in-memory and reset on restart (fine for single instance).
- Audit log and users are file/in-memory; PostgreSQL is planned.

## 14. Phase 2 Roadmap
- Real-time IoT data integration (simulated streaming).
- React/Next.js Frontend dashboard integration.
- Database integration (PostgreSQL) for persistent users, logs, and metrics.
- RAG/LLM assistant; advanced threat intelligence with deep learning.