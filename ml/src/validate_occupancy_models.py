from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.ensemble import (
    GradientBoostingRegressor,
    HistGradientBoostingRegressor,
    RandomForestRegressor,
)
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_PATH = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "daily_occupancy.csv"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "rolling_validation_results.csv"
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
        previous
        .rolling(3)
        .mean()
    )

    df["rolling_mean_7"] = (
        previous
        .rolling(7)
        .mean()
    )

    df["rolling_mean_14"] = (
        previous
        .rolling(14)
        .mean()
    )

    df["rolling_mean_28"] = (
        previous
        .rolling(28)
        .mean()
    )

    df["rolling_std_7"] = (
        previous
        .rolling(7)
        .std()
    )

    return (
        df
        .dropna()
        .reset_index(drop=True)
    )


def calculate_metrics(
    actual,
    prediction,
):
    prediction = np.clip(
        prediction,
        0,
        None,
    )

    mae = mean_absolute_error(
        actual,
        prediction,
    )

    rmse = np.sqrt(
        mean_squared_error(
            actual,
            prediction,
        )
    )

    return (
        float(mae),
        float(rmse),
    )


def build_models():
    return {
        "Random Forest":
            RandomForestRegressor(
                n_estimators=300,
                max_depth=10,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1,
            ),

        "Gradient Boosting":
            GradientBoostingRegressor(
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

    fold_size = 60
    number_of_folds = 5

    total_validation_rows = (
        fold_size
        * number_of_folds
    )

    first_validation_index = (
        len(df)
        - total_validation_rows
    )

    results = []

    for fold_number in range(
        number_of_folds
    ):
        test_start = (
            first_validation_index
            + fold_number
            * fold_size
        )

        test_end = (
            test_start
            + fold_size
        )

        train = df.iloc[
            :test_start
        ].copy()

        test = df.iloc[
            test_start:test_end
        ].copy()

        X_train = train[
            feature_columns
        ]

        y_train = train[
            "occupied_rooms"
        ]

        X_test = test[
            feature_columns
        ]

        y_test = test[
            "occupied_rooms"
        ]

        print(
            f"\nFOLD {fold_number + 1}"
        )

        print(
            "Train:",
            train["date"].min().date(),
            "to",
            train["date"].max().date(),
        )

        print(
            "Test:",
            test["date"].min().date(),
            "to",
            test["date"].max().date(),
        )

        # ----------------------------------------------
        # BASELINE
        # ----------------------------------------------

        baseline_prediction = (
            test["lag_1"].to_numpy()
        )

        baseline_mae, baseline_rmse = (
            calculate_metrics(
                y_test,
                baseline_prediction,
            )
        )

        results.append(
            {
                "fold":
                    fold_number + 1,

                "model":
                    "Yesterday Baseline",

                "mae":
                    baseline_mae,

                "rmse":
                    baseline_rmse,

                "test_start":
                    test["date"]
                    .min()
                    .date(),

                "test_end":
                    test["date"]
                    .max()
                    .date(),
            }
        )

        print(
            "Yesterday Baseline:",
            {
                "MAE": round(
                    baseline_mae,
                    4,
                ),
                "RMSE": round(
                    baseline_rmse,
                    4,
                ),
            },
        )

        # ----------------------------------------------
        # MODELS
        # ----------------------------------------------

        models = build_models()

        for model_name, model in models.items():
            model.fit(
                X_train,
                y_train,
            )

            prediction = model.predict(
                X_test
            )

            mae, rmse = (
                calculate_metrics(
                    y_test,
                    prediction,
                )
            )

            results.append(
                {
                    "fold":
                        fold_number + 1,

                    "model":
                        model_name,

                    "mae":
                        mae,

                    "rmse":
                        rmse,

                    "test_start":
                        test["date"]
                        .min()
                        .date(),

                    "test_end":
                        test["date"]
                        .max()
                        .date(),
                }
            )

            print(
                f"{model_name}:",
                {
                    "MAE":
                        round(mae, 4),

                    "RMSE":
                        round(rmse, 4),
                },
            )

    # --------------------------------------------------
    # SUMMARY
    # --------------------------------------------------

    results_df = pd.DataFrame(
        results
    )

    results_df.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    summary = (
        results_df
        .groupby("model")
        .agg(
            mean_mae=("mae", "mean"),
            std_mae=("mae", "std"),
            mean_rmse=("rmse", "mean"),
            std_rmse=("rmse", "std"),
        )
        .reset_index()
        .sort_values("mean_mae")
    )

    print(
        "\n================================="
    )

    print(
        "ROLLING VALIDATION SUMMARY"
    )

    print(
        "================================="
    )

    print(
        summary.to_string(
            index=False,
            float_format=lambda value:
                f"{value:.4f}",
        )
    )

    baseline_mae = (
        summary.loc[
            summary["model"]
            == "Yesterday Baseline",
            "mean_mae",
        ]
        .iloc[0]
    )

    print(
        "\nMAE IMPROVEMENT VS BASELINE"
    )

    for row in summary.itertuples():
        if row.model == "Yesterday Baseline":
            continue

        improvement = (
            (
                baseline_mae
                - row.mean_mae
            )
            / baseline_mae
            * 100
        )

        print(
            f"{row.model}: "
            f"{improvement:.2f}%"
        )

    print(
        "\nDetailed results saved to:",
        OUTPUT_PATH,
    )


if __name__ == "__main__":
    main()