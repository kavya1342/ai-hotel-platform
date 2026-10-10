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
from app.models.operational_task import TaskStatus
from app.models.user import User, UserRole
from app.schemas.operational_task import (
    OperationalTaskAssign,
    OperationalTaskComplete,
    OperationalTaskCreate,
    OperationalTaskResponse,
)
from app.services.operational_task_service import (
    InvalidOperationsAssigneeError,
    OperationalTaskAccessDeniedError,
    OperationalTaskNotFoundError,
    OperationalTaskReservationNotFoundError,
    OperationalTaskRoomNotFoundError,
    OperationalTaskTransitionError,
    add_operational_task,
    assign_operational_task,
    complete_operational_task,
    get_operational_tasks,
    start_operational_task,
)


router = APIRouter(
    prefix="/tasks",
    tags=["Operational Tasks"],
)


def task_error_to_http(error: Exception) -> HTTPException:
    if isinstance(error, OperationalTaskNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Operational task not found.",
        )

    if isinstance(error, OperationalTaskRoomNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found.",
        )

    if isinstance(
        error,
        OperationalTaskReservationNotFoundError,
    ):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found.",
        )

    if isinstance(error, InvalidOperationsAssigneeError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The assignee must be an active operations user.",
        )

    if isinstance(error, OperationalTaskAccessDeniedError):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this task.",
        )

    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="The requested task status transition is not allowed.",
    )


@router.post(
    "",
    response_model=OperationalTaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    task_data: OperationalTaskCreate,
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
) -> OperationalTaskResponse:
    try:
        task = await add_operational_task(
            session,
            task_data=task_data,
            created_by=current_user.id,
        )

        return OperationalTaskResponse.model_validate(task)

    except Exception as error:
        if isinstance(
            error,
            (
                OperationalTaskRoomNotFoundError,
                OperationalTaskReservationNotFoundError,
                InvalidOperationsAssigneeError,
            ),
        ):
            raise task_error_to_http(error) from error

        raise


@router.get(
    "",
    response_model=list[OperationalTaskResponse],
)
async def list_tasks(
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
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    task_status: TaskStatus | None = None,
    assigned_to: Annotated[int | None, Query(gt=0)] = None,
    room_id: Annotated[int | None, Query(gt=0)] = None,
) -> list[OperationalTaskResponse]:
    assignee_filter = (
        current_user.id
        if current_user.role == UserRole.OPERATIONS
        else assigned_to
    )

    tasks = await get_operational_tasks(
        session,
        offset=offset,
        limit=limit,
        task_status=task_status,
        assigned_to=assignee_filter,
        room_id=room_id,
    )

    return [
        OperationalTaskResponse.model_validate(task)
        for task in tasks
    ]


@router.post(
    "/{task_id}/assign",
    response_model=OperationalTaskResponse,
)
async def assign_task(
    task_id: int,
    assignment_data: OperationalTaskAssign,
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
) -> OperationalTaskResponse:
    try:
        task = await assign_operational_task(
            session,
            task_id=task_id,
            assigned_to=assignment_data.assigned_to,
        )

        return OperationalTaskResponse.model_validate(task)

    except Exception as error:
        raise task_error_to_http(error) from error


@router.post(
    "/{task_id}/start",
    response_model=OperationalTaskResponse,
)
async def start_task(
    task_id: int,
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
) -> OperationalTaskResponse:
    try:
        task = await start_operational_task(
            session,
            task_id=task_id,
            current_user=current_user,
        )

        return OperationalTaskResponse.model_validate(task)

    except Exception as error:
        raise task_error_to_http(error) from error


@router.post(
    "/{task_id}/complete",
    response_model=OperationalTaskResponse,
)
async def complete_task(
    task_id: int,
    completion_data: OperationalTaskComplete,
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
) -> OperationalTaskResponse:
    try:
        task = await complete_operational_task(
            session,
            task_id=task_id,
            completion_notes=completion_data.completion_notes,
            current_user=current_user,
        )

        return OperationalTaskResponse.model_validate(task)

    except Exception as error:
        raise task_error_to_http(error) from error