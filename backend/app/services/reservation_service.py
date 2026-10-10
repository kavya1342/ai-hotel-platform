from datetime import UTC, date, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.operational_task import TaskPriority, TaskType
from app.models.reservation import Reservation, ReservationStatus
from app.models.room import Room, RoomStatus
from app.models.user import UserRole
from app.repositories.operational_task_repository import (
    create_operational_task,
)
from app.repositories.reservation_repository import (
    create_reservation,
    get_reservation_by_id,
    has_conflicting_reservation,
    list_reservations,
)
from app.repositories.room_category_repository import (
    get_room_category_by_id,
)
from app.repositories.room_repository import (
    get_room_by_id,
    list_available_rooms,
    update_room_status,
)
from app.repositories.user_repository import get_user_by_id
from app.schemas.reservation import ReservationCreate


class ReservationGuestNotFoundError(Exception):
    pass


class ReservationRoomNotFoundError(Exception):
    pass


class RoomUnavailableError(Exception):
    pass


class RoomCapacityExceededError(Exception):
    pass


class ReservationConflictError(Exception):
    pass


class ReservationNotFoundError(Exception):
    pass


class ReservationCannotBeModifiedError(Exception):
    pass


class ReservationRoomNotAssignedError(Exception):
    pass


class ReservationCheckInNotAllowedError(Exception):
    pass


class ReservationCheckOutNotAllowedError(Exception):
    pass


class ReservationCancellationNotAllowedError(Exception):
    pass


async def add_reservation(
    session: AsyncSession,
    *,
    reservation_data: ReservationCreate,
    created_by: int,
) -> Reservation:
    guest = await get_user_by_id(
        session,
        reservation_data.guest_id,
    )

    if (
        guest is None
        or guest.role != UserRole.GUEST
        or not guest.is_active
    ):
        raise ReservationGuestNotFoundError

    if reservation_data.room_id is not None:
        room = await get_room_by_id(
            session,
            reservation_data.room_id,
        )

        if room is None or not room.is_active:
            raise ReservationRoomNotFoundError

        if room.status in {
            RoomStatus.MAINTENANCE,
            RoomStatus.UNAVAILABLE,
        }:
            raise RoomUnavailableError

        category = await get_room_category_by_id(
            session,
            room.category_id,
        )

        if category is None or not category.is_active:
            raise ReservationRoomNotFoundError

        if (
            reservation_data.number_of_guests
            > category.max_occupancy
        ):
            raise RoomCapacityExceededError

        conflict_exists = await has_conflicting_reservation(
            session,
            room_id=room.id,
            check_in_date=reservation_data.check_in_date,
            check_out_date=reservation_data.check_out_date,
        )

        if conflict_exists:
            raise ReservationConflictError

    try:
        reservation = await create_reservation(
            session,
            guest_id=reservation_data.guest_id,
            room_id=reservation_data.room_id,
            created_by=created_by,
            check_in_date=reservation_data.check_in_date,
            check_out_date=reservation_data.check_out_date,
            number_of_guests=reservation_data.number_of_guests,
        )

        await session.commit()
        await session.refresh(reservation)

        return reservation

    except Exception:
        await session.rollback()
        raise


async def get_reservations(
    session: AsyncSession,
    *,
    offset: int,
    limit: int,
    guest_id: int | None,
) -> list[Reservation]:
    return await list_reservations(
        session,
        offset=offset,
        limit=limit,
        guest_id=guest_id,
    )


async def find_available_rooms(
    session: AsyncSession,
    *,
    check_in_date: date,
    check_out_date: date,
    number_of_guests: int,
    category_id: int | None,
) -> list[Room]:
    return await list_available_rooms(
        session,
        check_in_date=check_in_date,
        check_out_date=check_out_date,
        number_of_guests=number_of_guests,
        category_id=category_id,
    )


async def assign_room_to_reservation(
    session: AsyncSession,
    *,
    reservation_id: int,
    room_id: int,
) -> Reservation:
    reservation = await get_reservation_by_id(
        session,
        reservation_id,
    )

    if reservation is None:
        raise ReservationNotFoundError

    if reservation.status not in {
        ReservationStatus.PENDING,
        ReservationStatus.CONFIRMED,
    }:
        raise ReservationCannotBeModifiedError

    room = await get_room_by_id(session, room_id)

    if room is None or not room.is_active:
        raise ReservationRoomNotFoundError

    if room.status in {
        RoomStatus.MAINTENANCE,
        RoomStatus.UNAVAILABLE,
    }:
        raise RoomUnavailableError

    category = await get_room_category_by_id(
        session,
        room.category_id,
    )

    if category is None or not category.is_active:
        raise ReservationRoomNotFoundError

    if reservation.number_of_guests > category.max_occupancy:
        raise RoomCapacityExceededError

    conflict_exists = await has_conflicting_reservation(
        session,
        room_id=room.id,
        check_in_date=reservation.check_in_date,
        check_out_date=reservation.check_out_date,
        exclude_reservation_id=reservation.id,
    )

    if conflict_exists:
        raise ReservationConflictError

    try:
        reservation.room_id = room.id

        await session.commit()
        await session.refresh(reservation)

        return reservation

    except Exception:
        await session.rollback()
        raise


async def check_in_reservation(
    session: AsyncSession,
    *,
    reservation_id: int,
) -> Reservation:
    reservation = await get_reservation_by_id(
        session,
        reservation_id,
    )

    if reservation is None:
        raise ReservationNotFoundError

    if reservation.status != ReservationStatus.CONFIRMED:
        raise ReservationCheckInNotAllowedError

    if reservation.room_id is None:
        raise ReservationRoomNotAssignedError

    room = await get_room_by_id(
        session,
        reservation.room_id,
    )

    if room is None or not room.is_active:
        raise ReservationRoomNotFoundError

    if room.status != RoomStatus.AVAILABLE:
        raise RoomUnavailableError

    try:
        reservation.status = ReservationStatus.CHECKED_IN
        reservation.actual_check_in_at = datetime.now(UTC)

        await update_room_status(
            session,
            room=room,
            new_status=RoomStatus.OCCUPIED,
        )

        await session.commit()
        await session.refresh(reservation)

        return reservation

    except Exception:
        await session.rollback()
        raise


async def check_out_reservation(
    session: AsyncSession,
    *,
    reservation_id: int,
    created_by: int,
) -> Reservation:
    reservation = await get_reservation_by_id(
        session,
        reservation_id,
    )

    if reservation is None:
        raise ReservationNotFoundError

    if reservation.status != ReservationStatus.CHECKED_IN:
        raise ReservationCheckOutNotAllowedError

    if reservation.room_id is None:
        raise ReservationRoomNotAssignedError

    room = await get_room_by_id(
        session,
        reservation.room_id,
    )

    if room is None or not room.is_active:
        raise ReservationRoomNotFoundError

    try:
        reservation.status = ReservationStatus.CHECKED_OUT
        reservation.actual_check_out_at = datetime.now(UTC)

        await update_room_status(
            session,
            room=room,
            new_status=RoomStatus.NEEDS_CLEANING,
        )

        await create_operational_task(
            session,
            title=f"Clean Room {room.room_number}",
            description=(
                "Clean and prepare the room after guest checkout."
            ),
            task_type=TaskType.HOUSEKEEPING,
            priority=TaskPriority.HIGH,
            room_id=room.id,
            reservation_id=reservation.id,
            assigned_to=None,
            created_by=created_by,
        )

        await session.commit()
        await session.refresh(reservation)

        return reservation

    except Exception:
        await session.rollback()
        raise


async def cancel_reservation(
    session: AsyncSession,
    *,
    reservation_id: int,
) -> Reservation:
    reservation = await get_reservation_by_id(
        session,
        reservation_id,
    )

    if reservation is None:
        raise ReservationNotFoundError

    if reservation.status not in {
        ReservationStatus.PENDING,
        ReservationStatus.CONFIRMED,
    }:
        raise ReservationCancellationNotAllowedError

    try:
        reservation.status = ReservationStatus.CANCELLED

        await session.commit()
        await session.refresh(reservation)

        return reservation

    except Exception:
        await session.rollback()
        raise