from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DATA_PATH = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "hotel_bookings.csv"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "daily_occupancy.csv"
)


def load_bookings() -> pd.DataFrame:
    return pd.read_csv(RAW_DATA_PATH)


def build_arrival_date(
    df: pd.DataFrame,
) -> pd.DataFrame:
    df = df.copy()

    month_number = pd.to_datetime(
        df["arrival_date_month"],
        format="%B",
    ).dt.month

    df["arrival_date"] = pd.to_datetime(
        {
            "year": df["arrival_date_year"],
            "month": month_number,
            "day": df["arrival_date_day_of_month"],
        }
    )

    return df


def prepare_city_hotel_bookings(
    df: pd.DataFrame,
) -> pd.DataFrame:
    df = df.copy()

    df = df[
        (df["hotel"] == "City Hotel")
        & (df["is_canceled"] == 0)
    ].copy()

    df["stay_nights"] = (
        df["stays_in_weekend_nights"]
        + df["stays_in_week_nights"]
    )

    df = df[
        df["stay_nights"] > 0
    ].copy()

    df["departure_date"] = (
        df["arrival_date"]
        + pd.to_timedelta(
            df["stay_nights"],
            unit="D",
        )
    )

    return df


def expand_to_room_nights(
    df: pd.DataFrame,
    horizon_end: pd.Timestamp,
) -> pd.DataFrame:
    occupied_dates = []

    for row in df.itertuples():
        final_occupied_date = (
            row.departure_date
            - pd.Timedelta(days=1)
        )

        # The source dataset contains no arrivals
        # after horizon_end. Therefore dates beyond
        # this point would represent incomplete demand.
        final_occupied_date = min(
            final_occupied_date,
            horizon_end,
        )

        dates = pd.date_range(
            start=row.arrival_date,
            end=final_occupied_date,
            freq="D",
        )

        occupied_dates.extend(dates)

    return pd.DataFrame(
        {
            "date": occupied_dates,
        }
    )


def aggregate_daily_occupancy(
    room_nights: pd.DataFrame,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
) -> pd.DataFrame:
    daily_counts = (
        room_nights
        .groupby("date")
        .size()
        .reset_index(name="occupied_rooms")
    )

    calendar = pd.DataFrame(
        {
            "date": pd.date_range(
                start=start_date,
                end=end_date,
                freq="D",
            )
        }
    )

    daily = calendar.merge(
        daily_counts,
        on="date",
        how="left",
    )

    daily["occupied_rooms"] = (
        daily["occupied_rooms"]
        .fillna(0)
        .astype(int)
    )

    return daily


def main() -> None:
    bookings = load_bookings()

    bookings = build_arrival_date(
        bookings
    )

    source_start = bookings[
        "arrival_date"
    ].min()

    source_end = bookings[
        "arrival_date"
    ].max()

    city_bookings = (
        prepare_city_hotel_bookings(
            bookings
        )
    )

    room_nights = expand_to_room_nights(
        city_bookings,
        horizon_end=source_end,
    )

    daily = aggregate_daily_occupancy(
        room_nights,
        start_date=source_start,
        end_date=source_end,
    )

    daily.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print(
        "Valid City Hotel bookings:",
        len(city_bookings),
    )

    print(
        "Daily dataset shape:",
        daily.shape,
    )

    print(
        "Date range:",
        daily["date"].min().date(),
        "to",
        daily["date"].max().date(),
    )

    print(
        "Occupied-room demand range:",
        daily["occupied_rooms"].min(),
        "to",
        daily["occupied_rooms"].max(),
    )

    print(
        "\nLast rows:"
    )

    print(
        daily.tail()
    )

    print(
        "\nSaved to:",
        OUTPUT_PATH,
    )


if __name__ == "__main__":
    main()