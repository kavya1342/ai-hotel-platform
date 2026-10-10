from pathlib import Path
import json

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)


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

METRICS_PATH = (
    PROJECT_ROOT
    / "ml"
    / "models"
    / "occupancy_metrics.json"
)

PREDICTIONS_PATH = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "occupancy_test_predictions.csv"
)


def load_data() -> pd.DataFrame:
    df = pd.read_csv(
        DATA_PATH,
        parse_dates=["date"],
    )

    return df.sort_values("date").reset_index(drop=True)


def create_features(
    df: pd.DataFrame,
) -> pd.DataFrame:
    df = df.copy()

    # Calendar features
    df["day_of_week"] = df["date"].dt.dayofweek
    df["month"] = df["date"].dt.month
    df["day_of_year"] = df["date"].dt.dayofyear
    df["is_weekend"] = (
        df["day_of_week"] >= 5
    ).astype(int)

    # Lag features
    # These only use values known before the target date.
    df["lag_1"] = df["occupied_rooms"].shift(1)
    df["lag_7"] = df["occupied_rooms"].shift(7)
    df["lag_14"] = df["occupied_rooms"].shift(14)
    df["lag_28"] = df["occupied_rooms"].shift(28)

    # Rolling features.
    # shift(1) prevents using the current day's target.
    previous_values = df["occupied_rooms"].shift(1)

    df["rolling_mean_7"] = (
        previous_values
        .rolling(window=7)
        .mean()
    )

    df["rolling_mean_28"] = (
        previous_values
        .rolling(window=28)
        .mean()
    )

    df["rolling_std_7"] = (
        previous_values
        .rolling(window=7)
        .std()
    )

    return df.dropna().reset_index(drop=True)


def calculate_metrics(
    y_true: pd.Series,
    predictions: np.ndarray,
) -> dict:
    mae = mean_absolute_error(
        y_true,
        predictions,
    )

    rmse = np.sqrt(
        mean_squared_error(
            y_true,
            predictions,
        )
    )

    r2 = r2_score(
        y_true,
        predictions,
    )

    return {
        "mae": round(float(mae), 4),
        "rmse": round(float(rmse), 4),
        "r2": round(float(r2), 4),
    }


def main() -> None:
    df = load_data()

    feature_df = create_features(df)

    feature_columns = [
        "day_of_week",
        "month",
        "day_of_year",
        "is_weekend",
        "lag_1",
        "lag_7",
        "lag_14",
        "lag_28",
        "rolling_mean_7",
        "rolling_mean_28",
        "rolling_std_7",
    ]

    target_column = "occupied_rooms"

    # --------------------------------------------------
    # TIME-BASED SPLIT
    # --------------------------------------------------

    # Use the final 90 days as unseen test data.
    test_days = 90

    train_df = feature_df.iloc[:-test_days].copy()
    test_df = feature_df.iloc[-test_days:].copy()

    X_train = train_df[feature_columns]
    y_train = train_df[target_column]

    X_test = test_df[feature_columns]
    y_test = test_df[target_column]

    # --------------------------------------------------
    # BASELINES
    # --------------------------------------------------

    # Baseline 1:
    # tomorrow behaves like yesterday
    baseline_lag1 = test_df["lag_1"].to_numpy()

    # Baseline 2:
    # tomorrow behaves like the same weekday last week
    baseline_lag7 = test_df["lag_7"].to_numpy()

    baseline_lag1_metrics = calculate_metrics(
        y_test,
        baseline_lag1,
    )

    baseline_lag7_metrics = calculate_metrics(
        y_test,
        baseline_lag7,
    )

    # --------------------------------------------------
    # RANDOM FOREST
    # --------------------------------------------------

    model = RandomForestRegressor(
        n_estimators=300,
        max_depth=12,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )

    model.fit(
        X_train,
        y_train,
    )

    predictions = model.predict(X_test)

    predictions = np.clip(
        predictions,
        a_min=0,
        a_max=None,
    )

    model_metrics = calculate_metrics(
        y_test,
        predictions,
    )

    # --------------------------------------------------
    # SAVE TEST PREDICTIONS
    # --------------------------------------------------

    prediction_df = pd.DataFrame(
        {
            "date": test_df["date"],
            "actual": y_test.to_numpy(),
            "baseline_lag1": baseline_lag1,
            "baseline_lag7": baseline_lag7,
            "ml_prediction": predictions,
        }
    )

    prediction_df.to_csv(
        PREDICTIONS_PATH,
        index=False,
    )

    # --------------------------------------------------
    # SAVE MODEL
    # --------------------------------------------------

    model_artifact = {
        "model": model,
        "feature_columns": feature_columns,
        "training_end_date": (
            train_df["date"].max().strftime(
                "%Y-%m-%d"
            )
        ),
        "target_definition": (
            "Daily occupied-room demand proxy "
            "constructed from non-cancelled City Hotel stays."
        ),
    }

    joblib.dump(
        model_artifact,
        MODEL_PATH,
    )

    # --------------------------------------------------
    # SAVE METRICS
    # --------------------------------------------------

    metrics = {
        "train_rows": int(len(train_df)),
        "test_rows": int(len(test_df)),
        "train_start": str(
            train_df["date"].min().date()
        ),
        "train_end": str(
            train_df["date"].max().date()
        ),
        "test_start": str(
            test_df["date"].min().date()
        ),
        "test_end": str(
            test_df["date"].max().date()
        ),
        "baseline_lag1": baseline_lag1_metrics,
        "baseline_lag7": baseline_lag7_metrics,
        "random_forest": model_metrics,
    }

    with open(
        METRICS_PATH,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            metrics,
            file,
            indent=2,
        )

    # --------------------------------------------------
    # OUTPUT
    # --------------------------------------------------

    print("Train rows:", len(train_df))
    print("Test rows:", len(test_df))

    print(
        "\nTrain period:",
        train_df["date"].min().date(),
        "to",
        train_df["date"].max().date(),
    )

    print(
        "Test period:",
        test_df["date"].min().date(),
        "to",
        test_df["date"].max().date(),
    )

    print("\nBaseline - Yesterday:")
    print(baseline_lag1_metrics)

    print("\nBaseline - Same day last week:")
    print(baseline_lag7_metrics)

    print("\nRandom Forest:")
    print(model_metrics)

    print(
        "\nModel saved to:",
        MODEL_PATH,
    )

    print(
        "Metrics saved to:",
        METRICS_PATH,
    )


if __name__ == "__main__":
    main()