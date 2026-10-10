from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.operational_task import (
    OperationalTask,
    TaskPriority,
    TaskStatus,
    TaskType,
)


async def get_operational_task_by_id(
    session: AsyncSession,
    task_id: int,
) -> OperationalTask | None:
    statement = select(OperationalTask).where(
        OperationalTask.id == task_id
    )
    result = await session.execute(statement)

    return result.scalar_one_or_none()


async def create_operational_task(
    session: AsyncSession,
    *,
    title: str,
    description: str | None,
    task_type: TaskType,
    priority: TaskPriority,
    room_id: int | None,
    reservation_id: int | None,
    assigned_to: int | None,
    created_by: int,
) -> OperationalTask:
    task = OperationalTask(
        title=title,
        description=description,
        task_type=task_type,
        priority=priority,
        room_id=room_id,
        reservation_id=reservation_id,
        assigned_to=assigned_to,
        created_by=created_by,
        status=(
            TaskStatus.ASSIGNED
            if assigned_to is not None
            else TaskStatus.PENDING
        ),
    )

    session.add(task)
    await session.flush()
    await session.refresh(task)

    return task


async def list_operational_tasks(
    session: AsyncSession,
    *,
    offset: int,
    limit: int,
    task_status: TaskStatus | None,
    assigned_to: int | None,
    room_id: int | None,
) -> list[OperationalTask]:
    statement = select(OperationalTask)

    if task_status is not None:
        statement = statement.where(
            OperationalTask.status == task_status
        )

    if assigned_to is not None:
        statement = statement.where(
            OperationalTask.assigned_to == assigned_to
        )

    if room_id is not None:
        statement = statement.where(
            OperationalTask.room_id == room_id
        )

    statement = (
        statement
        .order_by(OperationalTask.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    result = await session.execute(statement)

    return list(result.scalars().all())