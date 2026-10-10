from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.ensemble import (
    ExtraTreesRegressor,
    GradientBoostingRegressor,
    HistGradientBoostingRegressor,
    RandomForestRegressor,
)
from sklearn.linear_model import Ridge
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_PATH = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "daily_occupancy.csv"
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

    df["lag_1"] = df["occupied_rooms"].shift(1)
    df["lag_2"] = df["occupied_rooms"].shift(2)
    df["lag_3"] = df["occupied_rooms"].shift(3)
    df["lag_7"] = df["occupied_rooms"].shift(7)
    df["lag_14"] = df["occupied_rooms"].shift(14)
    df["lag_28"] = df["occupied_rooms"].shift(28)

    previous = df["occupied_rooms"].shift(1)

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

    return df.dropna().reset_index(drop=True)


def metrics(y_true, predictions):
    predictions = np.clip(
        predictions,
        0,
        None,
    )

    return {
        "MAE": round(
            mean_absolute_error(
                y_true,
                predictions,
            ),
            4,
        ),
        "RMSE": round(
            np.sqrt(
                mean_squared_error(
                    y_true,
                    predictions,
                )
            ),
            4,
        ),
        "R2": round(
            r2_score(
                y_true,
                predictions,
            ),
            4,
        ),
    }


def main():
    df = create_features(
        load_data()
    )

    features = [
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

    test_days = 90

    train = df.iloc[:-test_days]
    test = df.iloc[-test_days:]

    X_train = train[features]
    y_train = train["occupied_rooms"]

    X_test = test[features]
    y_test = test["occupied_rooms"]

    print(
        "Train period:",
        train["date"].min().date(),
        "to",
        train["date"].max().date(),
    )

    print(
        "Test period:",
        test["date"].min().date(),
        "to",
        test["date"].max().date(),
    )

    print("\nBASELINES")

    print(
        "Yesterday:",
        metrics(
            y_test,
            test["lag_1"],
        ),
    )

    print(
        "Last week:",
        metrics(
            y_test,
            test["lag_7"],
        ),
    )

    models = {
        "Ridge": make_pipeline(
            StandardScaler(),
            Ridge(alpha=10.0),
        ),

        "Random Forest": RandomForestRegressor(
            n_estimators=400,
            max_depth=10,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
        ),

        "Extra Trees": ExtraTreesRegressor(
            n_estimators=400,
            max_depth=12,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
        ),

        "Gradient Boosting": GradientBoostingRegressor(
            n_estimators=200,
            learning_rate=0.03,
            max_depth=3,
            loss="huber",
            random_state=42,
        ),

        "Hist Gradient Boosting":
            HistGradientBoostingRegressor(
                max_iter=300,
                learning_rate=0.05,
                max_leaf_nodes=15,
                l2_regularization=1.0,
                random_state=42,
            ),
    }

    print("\nMODELS")

    results = []

    for name, model in models.items():
        model.fit(
            X_train,
            y_train,
        )

        predictions = model.predict(
            X_test
        )

        result = metrics(
            y_test,
            predictions,
        )

        results.append(
            {
                "Model": name,
                **result,
            }
        )

        print(
            f"{name}:",
            result,
        )

    results_df = pd.DataFrame(
        results
    ).sort_values("MAE")

    print("\nRANKING BY MAE")
    print(
        results_df.to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()