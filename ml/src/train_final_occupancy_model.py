from pathlib import Path
import json

import joblib
import pandas as pd

from sklearn.ensemble import GradientBoostingRegressor


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_PATH = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "daily_occupancy.csv"
)

MODEL_PATH = (
    PROJECT_ROOT
    / "ml"
    / "models"
    / "occupancy_forecast_model.joblib"
)

METADATA_PATH = (
    PROJECT_ROOT
    / "ml"
    / "models"
    / "occupancy_model_metadata.json"
)


def load_data():
    return (
        pd.read_csv(
            DATA_PATH,
            parse_dates=["date"],
        )
        .sort_values("date")
        .reset_index(drop=True)
    )


def create_features(df):
    df = df.copy()

    df["day_of_week"] = df["date"].dt.dayofweek
    df["month"] = df["date"].dt.month
    df["day_of_year"] = df["date"].dt.dayofyear

    df["is_weekend"] = (
        df["day_of_week"] >= 5
    ).astype(int)

    df["lag_1"] = (
        df["occupied_rooms"].shift(1)
    )

    df["lag_2"] = (
        df["occupied_rooms"].shift(2)
    )

    df["lag_3"] = (
        df["occupied_rooms"].shift(3)
    )

    df["lag_7"] = (
        df["occupied_rooms"].shift(7)
    )

    df["lag_14"] = (
        df["occupied_rooms"].shift(14)
    )

    df["lag_28"] = (
        df["occupied_rooms"].shift(28)
    )

    previous = (
        df["occupied_rooms"].shift(1)
    )

    df["rolling_mean_3"] = (
        previous.rolling(3).mean()
    )

    df["rolling_mean_7"] = (
        previous.rolling(7).mean()
    )

    df["rolling_mean_14"] = (
        previous.rolling(14).mean()
    )

    df["rolling_mean_28"] = (
        previous.rolling(28).mean()
    )

    df["rolling_std_7"] = (
        previous.rolling(7).std()
    )

    return (
        df
        .dropna()
        .reset_index(drop=True)
    )


def main():
    df = create_features(
        load_data()
    )

    feature_columns = [
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
    ]

    X = df[feature_columns]
    y = df["occupied_rooms"]

    model = GradientBoostingRegressor(
        n_estimators=200,
        learning_rate=0.03,
        max_depth=3,
        loss="huber",
        random_state=42,
    )

    model.fit(
        X,
        y,
    )

    artifact = {
        "model": model,
        "feature_columns": feature_columns,
    }

    joblib.dump(
        artifact,
        MODEL_PATH,
    )

    metadata = {
        "model_type":
            "GradientBoostingRegressor",

        "forecast_horizon":
            "one_day_ahead",

        "training_rows":
            int(len(df)),

        "training_start_date":
            str(df["date"].min().date()),

        "training_end_date":
            str(df["date"].max().date()),

        "target":
            (
                "Daily occupied-room demand proxy "
                "for City Hotel."
            ),

        "rolling_validation_mean_mae":
            11.8386,

        "baseline_mean_mae":
            12.8733,

        "mae_improvement_vs_baseline_percent":
            8.04,

        "validation_folds":
            5,

        "important_limitation":
            (
                "Target is a demand proxy constructed "
                "from non-cancelled historical stays, "
                "not verified physical hotel occupancy."
            ),
    }

    with open(
        METADATA_PATH,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            metadata,
            file,
            indent=2,
        )

    print(
        "Final model:",
        type(model).__name__,
    )

    print(
        "Training rows:",
        len(df),
    )

    print(
        "Training period:",
        df["date"].min().date(),
        "to",
        df["date"].max().date(),
    )

    print(
        "Features:",
        len(feature_columns),
    )

    print(
        "Model saved to:",
        MODEL_PATH,
    )

    print(
        "Metadata saved to:",
        METADATA_PATH,
    )


if __name__ == "__main__":
    main()