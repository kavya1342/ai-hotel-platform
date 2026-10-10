from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.guest_request import (
    GuestRequest,
    GuestRequestCategory,
    GuestRequestPriority,
    GuestRequestStatus,
)
from app.models.user import User, UserRole
from app.repositories.guest_request_repository import (
    create_guest_request,
    get_guest_request_by_id,
    list_guest_requests,
)
from app.repositories.reservation_repository import (
    get_reservation_by_id,
)
from app.repositories.room_repository import get_room_by_id
from app.repositories.user_repository import get_user_by_id
from app.schemas.guest_request import GuestRequestCreate
from app.services.gemini_service import (
    GeminiClassificationError,
    classify_guest_request,
)

class GuestRequestNotFoundError(Exception):
    pass


class GuestRequestReservationNotFoundError(Exception):
    pass


class GuestRequestRoomNotFoundError(Exception):
    pass


class GuestRequestAccessDeniedError(Exception):
    pass


class GuestRequestRoomMismatchError(Exception):
    pass


class InvalidGuestRequestAssigneeError(Exception):
    pass


class GuestRequestTransitionError(Exception):
    pass


async def add_guest_request(
    session: AsyncSession,
    *,
    request_data: GuestRequestCreate,
    current_user: User,
) -> GuestRequest:
    reservation = None
    room_id = request_data.room_id

    if request_data.reservation_id is not None:
        reservation = await get_reservation_by_id(
            session,
            request_data.reservation_id,
        )

        if reservation is None:
            raise GuestRequestReservationNotFoundError

        if reservation.guest_id != current_user.id:
            raise GuestRequestAccessDeniedError

        if room_id is None:
            room_id = reservation.room_id

        if (
            room_id is not None
            and reservation.room_id is not None
            and room_id != reservation.room_id
        ):
            raise GuestRequestRoomMismatchError

    if room_id is not None:
        room = await get_room_by_id(session, room_id)

        if room is None or not room.is_active:
            raise GuestRequestRoomNotFoundError

    try:
        classification = await classify_guest_request(
            request_data.message
        )

        category = classification.category
        priority = classification.priority
        ai_summary = classification.summary

    except GeminiClassificationError:
        category = GuestRequestCategory.OTHER
        priority = GuestRequestPriority.MEDIUM
        ai_summary = None

    try:
        guest_request = await create_guest_request(
            session,
            guest_id=current_user.id,
            reservation_id=request_data.reservation_id,
            room_id=room_id,
            message=request_data.message,
            category=category,
            priority=priority,
            ai_summary=ai_summary,
        )

        await session.commit()
        await session.refresh(guest_request)

        return guest_request

    except Exception:
        await session.rollback()
        raise


async def get_guest_requests(
    session: AsyncSession,
    *,
    offset: int,
    limit: int,
    guest_id: int | None,
    request_status: GuestRequestStatus | None,
    assigned_to: int | None,
) -> list[GuestRequest]:
    return await list_guest_requests(
        session,
        offset=offset,
        limit=limit,
        guest_id=guest_id,
        request_status=request_status,
        assigned_to=assigned_to,
    )


async def validate_guest_request_assignee(
    session: AsyncSession,
    user_id: int,
) -> User:
    user = await get_user_by_id(session, user_id)

    if (
        user is None
        or not user.is_active
        or user.role
        not in {
            UserRole.FRONT_DESK,
            UserRole.OPERATIONS,
        }
    ):
        raise InvalidGuestRequestAssigneeError

    return user


async def assign_guest_request(
    session: AsyncSession,
    *,
    request_id: int,
    assigned_to: int,
) -> GuestRequest:
    guest_request = await get_guest_request_by_id(
        session,
        request_id,
    )

    if guest_request is None:
        raise GuestRequestNotFoundError

    if guest_request.status not in {
        GuestRequestStatus.SUBMITTED,
        GuestRequestStatus.ACKNOWLEDGED,
    }:
        raise GuestRequestTransitionError

    await validate_guest_request_assignee(
        session,
        assigned_to,
    )

    try:
        guest_request.assigned_to = assigned_to
        guest_request.status = GuestRequestStatus.ACKNOWLEDGED

        await session.commit()
        await session.refresh(guest_request)

        return guest_request

    except Exception:
        await session.rollback()
        raise


def verify_guest_request_access(
    guest_request: GuestRequest,
    current_user: User,
) -> None:
    if (
        current_user.role
        in {
            UserRole.FRONT_DESK,
            UserRole.OPERATIONS,
        }
        and guest_request.assigned_to != current_user.id
    ):
        raise GuestRequestAccessDeniedError


async def start_guest_request(
    session: AsyncSession,
    *,
    request_id: int,
    current_user: User,
) -> GuestRequest:
    guest_request = await get_guest_request_by_id(
        session,
        request_id,
    )

    if guest_request is None:
        raise GuestRequestNotFoundError

    verify_guest_request_access(
        guest_request,
        current_user,
    )

    if guest_request.status != GuestRequestStatus.ACKNOWLEDGED:
        raise GuestRequestTransitionError

    try:
        guest_request.status = GuestRequestStatus.IN_PROGRESS

        await session.commit()
        await session.refresh(guest_request)

        return guest_request

    except Exception:
        await session.rollback()
        raise


async def resolve_guest_request(
    session: AsyncSession,
    *,
    request_id: int,
    resolution_notes: str,
    current_user: User,
) -> GuestRequest:
    guest_request = await get_guest_request_by_id(
        session,
        request_id,
    )

    if guest_request is None:
        raise GuestRequestNotFoundError

    verify_guest_request_access(
        guest_request,
        current_user,
    )

    if guest_request.status != GuestRequestStatus.IN_PROGRESS:
        raise GuestRequestTransitionError

    try:
        guest_request.status = GuestRequestStatus.RESOLVED
        guest_request.resolution_notes = resolution_notes
        guest_request.resolved_at = datetime.now(UTC)

        await session.commit()
        await session.refresh(guest_request)

        return guest_request

    except Exception:
        await session.rollback()
        raise