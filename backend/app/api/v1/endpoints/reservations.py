from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from app.schemas.room import RoomResponse
from app.schemas.reservation import RoomAssignmentRequest

from app.api.dependencies import require_roles
from app.db.session import get_db_session
from app.models.user import User, UserRole
from app.schemas.reservation import (
    ReservationCreate,
    ReservationResponse,
)
from app.services.reservation_service import (
    ReservationConflictError,
    ReservationGuestNotFoundError,
    ReservationRoomNotFoundError,
    RoomCapacityExceededError,
    RoomUnavailableError,ReservationCannotBeModifiedError,
ReservationNotFoundError,ReservationCancellationNotAllowedError,
ReservationCheckInNotAllowedError,
ReservationCheckOutNotAllowedError,
ReservationRoomNotAssignedError,
cancel_reservation,
check_in_reservation,
check_out_reservation,
assign_room_to_reservation,
find_available_rooms,
    add_reservation,
    get_reservations,
)


router = APIRouter(
    prefix="/reservations",
    tags=["Reservations"],
)


@router.post(
    "",
    response_model=ReservationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_hotel_reservation(
    reservation_data: ReservationCreate,
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
    current_user: Annotated[
        User,
        Depends(
            require_roles(
                UserRole.MANAGER,
                UserRole.FRONT_DESK,
            )
        ),
    ],
) -> ReservationResponse:
    try:
        reservation = await add_reservation(
            session,
            reservation_data=reservation_data,
            created_by=current_user.id,
        )

        return ReservationResponse.model_validate(reservation)

    except ReservationGuestNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="An active guest account was not found.",
        ) from error

    except ReservationRoomNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The selected room was not found.",
        ) from error

    except RoomUnavailableError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The selected room is operationally unavailable.",
        ) from error

    except RoomCapacityExceededError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The number of guests exceeds room capacity.",
        ) from error

    except ReservationConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The room is already reserved for overlapping dates.",
        ) from error


@router.get(
    "",
    response_model=list[ReservationResponse],
)
async def get_hotel_reservations(
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
    current_user: Annotated[
        User,
        Depends(
            require_roles(
                UserRole.MANAGER,
                UserRole.FRONT_DESK,
                UserRole.GUEST,
            )
        ),
    ],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[ReservationResponse]:
    guest_filter = (
        current_user.id
        if current_user.role == UserRole.GUEST
        else None
    )

    reservations = await get_reservations(
        session,
        offset=offset,
        limit=limit,
        guest_id=guest_filter,
    )

    return [
        ReservationResponse.model_validate(reservation)
        for reservation in reservations
    ]
@router.get(
    "/availability",
    response_model=list[RoomResponse],
)
async def check_room_availability(
    check_in_date: date,
    check_out_date: date,
    number_of_guests: Annotated[int, Query(ge=1, le=20)],
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
    current_user: Annotated[
        User,
        Depends(
            require_roles(
                UserRole.MANAGER,
                UserRole.FRONT_DESK,
            )
        ),
    ],
    category_id: Annotated[int | None, Query(gt=0)] = None,
) -> list[RoomResponse]:
    if check_out_date <= check_in_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Check-out date must be after check-in date.",
        )

    rooms = await find_available_rooms(
        session,
        check_in_date=check_in_date,
        check_out_date=check_out_date,
        number_of_guests=number_of_guests,
        category_id=category_id,
    )

    return [
        RoomResponse.model_validate(room)
        for room in rooms
    ]
@router.post(
    "/{reservation_id}/assign-room",
    response_model=ReservationResponse,
)
async def assign_reservation_room(
    reservation_id: int,
    assignment_data: RoomAssignmentRequest,
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
    current_user: Annotated[
        User,
        Depends(
            require_roles(
                UserRole.MANAGER,
                UserRole.FRONT_DESK,
            )
        ),
    ],
) -> ReservationResponse:
    try:
        reservation = await assign_room_to_reservation(
            session,
            reservation_id=reservation_id,
            room_id=assignment_data.room_id,
        )

        return ReservationResponse.model_validate(reservation)

    except ReservationNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found.",
        ) from error

    except ReservationCannotBeModifiedError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This reservation can no longer be modified.",
        ) from error

    except ReservationRoomNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The selected room was not found.",
        ) from error

    except RoomUnavailableError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The selected room is operationally unavailable.",
        ) from error

    except RoomCapacityExceededError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The number of guests exceeds room capacity.",
        ) from error

    except ReservationConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The room is already reserved for overlapping dates.",
        ) from error
@router.post(
    "/{reservation_id}/check-in",
    response_model=ReservationResponse,
)
async def check_in_guest(
    reservation_id: int,
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
    current_user: Annotated[
        User,
        Depends(
            require_roles(
                UserRole.MANAGER,
                UserRole.FRONT_DESK,
            )
        ),
    ],
) -> ReservationResponse:
    try:
        reservation = await check_in_reservation(
            session,
            reservation_id=reservation_id,
        )

        return ReservationResponse.model_validate(reservation)

    except ReservationNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found.",
        ) from error

    except ReservationRoomNotAssignedError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A room must be assigned before check-in.",
        ) from error

    except ReservationCheckInNotAllowedError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This reservation cannot be checked in.",
        ) from error

    except (
        ReservationRoomNotFoundError,
        RoomUnavailableError,
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The assigned room is not available for check-in.",
        ) from error


@router.post(
    "/{reservation_id}/check-out",
    response_model=ReservationResponse,
)
async def check_out_guest(
    reservation_id: int,
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
    current_user: Annotated[
        User,
        Depends(
            require_roles(
                UserRole.MANAGER,
                UserRole.FRONT_DESK,
            )
        ),
    ],
) -> ReservationResponse:
    try:
        reservation = await check_out_reservation(
    session,
    reservation_id=reservation_id,
    created_by=current_user.id,
)

        return ReservationResponse.model_validate(reservation)

    except ReservationNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found.",
        ) from error

    except ReservationCheckOutNotAllowedError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only a checked-in reservation can be checked out.",
        ) from error

    except (
        ReservationRoomNotAssignedError,
        ReservationRoomNotFoundError,
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The reservation does not have a valid assigned room.",
        ) from error


@router.post(
    "/{reservation_id}/cancel",
    response_model=ReservationResponse,
)
async def cancel_hotel_reservation(
    reservation_id: int,
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
    current_user: Annotated[
        User,
        Depends(
            require_roles(
                UserRole.MANAGER,
                UserRole.FRONT_DESK,
            )
        ),
    ],
) -> ReservationResponse:
    try:
        reservation = await cancel_reservation(
            session,
            reservation_id=reservation_id,
        )

        return ReservationResponse.model_validate(reservation)

    except ReservationNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found.",
        ) from error

    except ReservationCancellationNotAllowedError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This reservation can no longer be cancelled.",
        ) from error