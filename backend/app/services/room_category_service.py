from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.room_category import RoomCategory
from app.repositories.room_category_repository import (
    create_room_category,
    get_room_category_by_name,
    list_room_categories,
)
from app.schemas.room_category import RoomCategoryCreate


class RoomCategoryAlreadyExistsError(Exception):
    pass


async def add_room_category(
    session: AsyncSession,
    category_data: RoomCategoryCreate,
) -> RoomCategory:
    existing_category = await get_room_category_by_name(
        session,
        category_data.name,
    )

    if existing_category is not None:
        raise RoomCategoryAlreadyExistsError

    try:
        category = await create_room_category(
            session,
            name=category_data.name,
            description=category_data.description,
            base_price=category_data.base_price,
            max_occupancy=category_data.max_occupancy,
        )

        await session.commit()
        await session.refresh(category)

        return category

    except IntegrityError as error:
        await session.rollback()
        raise RoomCategoryAlreadyExistsError from error

    except Exception:
        await session.rollback()
        raise


async def get_room_categories(
    session: AsyncSession,
    *,
    offset: int,
    limit: int,
) -> list[RoomCategory]:
    return await list_room_categories(
        session,
        offset=offset,
        limit=limit,
    )