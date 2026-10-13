from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description=(
            "Backend API for the AI Hotel Operations "
            "and Guest Experience Platform."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
    )

    allowed_origins = [
        origin.strip()
        for origin in settings.cors_origins.split(",")
        if origin.strip()
    ]

    application.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(
        api_router,
        prefix=settings.api_v1_prefix,
    )

    @application.get("/", tags=["Root"])
    async def root() -> dict[str, str]:
        return {
            "message": f"{settings.app_name} is running",
            "environment": settings.environment,
        }

    return application


app = create_app()