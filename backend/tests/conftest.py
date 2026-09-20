"""
Shared pytest fixtures for the backend test suite.
Makes sure the backend root is importable regardless of how pytest is invoked
(plain `pytest` or `python -m pytest`).
"""

import os
import sys

# Backend root = parent of the tests/ directory
BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.prediction import prediction_service


@pytest.fixture(scope="session")
def client():
    """TestClient with application lifespan active (models loaded on startup)."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def tokens(client):
    """JWT tokens for the three default roles."""
    result = {}
    for role, pwd in [("admin", "admin123"), ("operator", "operator123"), ("viewer", "viewer123")]:
        resp = client.post(
            "/api/auth/login",
            data={"username": role, "password": pwd},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 200, f"Login failed for {role}: {resp.text}"
        result[role] = resp.json()["access_token"]
    return result


@pytest.fixture(scope="session")
def auth_headers(tokens):
    """Authorization headers per role."""
    return {role: {"Authorization": f"Bearer {tok}"} for role, tok in tokens.items()}


@pytest.fixture(scope="session")
def sample_input():
    """Standard valid prediction input."""
    return {
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
        "weather": "Clear",
    }


@pytest.fixture(scope="session")
def high_stress_input():
    """Input designed to exceed multiple thresholds and generate alerts."""
    return {
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
        "weather": "Foggy",
    }