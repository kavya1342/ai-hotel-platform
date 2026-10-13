from app.services.occupancy_forecast_service import (
    build_next_day_features,
    classify_demand,
    load_model_artifact,
    load_occupancy_history,
    predict_next_day_occupancy,
)


def test_model_artifact_loads():
    artifact = load_model_artifact()

    assert "model" in artifact
    assert "feature_columns" in artifact
    assert len(artifact["feature_columns"]) > 0


def test_feature_generation_contains_required_features():
    history = load_occupancy_history()

    target_date, features = build_next_day_features(history)

    required_features = {
        "day_of_week",
        "month",
        "day_of_year",
        "is_weekend",
        "lag_1",
        "lag_2",
        "lag_3",
        "lag_7",
        "lag_14",
        "lag_28",
        "rolling_mean_3",
        "rolling_mean_7",
        "rolling_mean_14",
        "rolling_mean_28",
        "rolling_std_7",
    }

    assert set(features.keys()) == required_features
    assert target_date > history["date"].iloc[-1]


def test_prediction_is_non_negative():
    forecast = predict_next_day_occupancy()

    assert forecast["predicted_occupied_rooms"] >= 0


def test_prediction_contains_expected_fields():
    forecast = predict_next_day_occupancy()

    expected_fields = {
        "forecast_date",
        "predicted_occupied_rooms",
        "demand_level",
        "operational_recommendation",
        "model",
        "forecast_horizon",
        "historical_data_end",
        "target_definition",
        "validation_mean_mae",
        "baseline_mean_mae",
        "improvement_vs_baseline_percent",
    }

    assert expected_fields.issubset(forecast.keys())


def test_demand_level_is_valid():
    forecast = predict_next_day_occupancy()

    assert forecast["demand_level"] in {
        "LOW",
        "MEDIUM",
        "HIGH",
    }


def test_current_forecast_is_high_demand():
    forecast = predict_next_day_occupancy()

    assert forecast["demand_level"] == "HIGH"


def test_demand_classification_returns_recommendation():
    history = load_occupancy_history()

    demand_level, recommendation = classify_demand(
        prediction=219.5,
        history=history,
    )

    assert demand_level in {
        "LOW",
        "MEDIUM",
        "HIGH",
    }

    assert isinstance(recommendation, str)
    assert len(recommendation) > 0