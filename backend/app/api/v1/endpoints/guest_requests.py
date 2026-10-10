from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_roles
from app.db.session import get_db_session
from app.models.guest_request import GuestRequestStatus
from app.models.user import User, UserRole
from app.schemas.guest_request import (
    GuestRequestAssign,
    GuestRequestCreate,
    GuestRequestResolve,
    GuestRequestResponse,
)
from app.services.guest_request_service import (
    GuestRequestAccessDeniedError,
    GuestRequestNotFoundError,
    GuestRequestReservationNotFoundError,
    GuestRequestRoomMismatchError,
    GuestRequestRoomNotFoundError,
    GuestRequestTransitionError,
    InvalidGuestRequestAssigneeError,
    add_guest_request,
    assign_guest_request,
    get_guest_requests,
    resolve_guest_request,
    start_guest_request,
)


router = APIRouter(
    prefix="/guest-requests",
    tags=["Guest Requests"],
)


def guest_request_error_to_http(
    error: Exception,
) -> HTTPException:
    if isinstance(error, GuestRequestNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guest request not found.",
        )

    if isinstance(
        error,
        GuestRequestReservationNotFoundError,
    ):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found.",
        )

    if isinstance(error, GuestRequestRoomNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found.",
        )

    if isinstance(error, GuestRequestAccessDeniedError):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this guest request.",
        )

    if isinstance(error, GuestRequestRoomMismatchError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "The selected room does not match the "
                "reservation room."
            ),
        )

    if isinstance(error, InvalidGuestRequestAssigneeError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "The assignee must be an active front-desk "
                "or operations user."
            ),
        )

    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="The requested status transition is not allowed.",
    )


@router.post(
    "",
    response_model=GuestRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_request(
    request_data: GuestRequestCreate,
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
    current_user: Annotated[
        User,
        Depends(require_roles(UserRole.GUEST)),
    ],
) -> GuestRequestResponse:
    try:
        guest_request = await add_guest_request(
            session,
            request_data=request_data,
            current_user=current_user,
        )

        return GuestRequestResponse.model_validate(
            guest_request
        )

    except Exception as error:
        if isinstance(
            error,
            (
                GuestRequestReservationNotFoundError,
                GuestRequestRoomNotFoundError,
                GuestRequestAccessDeniedError,
                GuestRequestRoomMismatchError,
            ),
        ):
            raise guest_request_error_to_http(error) from error

        raise


@router.get(
    "",
    response_model=list[GuestRequestResponse],
)
async def list_requests(
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
                UserRole.OPERATIONS,
                UserRole.GUEST,
            )
        ),
    ],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    guest_id: Annotated[int | None, Query(gt=0)] = None,
    request_status: GuestRequestStatus | None = None,
    assigned_to: Annotated[int | None, Query(gt=0)] = None,
) -> list[GuestRequestResponse]:
    guest_filter = guest_id
    assignee_filter = assigned_to

    if current_user.role == UserRole.GUEST:
        guest_filter = current_user.id
        assignee_filter = None

    elif current_user.role == UserRole.OPERATIONS:
        guest_filter = None
        assignee_filter = current_user.id

    requests = await get_guest_requests(
        session,
        offset=offset,
        limit=limit,
        guest_id=guest_filter,
        request_status=request_status,
        assigned_to=assignee_filter,
    )

    return [
        GuestRequestResponse.model_validate(request)
        for request in requests
    ]


@router.post(
    "/{request_id}/assign",
    response_model=GuestRequestResponse,
)
async def assign_request(
    request_id: int,
    assignment_data: GuestRequestAssign,
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
) -> GuestRequestResponse:
    try:
        guest_request = await assign_guest_request(
            session,
            request_id=request_id,
            assigned_to=assignment_data.assigned_to,
        )

        return GuestRequestResponse.model_validate(
            guest_request
        )

    except Exception as error:
        raise guest_request_error_to_http(error) from error


@router.post(
    "/{request_id}/start",
    response_model=GuestRequestResponse,
)
async def start_request(
    request_id: int,
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
                UserRole.OPERATIONS,
            )
        ),
    ],
) -> GuestRequestResponse:
    try:
        guest_request = await start_guest_request(
            session,
            request_id=request_id,
            current_user=current_user,
        )

        return GuestRequestResponse.model_validate(
            guest_request
        )

    except Exception as error:
        raise guest_request_error_to_http(error) from error


@router.post(
    "/{request_id}/resolve",
    response_model=GuestRequestResponse,
)
async def resolve_request(
    request_id: int,
    resolution_data: GuestRequestResolve,
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
                UserRole.OPERATIONS,
            )
        ),
    ],
) -> GuestRequestResponse:
    try:
        guest_request = await resolve_guest_request(
            session,
            request_id=request_id,
            resolution_notes=(
                resolution_data.resolution_notes
            ),
            current_user=current_user,
        )

        return GuestRequestResponse.model_validate(
            guest_request
        )

    except Exception as error:
        raise guest_request_error_to_http(error) from error