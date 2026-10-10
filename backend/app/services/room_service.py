from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.room import Room, RoomStatus
from app.repositories.room_category_repository import (
    get_room_category_by_id,
)
from app.repositories.room_repository import (
    create_room,
    get_room_by_id,
    get_room_by_number,
    list_rooms,
    update_room_status,
)
from app.schemas.room import RoomCreate


class RoomAlreadyExistsError(Exception):
    pass


class RoomCategoryNotFoundError(Exception):
    pass


class RoomNotFoundError(Exception):
    pass


async def add_room(
    session: AsyncSession,
    room_data: RoomCreate,
) -> Room:
    category = await get_room_category_by_id(
        session,
        room_data.category_id,
    )

    if category is None or not category.is_active:
        raise RoomCategoryNotFoundError

    existing_room = await get_room_by_number(
        session,
        room_data.room_number,
    )

    if existing_room is not None:
        raise RoomAlreadyExistsError

    try:
        room = await create_room(
            session,
            room_number=room_data.room_number,
            floor=room_data.floor,
            category_id=room_data.category_id,
        )

        await session.commit()
        await session.refresh(room)

        return room

    except IntegrityError as error:
        await session.rollback()
        raise RoomAlreadyExistsError from error

    except Exception:
        await session.rollback()
        raise


async def get_rooms(
    session: AsyncSession,
    *,
    offset: int,
    limit: int,
    status: RoomStatus | None,
    category_id: int | None,
    floor: int | None,
) -> list[Room]:
    return await list_rooms(
        session,
        offset=offset,
        limit=limit,
        status=status,
        category_id=category_id,
        floor=floor,
    )


async def change_room_status(
    session: AsyncSession,
    *,
    room_id: int,
    new_status: RoomStatus,
) -> Room:
    room = await get_room_by_id(session, room_id)

    if room is None:
        raise RoomNotFoundError

    try:
        updated_room = await update_room_status(
            session,
            room=room,
            new_status=new_status,
        )

        await session.commit()
        await session.refresh(updated_room)

        return updated_room

    except Exception:
        await session.rollback()
        raise