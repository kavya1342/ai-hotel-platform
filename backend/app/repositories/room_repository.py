from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.room_category import RoomCategory
from app.models.room import Room, RoomStatus
from datetime import date

from sqlalchemy import exists, select
from app.models.reservation import Reservation, ReservationStatus

async def get_room_by_id(
    session: AsyncSession,
    room_id: int,
) -> Room | None:
    statement = select(Room).where(Room.id == room_id)
    result = await session.execute(statement)

    return result.scalar_one_or_none()


async def get_room_by_number(
    session: AsyncSession,
    room_number: str,
) -> Room | None:
    statement = select(Room).where(
        Room.room_number == room_number
    )
    result = await session.execute(statement)

    return result.scalar_one_or_none()


async def create_room(
    session: AsyncSession,
    *,
    room_number: str,
    floor: int,
    category_id: int,
) -> Room:
    room = Room(
        room_number=room_number,
        floor=floor,
        category_id=category_id,
    )

    session.add(room)
    await session.flush()
    await session.refresh(room)

    return room


async def list_rooms(
    session: AsyncSession,
    *,
    offset: int,
    limit: int,
    status: RoomStatus | None,
    category_id: int | None,
    floor: int | None,
) -> list[Room]:
    statement = select(Room)

    if status is not None:
        statement = statement.where(Room.status == status)

    if category_id is not None:
        statement = statement.where(
            Room.category_id == category_id
        )

    if floor is not None:
        statement = statement.where(Room.floor == floor)

    statement = (
        statement
        .order_by(Room.room_number)
        .offset(offset)
        .limit(limit)
    )

    result = await session.execute(statement)

    return list(result.scalars().all())


async def update_room_status(
    session: AsyncSession,
    *,
    room: Room,
    new_status: RoomStatus,
) -> Room:
    room.status = new_status

    await session.flush()
    await session.refresh(room)

    return room
async def list_available_rooms(
    session: AsyncSession,
    *,
    check_in_date: date,
    check_out_date: date,
    number_of_guests: int,
    category_id: int | None,
) -> list[Room]:
    conflicting_reservation = exists().where(
        Reservation.room_id == Room.id,
        Reservation.status.in_(
            {
                ReservationStatus.PENDING,
                ReservationStatus.CONFIRMED,
                ReservationStatus.CHECKED_IN,
            }
        ),
        Reservation.check_in_date < check_out_date,
        Reservation.check_out_date > check_in_date,
    )

    statement = (
        select(Room)
        .join(
            RoomCategory,
            Room.category_id == RoomCategory.id,
        )
        .where(
            Room.is_active.is_(True),
            RoomCategory.is_active.is_(True),
            RoomCategory.max_occupancy >= number_of_guests,
            Room.status.notin_(
                {
                    RoomStatus.MAINTENANCE,
                    RoomStatus.UNAVAILABLE,
                }
            ),
            ~conflicting_reservation,
        )
        .order_by(Room.room_number)
    )

    if category_id is not None:
        statement = statement.where(
            Room.category_id == category_id
        )

    result = await session.execute(statement)

    return list(result.scalars().all())