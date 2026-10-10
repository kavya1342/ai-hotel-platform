from datetime import UTC, datetime

from fastapi import APIRouter


router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def get_health() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "api",
        "timestamp": datetime.now(UTC).isoformat(),
    }