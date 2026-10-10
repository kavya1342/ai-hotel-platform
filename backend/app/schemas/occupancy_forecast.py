from pydantic import BaseModel


class OccupancyForecastResponse(BaseModel):
    forecast_date: str
    predicted_occupied_rooms: float

    model: str
    forecast_horizon: str
    historical_data_end: str

    target_definition: str

    validation_mean_mae: float
    baseline_mean_mae: float
    improvement_vs_baseline_percent: float