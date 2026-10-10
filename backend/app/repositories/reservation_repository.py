from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reservation import (
    Reservation,
    ReservationStatus,
)


ACTIVE_RESERVATION_STATUSES = {
    ReservationStatus.PENDING,
    ReservationStatus.CONFIRMED,
    ReservationStatus.CHECKED_IN,
}


async def has_conflicting_reservation(
    session: AsyncSession,
    *,
    room_id: int,
    check_in_date: date,
    check_out_date: date,
) -> bool:
    statement = select(Reservation.id).where(
        Reservation.room_id == room_id,
        Reservation.status.in_(ACTIVE_RESERVATION_STATUSES),
        Reservation.check_in_date < check_out_date,
        Reservation.check_out_date > check_in_date,
    )

    result = await session.execute(statement)

    return result.scalar_one_or_none() is not None


async def create_reservation(
    session: AsyncSession,
    *,
    guest_id: int,
    room_id: int | None,
    created_by: int,
    check_in_date: date,
    check_out_date: date,
    number_of_guests: int,
) -> Reservation:
    reservation = Reservation(
        guest_id=guest_id,
        room_id=room_id,
        created_by=created_by,
        check_in_date=check_in_date,
        check_out_date=check_out_date,
        number_of_guests=number_of_guests,
        status=ReservationStatus.CONFIRMED,
    )

    session.add(reservation)
    await session.flush()
    await session.refresh(reservation)

    return reservation


async def list_reservations(
    session: AsyncSession,
    *,
    offset: int,
    limit: int,
    guest_id: int | None = None,
) -> list[Reservation]:
    statement = select(Reservation)

    if guest_id is not None:
        statement = statement.where(
            Reservation.guest_id == guest_id
        )

    statement = (
        statement
        .order_by(Reservation.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    result = await session.execute(statement)

    return list(result.scalars().all())

async def get_reservation_by_id(
    session: AsyncSession,
    reservation_id: int,
) -> Reservation | None:
    statement = select(Reservation).where(
        Reservation.id == reservation_id
    )
    result = await session.execute(statement)

    return result.scalar_one_or_none()
async def has_conflicting_reservation(
    session: AsyncSession,
    *,
    room_id: int,
    check_in_date: date,
    check_out_date: date,
    exclude_reservation_id: int | None = None,
) -> bool:
    statement = select(Reservation.id).where(
        Reservation.room_id == room_id,
        Reservation.status.in_(ACTIVE_RESERVATION_STATUSES),
        Reservation.check_in_date < check_out_date,
        Reservation.check_out_date > check_in_date,
    )

    if exclude_reservation_id is not None:
        statement = statement.where(
            Reservation.id != exclude_reservation_id
        )

    result = await session.execute(statement)

    return result.first() is not None
