from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_current_user,
    require_roles,
)
from app.db.session import get_db_session
from app.models.user import User, UserRole
from app.schemas.room_category import (
    RoomCategoryCreate,
    RoomCategoryResponse,
)
from app.services.room_category_service import (
    RoomCategoryAlreadyExistsError,
    add_room_category,
    get_room_categories,
)


router = APIRouter(
    prefix="/room-categories",
    tags=["Room Categories"],
)


@router.post(
    "",
    response_model=RoomCategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_category(
    category_data: RoomCategoryCreate,
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
    current_manager: Annotated[
        User,
        Depends(require_roles(UserRole.MANAGER)),
    ],
) -> RoomCategoryResponse:
    try:
        category = await add_room_category(
            session,
            category_data,
        )

        return RoomCategoryResponse.model_validate(category)

    except RoomCategoryAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A room category with this name already exists.",
        ) from error


@router.get(
    "",
    response_model=list[RoomCategoryResponse],
)
async def get_categories(
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    offset: Annotated[
        int,
        Query(ge=0),
    ] = 0,
    limit: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 20,
) -> list[RoomCategoryResponse]:
    categories = await get_room_categories(
        session,
        offset=offset,
        limit=limit,
    )

    return [
        RoomCategoryResponse.model_validate(category)
        for category in categories
    ]