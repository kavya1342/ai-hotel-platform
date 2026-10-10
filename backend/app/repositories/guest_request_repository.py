from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.guest_request import (
    GuestRequest,
    GuestRequestCategory,
    GuestRequestPriority,
    GuestRequestStatus,
)


async def get_guest_request_by_id(
    session: AsyncSession,
    request_id: int,
) -> GuestRequest | None:
    statement = select(GuestRequest).where(
        GuestRequest.id == request_id
    )

    result = await session.execute(statement)

    return result.scalar_one_or_none()


async def create_guest_request(
    session: AsyncSession,
    *,
    guest_id: int,
    reservation_id: int | None,
    room_id: int | None,
    message: str,
    category: GuestRequestCategory,
    priority: GuestRequestPriority,
    ai_summary: str | None,
) -> GuestRequest:
    guest_request = GuestRequest(
        guest_id=guest_id,
        reservation_id=reservation_id,
        room_id=room_id,
        message=message,
        category=category,
        priority=priority,
        ai_summary=ai_summary,
        status=GuestRequestStatus.SUBMITTED,
    )

    session.add(guest_request)
    await session.flush()
    await session.refresh(guest_request)

    return guest_request


async def list_guest_requests(
    session: AsyncSession,
    *,
    offset: int,
    limit: int,
    guest_id: int | None,
    request_status: GuestRequestStatus | None,
    assigned_to: int | None,
) -> list[GuestRequest]:
    statement = select(GuestRequest)

    if guest_id is not None:
        statement = statement.where(
            GuestRequest.guest_id == guest_id
        )

    if request_status is not None:
        statement = statement.where(
            GuestRequest.status == request_status
        )

    if assigned_to is not None:
        statement = statement.where(
            GuestRequest.assigned_to == assigned_to
        )

    statement = (
        statement
        .order_by(GuestRequest.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    result = await session.execute(statement)

    return list(result.scalars().all())