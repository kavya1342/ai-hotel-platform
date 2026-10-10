from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.operational_task import (
    OperationalTask,
    TaskStatus,
    TaskType,
)
from app.models.room import RoomStatus
from app.models.user import User, UserRole
from app.repositories.operational_task_repository import (
    create_operational_task,
    get_operational_task_by_id,
    list_operational_tasks,
)
from app.repositories.reservation_repository import (
    get_reservation_by_id,
)
from app.repositories.room_repository import (
    get_room_by_id,
    update_room_status,
)
from app.repositories.user_repository import get_user_by_id
from app.schemas.operational_task import OperationalTaskCreate


class OperationalTaskNotFoundError(Exception):
    pass


class OperationalTaskRoomNotFoundError(Exception):
    pass


class OperationalTaskReservationNotFoundError(Exception):
    pass


class InvalidOperationsAssigneeError(Exception):
    pass


class OperationalTaskTransitionError(Exception):
    pass


class OperationalTaskAccessDeniedError(Exception):
    pass


async def validate_operations_assignee(
    session: AsyncSession,
    user_id: int,
) -> User:
    user = await get_user_by_id(session, user_id)

    if (
        user is None
        or not user.is_active
        or user.role != UserRole.OPERATIONS
    ):
        raise InvalidOperationsAssigneeError

    return user


async def add_operational_task(
    session: AsyncSession,
    *,
    task_data: OperationalTaskCreate,
    created_by: int,
) -> OperationalTask:
    if task_data.room_id is not None:
        room = await get_room_by_id(session, task_data.room_id)

        if room is None or not room.is_active:
            raise OperationalTaskRoomNotFoundError

    if task_data.reservation_id is not None:
        reservation = await get_reservation_by_id(
            session,
            task_data.reservation_id,
        )

        if reservation is None:
            raise OperationalTaskReservationNotFoundError

    if task_data.assigned_to is not None:
        await validate_operations_assignee(
            session,
            task_data.assigned_to,
        )

    try:
        task = await create_operational_task(
            session,
            title=task_data.title,
            description=task_data.description,
            task_type=task_data.task_type,
            priority=task_data.priority,
            room_id=task_data.room_id,
            reservation_id=task_data.reservation_id,
            assigned_to=task_data.assigned_to,
            created_by=created_by,
        )

        await session.commit()
        await session.refresh(task)

        return task

    except Exception:
        await session.rollback()
        raise


async def get_operational_tasks(
    session: AsyncSession,
    *,
    offset: int,
    limit: int,
    task_status: TaskStatus | None,
    assigned_to: int | None,
    room_id: int | None,
) -> list[OperationalTask]:
    return await list_operational_tasks(
        session,
        offset=offset,
        limit=limit,
        task_status=task_status,
        assigned_to=assigned_to,
        room_id=room_id,
    )


async def assign_operational_task(
    session: AsyncSession,
    *,
    task_id: int,
    assigned_to: int,
) -> OperationalTask:
    task = await get_operational_task_by_id(session, task_id)

    if task is None:
        raise OperationalTaskNotFoundError

    if task.status not in {
        TaskStatus.PENDING,
        TaskStatus.ASSIGNED,
    }:
        raise OperationalTaskTransitionError

    await validate_operations_assignee(
        session,
        assigned_to,
    )

    try:
        task.assigned_to = assigned_to
        task.status = TaskStatus.ASSIGNED

        await session.commit()
        await session.refresh(task)

        return task

    except Exception:
        await session.rollback()
        raise


def verify_task_access(
    task: OperationalTask,
    current_user: User,
) -> None:
    if (
        current_user.role == UserRole.OPERATIONS
        and task.assigned_to != current_user.id
    ):
        raise OperationalTaskAccessDeniedError


async def start_operational_task(
    session: AsyncSession,
    *,
    task_id: int,
    current_user: User,
) -> OperationalTask:
    task = await get_operational_task_by_id(session, task_id)

    if task is None:
        raise OperationalTaskNotFoundError

    verify_task_access(task, current_user)

    if task.status != TaskStatus.ASSIGNED:
        raise OperationalTaskTransitionError

    try:
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now(UTC)

        if (
            task.task_type == TaskType.HOUSEKEEPING
            and task.room_id is not None
        ):
            room = await get_room_by_id(session, task.room_id)

            if room is not None:
                await update_room_status(
                    session,
                    room=room,
                    new_status=RoomStatus.CLEANING,
                )

        await session.commit()
        await session.refresh(task)

        return task

    except Exception:
        await session.rollback()
        raise


async def complete_operational_task(
    session: AsyncSession,
    *,
    task_id: int,
    completion_notes: str | None,
    current_user: User,
) -> OperationalTask:
    task = await get_operational_task_by_id(session, task_id)

    if task is None:
        raise OperationalTaskNotFoundError

    verify_task_access(task, current_user)

    if task.status != TaskStatus.IN_PROGRESS:
        raise OperationalTaskTransitionError

    try:
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now(UTC)
        task.completion_notes = completion_notes

        if (
            task.task_type == TaskType.HOUSEKEEPING
            and task.room_id is not None
        ):
            room = await get_room_by_id(session, task.room_id)

            if room is not None:
                await update_room_status(
                    session,
                    room=room,
                    new_status=RoomStatus.AVAILABLE,
                )

        await session.commit()
        await session.refresh(task)

        return task

    except Exception:
        await session.rollback()
        raise