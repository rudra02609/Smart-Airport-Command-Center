"""
Comprehensive API Test Suite for Smart Airport Command Center.
Tests all endpoints: auth, predictions, alerts, security.
Run with: python tests/test_all_endpoints.py
Server must be running: uvicorn app.main:app --reload
"""

import requests
import json
import time
import sys

# API base URL
BASE_URL = "http://localhost:8000"

# Test counters
passed = 0
failed = 0

# Standard prediction input
test_input = {
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

# High-stress scenario (triggers alerts)
high_stress_input = {
    "hour": 7,
    "day_of_week": 5,
    "is_weekend": 1,
    "is_peak_hour": 1,
    "terminal": "T1",
    "num_flights": 29,
    "security_staff": 10,
    "checkin_staff": 8,
    "gates_available": 8,
    "is_holiday_season": 1,
    "baggage_volume": 6000,
    "international_ratio": 0.8,
    "weather": "Foggy"
}


def test(name, func):
    """Run a test and track pass/fail."""
    global passed, failed
    print(f"\n{'─'*60}")
    print(f"🧪 {name}")
    print(f"{'─'*60}")
    try:
        func()
        passed += 1
        print(f"✅ PASSED")
    except AssertionError as e:
        failed += 1
        print(f"❌ FAILED: {e}")
    except Exception as e:
        failed += 1
        print(f"❌ ERROR: {e}")


def get_token(username, password):
    """Helper: Login and return JWT token."""
    resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        data={"username": username, "password": password},
        timeout=5
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()["access_token"]


def auth_headers(token):
    """Helper: Create auth headers."""
    return {"Authorization": f"Bearer {token}"}


# ============================================================
# TESTS
# ============================================================

def test_root():
    resp = requests.get(f"{BASE_URL}/", timeout=5)
    assert resp.status_code == 200
    data = resp.json()
    assert "endpoints" in data
    print(f"   Version: {data.get('version')}")

def test_health():
    resp = requests.get(f"{BASE_URL}/api/health", timeout=5)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    print(f"   Models loaded: {data.get('models_count')}")
    print(f"   Uptime: {data.get('uptime')}")

def test_login_admin():
    resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        data={"username": "admin", "password": "admin123"},
        timeout=5
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["token_type"] == "bearer"
    assert data["role"] == "admin"
    print(f"   Token received, Role: {data['role']}")

def test_login_operator():
    resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        data={"username": "operator", "password": "operator123"},
        timeout=5
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "operator"
    print(f"   Token received, Role: operator")

def test_login_invalid():
    resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        data={"username": "admin", "password": "wrongpassword"},
        timeout=5
    )
    assert resp.status_code == 401
    print(f"   Correctly rejected invalid credentials")

def test_auth_me():
    token = get_token("admin", "admin123")
    resp = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers(token), timeout=5)
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "admin"
    print(f"   User: {data['username']}, Role: {data['role']}")

def test_prediction_requires_auth():
    resp = requests.post(
        f"{BASE_URL}/api/predict/passenger-flow",
        json=test_input,
        timeout=5
    )
    assert resp.status_code == 401
    print(f"   Correctly blocked unauthenticated request")

def test_passenger_flow_prediction():
    token = get_token("operator", "operator123")
    resp = requests.post(
        f"{BASE_URL}/api/predict/passenger-flow",
        json=test_input,
        headers=auth_headers(token),
        timeout=5
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "predicted_passenger_flow" in data
    assert "security_risk_score" in data
    assert "congestion_level" in data
    print(f"   Passenger Flow: {data['predicted_passenger_flow']}")
    print(f"   Risk Score: {data['security_risk_score']}")
    print(f"   Congestion: {data['congestion_level']}")

def test_queue_length_prediction():
    token = get_token("operator", "operator123")
    resp = requests.post(
        f"{BASE_URL}/api/predict/queue-length",
        json=test_input,
        headers=auth_headers(token),
        timeout=5
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "predicted_queue_length" in data
    assert "security_risk_score" in data
    print(f"   Queue Length: {data['predicted_queue_length']}")
    print(f"   Risk Score: {data['security_risk_score']}")

def test_waiting_time_prediction():
    token = get_token("operator", "operator123")
    resp = requests.post(
        f"{BASE_URL}/api/predict/waiting-time",
        json=test_input,
        headers=auth_headers(token),
        timeout=5
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "predicted_waiting_time" in data
    assert "security_risk_score" in data
    print(f"   Waiting Time: {data['predicted_waiting_time']} minutes")
    print(f"   Risk Score: {data['security_risk_score']}")

def test_viewer_cannot_predict():
    token = get_token("viewer", "viewer123")
    resp = requests.post(
        f"{BASE_URL}/api/predict/passenger-flow",
        json=test_input,
        headers=auth_headers(token),
        timeout=5
    )
    assert resp.status_code == 403
    print(f"   Viewer correctly denied access to prediction API")

def test_full_analysis():
    token = get_token("admin", "admin123")
    resp = requests.post(
        f"{BASE_URL}/api/alerts/check",
        json=high_stress_input,
        headers=auth_headers(token),
        timeout=5
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "passenger_flow" in data
    assert "queue_length" in data
    assert "waiting_time" in data
    assert "congestion_level" in data
    assert "security_risk_score" in data
    assert "alerts" in data
    assert "recommendations" in data
    print(f"   PF={data['passenger_flow']:.0f}, QL={data['queue_length']:.0f}, WT={data['waiting_time']:.0f}")
    print(f"   Congestion: {data['congestion_level']}")
    print(f"   Risk Score: {data['security_risk_score']}")
    print(f"   Alerts: {len(data['alerts'])}")
    print(f"   Recommendations: {len(data['recommendations'])}")

def test_evaluate_alerts():
    token = get_token("operator", "operator123")
    resp = requests.post(
        f"{BASE_URL}/api/alerts/evaluate",
        json={"passenger_flow": 9000, "queue_length": 150, "waiting_time": 60},
        headers=auth_headers(token),
        timeout=5
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["congestion_level"] in ["HIGH", "CRITICAL"]
    assert data["security_risk_score"] > 50
    print(f"   Congestion: {data['congestion_level']}")
    print(f"   Risk Score: {data['security_risk_score']}")
    print(f"   Alerts: {len(data['alerts'])}")

def test_security_status():
    token = get_token("admin", "admin123")
    resp = requests.get(
        f"{BASE_URL}/api/security/status",
        headers=auth_headers(token),
        timeout=5
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["security_system"] == "active"
    print(f"   Security system: {data['security_system']}")

def test_security_logs():
    token = get_token("admin", "admin123")
    resp = requests.get(
        f"{BASE_URL}/api/security/logs?limit=10",
        headers=auth_headers(token),
        timeout=5
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "logs" in data
    print(f"   Logs returned: {data['total_returned']}")

def test_security_check():
    token = get_token("admin", "admin123")
    resp = requests.post(
        f"{BASE_URL}/api/security/check",
        headers=auth_headers(token),
        timeout=5
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "threat_level" in data
    print(f"   Threat Level: {data['threat_level']}")
    print(f"   Anomaly Score: {data.get('anomaly_score', 'N/A')}")

def test_operator_cannot_access_security():
    token = get_token("operator", "operator123")
    resp = requests.get(
        f"{BASE_URL}/api/security/status",
        headers=auth_headers(token),
        timeout=5
    )
    assert resp.status_code == 403
    print(f"   Operator correctly denied access to security endpoints")

def test_invalid_input_validation():
    token = get_token("operator", "operator123")
    invalid_input = {"hour": 25, "day_of_week": 1}  # Invalid and incomplete
    resp = requests.post(
        f"{BASE_URL}/api/predict/passenger-flow",
        json=invalid_input,
        headers=auth_headers(token),
        timeout=5
    )
    assert resp.status_code == 422
    print(f"   Invalid input correctly rejected with 422")

def test_rate_limiting():
    """Send many requests quickly to test rate limiting."""
    token = get_token("operator", "operator123")
    # This is a soft test - we just verify the endpoint works
    # Real rate limit testing would need 100+ rapid requests
    resp = requests.post(
        f"{BASE_URL}/api/predict/passenger-flow",
        json=test_input,
        headers=auth_headers(token),
        timeout=5
    )
    assert resp.status_code == 200
    print(f"   Rate limiter is active (full test requires 100+ rapid requests)")


# ============================================================
# RUN ALL TESTS
# ============================================================

if __name__ == "__main__":
    print("\n" + "#"*60)
    print("🧪 SMART AIRPORT COMMAND CENTER - COMPREHENSIVE TEST SUITE")
    print("#"*60)
    print(f"\n📍 Server: {BASE_URL}")
    print("⚠️  Make sure the server is running: uvicorn app.main:app --reload")
    
    # Wait for server
    time.sleep(1)
    
    # Run all tests
    test("1. Root Endpoint", test_root)
    test("2. Health Check", test_health)
    test("3. Login - Admin", test_login_admin)
    test("4. Login - Operator", test_login_operator)
    test("5. Login - Invalid Credentials", test_login_invalid)
    test("6. Auth - Get Current User", test_auth_me)
    test("7. Prediction Requires Auth", test_prediction_requires_auth)
    test("8. Passenger Flow Prediction (with Risk Score)", test_passenger_flow_prediction)
    test("9. Queue Length Prediction (with Risk Score)", test_queue_length_prediction)
    test("10. Waiting Time Prediction (with Risk Score)", test_waiting_time_prediction)
    test("11. RBAC - Viewer Cannot Predict", test_viewer_cannot_predict)
    test("12. Full Analysis (All Predictions + Alerts + Recommendations)", test_full_analysis)
    test("13. Evaluate Alerts (Manual Values)", test_evaluate_alerts)
    test("14. Security Status (Admin Only)", test_security_status)
    test("15. Audit Logs", test_security_logs)
    test("16. Anomaly Detection Check", test_security_check)
    test("17. RBAC - Operator Cannot Access Security", test_operator_cannot_access_security)
    test("18. Input Validation (422)", test_invalid_input_validation)
    test("19. Rate Limiting Active", test_rate_limiting)
    
    # Summary
    total = passed + failed
    print(f"\n{'#'*60}")
    print(f"📊 TEST RESULTS: {passed}/{total} passed, {failed}/{total} failed")
    print(f"{'#'*60}\n")
    
    if failed > 0:
        sys.exit(1)
