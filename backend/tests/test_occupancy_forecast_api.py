import sys
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient


BACKEND_DIR = Path(__file__).resolve().parents[1]

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


from app.api.dependencies import get_current_user
from app.api.v1.endpoints import occupancy_forecast
from app.main import app
from app.models.user import UserRole


client = TestClient(app)


FAKE_FORECAST = {
    "forecast_date": "2017-09-01",
    "predicted_occupied_rooms": 219.5,
    "demand_level": "HIGH",
    "operational_recommendation": (
        "High historical demand is expected. "
        "Review housekeeping coverage, front-desk staffing, "
        "and room readiness before the forecast date."
    ),
    "model": "GradientBoostingRegressor",
    "forecast_horizon": "one_day_ahead",
    "historical_data_end": "2017-08-31",
    "target_definition": (
        "Daily occupied-room demand proxy based on "
        "non-cancelled City Hotel stays."
    ),
    "validation_mean_mae": 11.8386,
    "baseline_mean_mae": 12.8733,
    "improvement_vs_baseline_percent": 8.04,
}


def override_manager_user():
    return SimpleNamespace(
        role=UserRole.MANAGER,
    )


def override_front_desk_user():
    return SimpleNamespace(
        role=UserRole.FRONT_DESK,
    )


def test_unauthenticated_user_gets_401():
    app.dependency_overrides.clear()

    response = client.get(
        "/api/v1/forecast/occupancy"
    )

    assert response.status_code == 401


def test_front_desk_user_gets_403():
    app.dependency_overrides[get_current_user] = (
        override_front_desk_user
    )

    try:
        response = client.get(
            "/api/v1/forecast/occupancy"
        )

        assert response.status_code == 403

        assert response.json()["detail"] == (
            "You do not have permission to perform this action."
        )
    finally:
        app.dependency_overrides.clear()


def test_manager_user_gets_200(monkeypatch):
    app.dependency_overrides[get_current_user] = (
        override_manager_user
    )

    monkeypatch.setattr(
        occupancy_forecast,
        "predict_next_day_occupancy",
        lambda: FAKE_FORECAST,
    )

    try:
        response = client.get(
            "/api/v1/forecast/occupancy"
        )

        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_manager_response_contains_demand_level(
    monkeypatch,
):
    app.dependency_overrides[get_current_user] = (
        override_manager_user
    )

    monkeypatch.setattr(
        occupancy_forecast,
        "predict_next_day_occupancy",
        lambda: FAKE_FORECAST,
    )

    try:
        response = client.get(
            "/api/v1/forecast/occupancy"
        )

        data = response.json()

        assert data["demand_level"] == "HIGH"
    finally:
        app.dependency_overrides.clear()


def test_manager_response_contains_recommendation(
    monkeypatch,
):
    app.dependency_overrides[get_current_user] = (
        override_manager_user
    )

    monkeypatch.setattr(
        occupancy_forecast,
        "predict_next_day_occupancy",
        lambda: FAKE_FORECAST,
    )

    try:
        response = client.get(
            "/api/v1/forecast/occupancy"
        )

        data = response.json()

        assert "operational_recommendation" in data

        assert len(
            data["operational_recommendation"]
        ) > 0
    finally:
        app.dependency_overrides.clear()