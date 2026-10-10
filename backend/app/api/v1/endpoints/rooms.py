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
from app.models.room import RoomStatus
from app.models.user import User, UserRole
from app.schemas.room import (
    RoomCreate,
    RoomResponse,
    RoomStatusUpdate,
)
from app.services.room_service import (
    RoomAlreadyExistsError,
    RoomCategoryNotFoundError,
    RoomNotFoundError,
    add_room,
    change_room_status,
    get_rooms,
)


router = APIRouter(
    prefix="/rooms",
    tags=["Rooms"],
)


@router.post(
    "",
    response_model=RoomResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_hotel_room(
    room_data: RoomCreate,
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
    current_manager: Annotated[
        User,
        Depends(require_roles(UserRole.MANAGER)),
    ],
) -> RoomResponse:
    try:
        room = await add_room(session, room_data)
        return RoomResponse.model_validate(room)

    except RoomCategoryNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The selected room category was not found.",
        ) from error

    except RoomAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A room with this room number already exists.",
        ) from error


@router.get(
    "",
    response_model=list[RoomResponse],
)
async def get_hotel_rooms(
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    room_status: RoomStatus | None = None,
    category_id: Annotated[int | None, Query(gt=0)] = None,
    floor: Annotated[int | None, Query(ge=0)] = None,
) -> list[RoomResponse]:
    rooms = await get_rooms(
        session,
        offset=offset,
        limit=limit,
        status=room_status,
        category_id=category_id,
        floor=floor,
    )

    return [
        RoomResponse.model_validate(room)
        for room in rooms
    ]


@router.patch(
    "/{room_id}/status",
    response_model=RoomResponse,
)
async def update_hotel_room_status(
    room_id: int,
    status_data: RoomStatusUpdate,
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
    current_user: Annotated[
        User,
        Depends(
            require_roles(
                UserRole.MANAGER,
                UserRole.OPERATIONS,
            )
        ),
    ],
) -> RoomResponse:
    try:
        room = await change_room_status(
            session,
            room_id=room_id,
            new_status=status_data.status,
        )

        return RoomResponse.model_validate(room)

    except RoomNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found.",
        ) from error