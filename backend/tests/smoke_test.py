from fastapi.testclient import TestClient
from app.main import app
from app.models.schemas import PredictionInput
import json
import os

from app.services.prediction import prediction_service


def run_smoke_test():
    client = TestClient(app)

    # Ensure models are loaded (explicit call for test environments)
    print("Models dir:", prediction_service.models_dir)
    try:
        print("Models present:", os.listdir(prediction_service.models_dir))
    except Exception as e:
        print("Could not list models dir:", e)
    try:
        prediction_service.load_all_models()
    except Exception as e:
        print("load_all_models exception:", e)

    print("\n--- Health Check ---")
    r = client.get("/api/health")
    print("status_code:", r.status_code)
    assert r.status_code == 200
    print(json.dumps(r.json(), indent=2)[:1000])

    print("\n--- Login (operator) ---")
    login_resp = client.post(
        "/api/auth/login",
        data={"username": "operator", "password": "operator123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    print("login status:", login_resp.status_code)
    assert login_resp.status_code == 200
    token = login_resp.json().get("access_token")
    assert token

    headers = {"Authorization": f"Bearer {token}"}

    sample_input = {
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

    print("\n--- POST /api/predict/passenger-flow ---")
    r_pf = client.post("/api/predict/passenger-flow", json=sample_input, headers=headers)
    print("pf status:", r_pf.status_code)
    assert r_pf.status_code == 200
    print(r_pf.json())

    print("\n--- POST /api/predict/queue-length ---")
    r_ql = client.post("/api/predict/queue-length", json=sample_input, headers=headers)
    print("ql status:", r_ql.status_code)
    assert r_ql.status_code == 200
    print(r_ql.json())

    print("\n--- POST /api/predict/waiting-time ---")
    r_wt = client.post("/api/predict/waiting-time", json=sample_input, headers=headers)
    print("wt status:", r_wt.status_code)
    assert r_wt.status_code == 200
    print(r_wt.json())

    print("\nSmoke test completed successfully.")


if __name__ == "__main__":
    run_smoke_test()


def test_smoke():
    """Pytest entrypoint for the smoke test."""
    run_smoke_test()
