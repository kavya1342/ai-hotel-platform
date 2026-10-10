from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.room_categories import (
    router as room_categories_router,
)
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.rooms import router as rooms_router
from app.api.v1.endpoints.reservations import (
    router as reservations_router,
)
from app.api.v1.endpoints.operational_tasks import (
    router as operational_tasks_router,
)
from app.api.v1.endpoints.guest_requests import (
    router as guest_requests_router,
)
from app.api.v1.endpoints.occupancy_forecast import (
    router as occupancy_forecast_router,
)


api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(room_categories_router)
api_router.include_router(rooms_router)
api_router.include_router(reservations_router)
api_router.include_router(operational_tasks_router)
api_router.include_router(guest_requests_router)
api_router.include_router(occupancy_forecast_router)