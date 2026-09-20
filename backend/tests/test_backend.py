"""
Comprehensive pytest suite for the Smart Airport Command Center backend.

Covers: startup, health, ML predictions, input validation, authentication,
JWT, RBAC, rate limiting, audit logging, anomaly detection, smart alerts,
congestion detection, staff recommendations, security endpoints, error
handling, and end-to-end integration.

Run from the backend directory:
    python -m pytest tests/test_backend.py -v
"""

from datetime import timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.cybersecurity.anomaly_detection import AnomalyDetector
from app.cybersecurity.middleware import RateLimitMiddleware
from app.cybersecurity.rbac import Role
from app.cybersecurity.audit import audit_logger


# ============================================================
# 1. Application startup
# ============================================================

def _collect_route_paths(routes):
    """Recursively collect route paths (handles Starlette router nesting)."""
    paths = set()
    seen = set()
    def walk(items):
        for r in items:
            rid = id(r)
            if rid in seen:
                continue
            seen.add(rid)
            p = getattr(r, "path", None)
            if p is not None:
                paths.add(p)
            original = getattr(r, "original_router", None)
            if original is not None:
                walk(getattr(original, "routes", []) or [])
            sub = getattr(r, "routes", None)
            if isinstance(sub, list) and sub:
                walk(sub)
    walk(routes)
    return paths


def test_app_startup_and_routes(client):
    """The app imports, the lifespan runs, and routers are registered."""
    routes = _collect_route_paths(client.app.routes)
    for path in [
        "/", "/api/health", "/api/auth/login", "/api/auth/me",
        "/api/predict/passenger-flow", "/api/predict/queue-length",
        "/api/predict/waiting-time", "/api/alerts/check",
        "/api/alerts/evaluate", "/api/security/status",
        "/api/security/logs", "/api/security/check",
    ]:
        assert path in routes, f"Route {path} not registered"


def test_root_endpoint(client):
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert "endpoints" in data
    assert "version" in data
    # Default passwords must not be exposed by the API itself.
    assert "default_credentials" not in data


# ============================================================
# 2. Health endpoint
# ============================================================

def test_health_endpoint(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "uptime" in data


# ============================================================
# 3. ML model loading
# ============================================================

def test_ml_models_loaded(client):
    resp = client.get("/api/health")
    data = resp.json()
    assert data["models_count"] == 3
    for model in ["passenger_flow", "queue_length", "waiting_time"]:
        assert model in data["models_loaded"]


def test_model_metrics_reported(client):
    resp = client.get("/api/health")
    data = resp.json()
    metrics = data.get("model_metrics", {})
    for model in ["passenger_flow", "queue_length", "waiting_time"]:
        assert model in metrics
        assert "random_forest" in metrics[model]
        assert "r2" in metrics[model]["random_forest"]


# ============================================================
# 4-6. Prediction endpoints
# ============================================================

@pytest.mark.parametrize(
    "endpoint,key",
    [
        ("/api/predict/passenger-flow", "predicted_passenger_flow"),
        ("/api/predict/queue-length", "predicted_queue_length"),
        ("/api/predict/waiting-time", "predicted_waiting_time"),
    ],
)
def test_predictions_return_positive_numbers(client, auth_headers, sample_input, endpoint, key):
    resp = client.post(endpoint, json=sample_input, headers=auth_headers["operator"])
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data[key] > 0
    assert data["model"] == "Random Forest Regressor"
    assert "congestion_level" in data
    assert "security_risk_score" in data
    assert 0 <= data["security_risk_score"] <= 100


def test_full_analysis_endpoint(client, auth_headers, high_stress_input):
    resp = client.post("/api/alerts/check", json=high_stress_input, headers=auth_headers["admin"])
    assert resp.status_code == 200, resp.text
    data = resp.json()
    for key in ["passenger_flow", "queue_length", "waiting_time",
                "congestion_level", "congestion_score", "security_risk_score",
                "overall_severity", "alerts", "recommendations"]:
        assert key in data, f"Missing key: {key}"
    assert data["passenger_flow"] > 0
    assert data["queue_length"] >= 0
    assert data["waiting_time"] >= 0


def test_evaluate_alerts_manual_input(client, auth_headers):
    resp = client.post(
        "/api/alerts/evaluate",
        json={"passenger_flow": 9000, "queue_length": 150, "waiting_time": 60},
        headers=auth_headers["operator"],
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["congestion_level"] in ("HIGH", "CRITICAL")
    assert data["security_risk_score"] > 50
    assert len(data["alerts"]) >= 1


# ============================================================
# 7. Input validation
# ============================================================

def test_invalid_hour_rejected(client, auth_headers):
    bad = {
        "hour": 25, "day_of_week": 1, "is_weekend": 0, "is_peak_hour": 0,
        "terminal": "T1", "num_flights": 10, "security_staff": 10,
        "checkin_staff": 10, "gates_available": 10, "is_holiday_season": 0,
        "baggage_volume": 1000, "international_ratio": 0.5, "weather": "Clear",
    }
    resp = client.post("/api/predict/passenger-flow", json=bad, headers=auth_headers["operator"])
    assert resp.status_code == 422


def test_missing_fields_rejected(client, auth_headers):
    resp = client.post(
        "/api/predict/passenger-flow",
        json={"hour": 8, "day_of_week": 1},
        headers=auth_headers["operator"],
    )
    assert resp.status_code == 422


def test_invalid_terminal_rejected(client, auth_headers, sample_input):
    bad = {**sample_input, "terminal": "T9"}
    resp = client.post("/api/predict/passenger-flow", json=bad, headers=auth_headers["operator"])
    assert resp.status_code == 422


def test_invalid_weather_rejected(client, auth_headers, sample_input):
    bad = {**sample_input, "weather": "Sunny"}
    resp = client.post("/api/predict/passenger-flow", json=bad, headers=auth_headers["operator"])
    assert resp.status_code == 422


# ============================================================
# 8-10. Authentication & JWT
# ============================================================

@pytest.mark.parametrize(
    "username,password,expected_role",
    [
        ("admin", "admin123", "admin"),
        ("operator", "operator123", "operator"),
        ("viewer", "viewer123", "viewer"),
    ],
)
def test_login_success(client, username, password, expected_role):
    resp = client.post(
        "/api/auth/login",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["token_type"] == "bearer"
    assert data["role"] == expected_role
    assert data["access_token"]


def test_login_invalid_password(client):
    resp = client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "wrong"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 401


def test_login_unknown_user(client):
    resp = client.post(
        "/api/auth/login",
        data={"username": "ghost", "password": "admin123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 401


def test_auth_me_valid_token(client, tokens):
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tokens['admin']}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "admin"
    assert data["role"] == "admin"


def test_auth_me_invalid_token(client):
    resp = client.get("/api/auth/me", headers={"Authorization": "Bearer not.a.real.token"})
    assert resp.status_code == 401


def test_auth_me_no_token(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_expired_token_rejected(client):
    expired = create_access_token({"sub": "admin", "role": "admin"},
                                  expires_delta=timedelta(minutes=-1))
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert resp.status_code == 401


# ============================================================
# 11. RBAC permissions
# ============================================================

def test_prediction_requires_auth(client, sample_input):
    resp = client.post("/api/predict/passenger-flow", json=sample_input)
    assert resp.status_code == 401


def test_viewer_cannot_predict(client, auth_headers, sample_input):
    resp = client.post(
        "/api/predict/passenger-flow", json=sample_input, headers=auth_headers["viewer"]
    )
    assert resp.status_code == 403


def test_operator_cannot_access_security(client, auth_headers):
    resp = client.get("/api/security/status", headers=auth_headers["operator"])
    assert resp.status_code == 403
    resp = client.get("/api/security/logs", headers=auth_headers["operator"])
    assert resp.status_code == 403


def test_viewer_cannot_access_security(client, auth_headers):
    resp = client.get("/api/security/status", headers=auth_headers["viewer"])
    assert resp.status_code == 403


def test_operator_can_access_predictions_and_alerts(client, auth_headers, sample_input):
    resp = client.post(
        "/api/predict/passenger-flow", json=sample_input, headers=auth_headers["operator"]
    )
    assert resp.status_code == 200
    resp = client.post("/api/alerts/check", json=sample_input, headers=auth_headers["operator"])
    assert resp.status_code == 200


# ============================================================
# 12. Rate limiting
# ============================================================

def test_rate_limiter_enforces_limit():
    """Unit test the in-memory rate limiter with a low limit."""
    app = FastAPI()

    @app.get("/ping")
    async def ping():
        return {"ok": True}

    app.add_middleware(RateLimitMiddleware, max_requests=3, window_seconds=60)

    with TestClient(app) as client:
        for _ in range(3):
            resp = client.get("/ping")
            assert resp.status_code == 200
        resp = client.get("/ping")
        assert resp.status_code == 429


def test_rate_limiter_allows_normal_usage(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200


# ============================================================
# 13. Audit logging
# ============================================================

def test_audit_log_records_events(client, auth_headers, sample_input):
    before = len(audit_logger.get_logs(limit=10000))
    client.post("/api/predict/passenger-flow", json=sample_input, headers=auth_headers["operator"])
    client.get("/api/security/logs", headers=auth_headers["admin"])
    logs = audit_logger.get_logs(limit=10000)
    assert len(logs) > before


def test_audit_log_entries_have_expected_fields(client):
    logs = audit_logger.get_logs(limit=5)
    assert logs
    for entry in logs:
        for field in ["timestamp", "user", "action", "endpoint", "status", "ip_address"]:
            assert field in entry, f"Missing audit field: {field}"


def test_audit_log_records_failed_login(client):
    client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "badpass"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    logs = audit_logger.get_logs(action="login")
    failed = [l for l in logs if l["status"] == "failed"]
    assert failed, "Failed login should be audited"
    assert failed[-1]["user"] == "admin"


def test_audit_log_records_authorization_failures(client, auth_headers, sample_input):
    client.post("/api/predict/passenger-flow", json=sample_input, headers=auth_headers["viewer"])
    logs = audit_logger.get_logs(action="authorization_failed")
    assert logs, "Denied authorization should be audited"


# ============================================================
# 14. Anomaly detection
# ============================================================

def _burst(detector, ip, n):
    for _ in range(n):
        detector.record_request(ip, "/api/predict/passenger-flow")


def test_anomaly_normal_pattern():
    detector = AnomalyDetector()
    _burst(detector, "1.2.3.4", 3)
    result = detector.check_anomaly("1.2.3.4")
    assert result["threat_level"] == "normal"
    assert result["anomaly_score"] <= 10
    assert result["model_status"] in ("collecting_data", "trained")


def test_anomaly_failed_login_burst():
    detector = AnomalyDetector()
    for _ in range(8):
        detector.record_failed_login("5.6.7.8")
    detector.record_request("5.6.7.8", "/api/auth/login")
    result = detector.check_anomaly("5.6.7.8")
    assert result["anomaly_score"] >= 35
    assert result["threat_level"] in ("suspicious", "critical")
    assert result["features"]["failed_logins"] >= 8


def test_anomaly_high_request_burst():
    detector = AnomalyDetector()
    _burst(detector, "9.9.9.9", 60)
    result = detector.check_anomaly("9.9.9.9")
    assert result["features"]["burst_score"] >= 8
    assert result["threat_level"] in ("suspicious", "critical")


def test_anomaly_unknown_ip_is_normal():
    detector = AnomalyDetector()
    result = detector.check_anomaly("10.99.99.99")
    assert result["threat_level"] == "normal"
    assert result["ip"] == "10.99.99.99"


def test_anomaly_global_status():
    detector = AnomalyDetector()
    _burst(detector, "1.1.1.1", 5)
    status = detector.get_status()
    assert status["anomaly_detector"] == "active"
    assert status["tracked_ips"] >= 1


# ============================================================
# 15-17. Smart alerts, congestion, staff recommendations
# ============================================================

def test_smart_alert_thresholds(client, auth_headers):
    resp = client.post(
        "/api/alerts/evaluate",
        json={"passenger_flow": 9000, "queue_length": 150, "waiting_time": 60},
        headers=auth_headers["operator"],
    )
    assert resp.status_code == 200
    data = resp.json()
    assert any(a["category"] == "congestion" for a in data["alerts"])
    assert any(a["category"] == "capacity" for a in data["alerts"])
    assert all("message" in a and "severity" in a for a in data["alerts"])


def test_normal_conditions_no_high_alerts(client, auth_headers):
    resp = client.post(
        "/api/alerts/evaluate",
        json={"passenger_flow": 1500, "queue_length": 20, "waiting_time": 10},
        headers=auth_headers["operator"],
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["overall_severity"] in ("info", "low", "medium")
    assert data["congestion_level"] in ("MINIMAL", "LOW", "MODERATE")


def test_congestion_detection_high(client, auth_headers):
    resp = client.post(
        "/api/alerts/evaluate",
        json={"passenger_flow": 9200, "queue_length": 190, "waiting_time": 80},
        headers=auth_headers["operator"],
    )
    data = resp.json()
    assert data["congestion_level"] == "CRITICAL"
    assert data["congestion_score"] >= 85


def test_staff_recommendations_present(client, auth_headers, high_stress_input):
    resp = client.post("/api/alerts/check", json=high_stress_input, headers=auth_headers["admin"])
    data = resp.json()
    assert data["recommendations"]
    for rec in data["recommendations"]:
        assert "priority" in rec
        assert "recommendation" in rec
        assert "reason" in rec


# ============================================================
# 18. Security endpoints
# ============================================================

def test_security_status_admin(client, auth_headers):
    resp = client.get("/api/security/status", headers=auth_headers["admin"])
    assert resp.status_code == 200
    data = resp.json()
    assert data["security_system"] == "active"
    assert "anomaly_detector" in data
    assert "audit_log" in data


def test_security_logs_admin(client, auth_headers):
    resp = client.get("/api/security/logs?limit=5", headers=auth_headers["admin"])
    assert resp.status_code == 200
    data = resp.json()
    assert "logs" in data
    assert data["total_returned"] >= 0


def test_security_check_admin(client, auth_headers):
    resp = client.post("/api/security/check", headers=auth_headers["admin"])
    assert resp.status_code == 200
    data = resp.json()
    assert "threat_level" in data
    assert "anomaly_score" in data
    assert "features" in data


def test_security_check_with_ip(client, auth_headers):
    resp = client.post(
        "/api/security/check", json={"ip_address": "203.0.113.7"}, headers=auth_headers["admin"]
    )
    assert resp.status_code == 200
    assert resp.json()["ip"] == "203.0.113.7"


# ============================================================
# 19. Error handling
# ============================================================

def test_unknown_endpoint_404(client):
    resp = client.get("/api/does-not-exist")
    assert resp.status_code == 404


def test_alerts_evaluate_negative_rejected(client, auth_headers):
    resp = client.post(
        "/api/alerts/evaluate",
        json={"passenger_flow": -5, "queue_length": 10, "waiting_time": 10},
        headers=auth_headers["operator"],
    )
    assert resp.status_code == 422


# ============================================================
# 20. Integration between major modules
# ============================================================

def test_full_integration_flow(client, auth_headers, high_stress_input):
    """Prediction + alerts + congestion + staff recommendations together."""
    resp = client.post("/api/alerts/check", json=high_stress_input, headers=auth_headers["admin"])
    assert resp.status_code == 200
    data = resp.json()

    pf = data["passenger_flow"]
    ql = data["queue_length"]
    wt = data["waiting_time"]

    # The same metrics used downstream must be sane.
    assert pf > 0 and ql >= 0 and wt >= 0

    # Alerts and category consistency.
    assert data["congestion_score"] >= 0
    assert 0 <= data["security_risk_score"] <= 100

    # Staff recommendations reference the predicted state.
    assert isinstance(data["recommendations"], list)
    assert len(data["alerts"]) >= 1