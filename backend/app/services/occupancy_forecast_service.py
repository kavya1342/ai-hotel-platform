from pathlib import Path

import joblib
import pandas as pd


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[3]
)

MODEL_PATH = (
    PROJECT_ROOT
    / "ml"
    / "models"
    / "occupancy_forecast_model.joblib"
)

DATA_PATH = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "daily_occupancy.csv"
)


class OccupancyForecastError(Exception):
    pass


def load_model_artifact():
    if not MODEL_PATH.exists():
        raise OccupancyForecastError(
            "Occupancy forecast model was not found."
        )

    return joblib.load(MODEL_PATH)


def load_occupancy_history():
    if not DATA_PATH.exists():
        raise OccupancyForecastError(
            "Historical occupancy data was not found."
        )

    df = pd.read_csv(
        DATA_PATH,
        parse_dates=["date"],
    )

    df = (
        df
        .sort_values("date")
        .reset_index(drop=True)
    )

    if len(df) < 28:
        raise OccupancyForecastError(
            "At least 28 days of occupancy history are required."
        )

    return df


def build_next_day_features(
    history: pd.DataFrame,
):
    target_date = (
        history["date"].iloc[-1]
        + pd.Timedelta(days=1)
    )

    occupied = history[
        "occupied_rooms"
    ]

    feature_row = {
        "day_of_week":
            target_date.dayofweek,

        "month":
            target_date.month,

        "day_of_year":
            target_date.dayofyear,

        "is_weekend":
            int(target_date.dayofweek >= 5),

        "lag_1":
            occupied.iloc[-1],

        "lag_2":
            occupied.iloc[-2],

        "lag_3":
            occupied.iloc[-3],

        "lag_7":
            occupied.iloc[-7],

        "lag_14":
            occupied.iloc[-14],

        "lag_28":
            occupied.iloc[-28],

        "rolling_mean_3":
            occupied.iloc[-3:].mean(),

        "rolling_mean_7":
            occupied.iloc[-7:].mean(),

        "rolling_mean_14":
            occupied.iloc[-14:].mean(),

        "rolling_mean_28":
            occupied.iloc[-28:].mean(),

        "rolling_std_7":
            occupied.iloc[-7:].std(),
    }

    return target_date, feature_row


def classify_demand(
    prediction: float,
    history: pd.DataFrame,
):
    occupied = history["occupied_rooms"]

    low_threshold = float(
        occupied.quantile(0.33)
    )

    high_threshold = float(
        occupied.quantile(0.67)
    )

    if prediction < low_threshold:
        return (
            "LOW",
            (
                "Lower historical demand is expected. "
                "Use the period for preventive maintenance, "
                "staff training, and non-urgent room work."
            ),
        )

    if prediction <= high_threshold:
        return (
            "MEDIUM",
            (
                "Moderate historical demand is expected. "
                "Maintain normal housekeeping and front-desk "
                "coverage while monitoring room readiness."
            ),
        )

    return (
        "HIGH",
        (
            "High historical demand is expected. "
            "Review housekeeping coverage, front-desk staffing, "
            "and room readiness before the forecast date."
        ),
    )


def predict_next_day_occupancy():
    artifact = load_model_artifact()

    model = artifact["model"]

    feature_columns = artifact[
        "feature_columns"
    ]

    history = load_occupancy_history()

    target_date, feature_row = (
        build_next_day_features(
            history
        )
    )

    features = pd.DataFrame(
        [feature_row]
    )

    features = features[
        feature_columns
    ]

    prediction = model.predict(
        features
    )[0]

    prediction = max(
        float(prediction),
        0.0,
    )

    demand_level, recommendation = (
        classify_demand(
            prediction,
            history,
        )
    )

    return {
        "forecast_date":
            target_date.date().isoformat(),

        "predicted_occupied_rooms":
            round(prediction, 1),

        "demand_level":
            demand_level,

        "operational_recommendation":
            recommendation,

        "model":
            type(model).__name__,

        "forecast_horizon":
            "one_day_ahead",

        "historical_data_end":
            history["date"]
            .iloc[-1]
            .date()
            .isoformat(),

        "target_definition":
            (
                "Daily occupied-room demand proxy "
                "based on non-cancelled City Hotel stays."
            ),

        "validation_mean_mae":
            11.8386,

        "baseline_mean_mae":
            12.8733,

        "improvement_vs_baseline_percent":
            8.04,
    }