from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.room_category import RoomCategory


async def get_room_category_by_name(
    session: AsyncSession,
    name: str,
) -> RoomCategory | None:
    statement = select(RoomCategory).where(
        RoomCategory.name == name
    )
    result = await session.execute(statement)

    return result.scalar_one_or_none()

async def get_room_category_by_id(
    session: AsyncSession,
    category_id: int,
) -> RoomCategory | None:
    statement = select(RoomCategory).where(
        RoomCategory.id == category_id
    )
    result = await session.execute(statement)

    return result.scalar_one_or_none()

async def create_room_category(
    session: AsyncSession,
    *,
    name: str,
    description: str | None,
    base_price: Decimal,
    max_occupancy: int,
) -> RoomCategory:
    category = RoomCategory(
        name=name,
        description=description,
        base_price=base_price,
        max_occupancy=max_occupancy,
    )

    session.add(category)
    await session.flush()
    await session.refresh(category)

    return category


async def list_room_categories(
    session: AsyncSession,
    *,
    offset: int,
    limit: int,
) -> list[RoomCategory]:
    statement = (
        select(RoomCategory)
        .order_by(RoomCategory.name)
        .offset(offset)
        .limit(limit)
    )

    result = await session.execute(statement)

    return list(result.scalars().all())