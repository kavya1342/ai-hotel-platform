from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from app.api.dependencies import require_roles
from app.models.user import User, UserRole
from app.schemas.occupancy_forecast import (
    OccupancyForecastResponse,
)
from app.services.occupancy_forecast_service import (
    OccupancyForecastError,
    predict_next_day_occupancy,
)


router = APIRouter(
    prefix="/forecast",
    tags=["Occupancy Forecast"],
)


@router.get(
    "/occupancy",
    response_model=OccupancyForecastResponse,
)
def get_occupancy_forecast(
    current_user: Annotated[
        User,
        Depends(
            require_roles(
                UserRole.MANAGER,
            )
        ),
    ],
) -> OccupancyForecastResponse:
    try:
        forecast = predict_next_day_occupancy()

        return OccupancyForecastResponse(
            **forecast
        )

    except OccupancyForecastError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error